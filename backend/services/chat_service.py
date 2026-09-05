"""聊天编排服务，负责会话记忆、Agent 执行与数据持久化。"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import HTTPException
from langgraph.graph.state import CompiledStateGraph

from ..core.agent_factory import create_agent_instance, get_model_name
from ..core.agent_state import update_agent_checkpoint_state
from ..core.agent_output import append_schema_instruction, parse_and_validate_structured_output, render_prompt_template
from ..core.streaming import stream_agent_response, sse_event
from ..core.trace_handler import TraceContext
from ..runtime.models import RuntimeContext
from ..models.agent import Agent
from ..models.chat import (
    AgentStateContext,
    ChatHistoryMessage,
    ChatSession,
    ChatUser,
    McpConfig,
    ModelConfig,
    PreparedChatRun,
    RuntimeFile,
    SkillConfig,
)
from ..database import execute, fetch_all, fetch_one
from .agent_service import get_agent
from .mcp_config_service import get_agent_mcps
from .skill_service import get_agent_skills
from .runtime_service import get_runtime_files

log = logging.getLogger(__name__)


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def _load_model_config(agent: Agent, user_id: int) -> Optional[ModelConfig]:
    """按 Agent 配置加载模型实体；未绑定自定义模型时返回 ``None``。"""
    if not agent.model_config_id:
        return None
    from .model_service import get_model
    model_row: Optional[Dict[str, Any]] = await get_model(agent.model_config_id, user_id)
    return ModelConfig.from_mapping(model_row) if model_row else None


async def _load_chat_session(session_id: int, user_id: int) -> Optional[ChatSession]:
    """查询会话并在数据库边界立即转换为实体。"""
    session_row: Optional[Dict[str, Any]] = await fetch_one(
        "SELECT id, agent_id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user_id),
    )
    return ChatSession.from_mapping(session_row) if session_row else None


async def prepare_chat_run(
    user: Dict[str, Any],
    message: str,
    session_id: int,
    images: Optional[List[str]] = None,
    file_ids: Optional[List[str]] = None,
) -> PreparedChatRun:
    """加载并组装执行一次聊天请求所需的强类型运行时数据。"""
    current_user:ChatUser = ChatUser.from_mapping(user)
    session: Optional[ChatSession] = await _load_chat_session(session_id, current_user.user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在，请重新创建会话")

    agent: Optional[Agent] = await get_agent(session.agent_id, current_user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    try:
        runtime_file_rows: List[Dict[str, Any]] = await get_runtime_files(
            file_ids or [], current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    runtime_files = [RuntimeFile.from_mapping(item) for item in runtime_file_rows]

    # 图片保留 base64；普通文件只保存逻辑 ID，不向模型暴露宿主机路径。
    attachments = list(images or [])
    attachments.extend(item.to_attachment() for item in runtime_files)
    attachments_json = json.dumps(attachments, ensure_ascii=False) if attachments else None
    user_message_id = await execute(
        "INSERT INTO chat_messages (session_id, role, content, attachments, created_at) "
        "VALUES (%s, %s, %s, %s, %s)",
        (session_id, "user", message, attachments_json, _now()),
    )

    message_count_row: Optional[Dict[str, Any]] = await fetch_one(
        "SELECT COUNT(*) as cnt FROM chat_messages WHERE session_id=%s AND role='user'",
        (session_id,),
    )
    if message_count_row and int(message_count_row["cnt"]) == 1:
        title = message[:50].replace("\n", " ").strip() or "新对话"
        await execute("UPDATE chat_sessions SET title=%s WHERE id=%s", (title, session_id))

    # chat_messages 是持久化的会话记忆；每次执行前从 MySQL 恢复历史，
    # 可以保证 FastAPI 进程重启后 Agent 仍然能接上上下文。
    history_rows: List[Dict[str, Any]] = await fetch_all(
        "SELECT role, content, attachments FROM chat_messages "
        "WHERE session_id=%s AND role IN ('user', 'assistant') "
        "ORDER BY created_at ASC, id ASC",
        (session_id,),
    )
    history_messages = [ChatHistoryMessage.from_mapping(item) for item in history_rows]

    skill_rows: List[Dict[str, Any]] = await get_agent_skills(agent.id)
    mcp_rows: List[Dict[str, Any]] = await get_agent_mcps(agent.id)
    skills = [SkillConfig.from_mapping(item) for item in skill_rows]
    mcps = [McpConfig.from_mapping(item) for item in mcp_rows]
    model_config = await _load_model_config(agent, current_user.user_id)
    skills_data = [dict(item.raw) for item in skills]
    mcps_data = [dict(item.raw) for item in mcps]
    model_config_data = model_config.to_factory_dict() if model_config else None
    runtime_variables = {
        "user_input": message,
        "username": current_user.username,
        "user_id": current_user.user_id,
        "session_id": session_id,
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }
    rendered_prompt = render_prompt_template(
        agent.system_prompt, agent.prompt_variables, runtime_variables,
    )
    runtime_agent = agent.with_system_prompt(
        append_schema_instruction(rendered_prompt, agent.output_schema),
    )
    agent_executor: CompiledStateGraph = await create_agent_instance(
        runtime_agent,
        skills_data,
        mcps_data,
        model_config_data,
        runtime_context=RuntimeContext(
            user_id=current_user.user_id,
            workspace_id=f"session-{session_id}",
            session_id=session_id,
        ),
    )

    max_tool_rounds = max(1, min(agent.iteration_count, 100))
    # 每次请求使用新的 LangGraph thread_id，因为完整历史已经由 MySQL 提供。
    # 如果这里复用 session_id，同进程内还会叠加 InMemorySaver 里的状态，
    # 可能导致模型看到重复上下文。
    thread_id = f"session_{session_id}_message_{user_message_id}"

    trace_ctx = TraceContext(
        session_id=session_id,
        user_id=current_user.user_id,
        agent_id=agent.id,
        model_name=get_model_name(runtime_agent, model_config_data),
    )
    await trace_ctx.start(message)

    return PreparedChatRun(
        agent_executor=agent_executor,
        history_messages=history_messages,
        max_tool_rounds=max_tool_rounds,
        thread_id=thread_id,
        trace_ctx=trace_ctx,
        output_schema=agent.output_schema,
        # 文件 ID 和可用 Skill 进入 LangGraph State，文件内容仍由 Runtime 按权限读取。
        state_context=AgentStateContext(
            runtime_file_ids=[item.id for item in runtime_files],
            available_skills=[item.name for item in skills],
            loaded_skills=[],
            current_input=message,
        ),
    )


async def stream_chat(
    user: Dict[str, Any],
    message: str,
    session_id: int,
    images: Optional[List[str]] = None,
    file_ids: Optional[List[str]] = None,
) -> AsyncGenerator[str, None]:
    """运行 Agent 并生成 SSE 数据块，同时持久化助手回复。"""
    run:PreparedChatRun = await prepare_chat_run(user, message, session_id, images, file_ids)
    full_response = []
    reasoning_response = []
    # Token 先按 LLM 轮次暂存，收到分类事件后再进入正式回答或执行说明。
    pending_rounds = {}
    stream_failed = False

    try:
        async for chunk in stream_agent_response(
            agent_executor=run.agent_executor,
            user_message=message,
            thread_id=run.thread_id,
            history_messages=run.history_messages,
            max_tool_rounds=run.max_tool_rounds,
            trace_ctx=run.trace_ctx,
            images=images,
            state_context=run.state_context,
        ):
            suppress_chunk = False
            if chunk.startswith("data:"):
                payload = chunk[5:]
                if payload.endswith("\n\n"):
                    payload = payload[:-2]
                try:
                    event = json.loads(payload)
                    event_type = event.get("type")
                    if event_type == "pending_text_delta":
                        round_id = event.get("round_id", "")
                        pending_rounds.setdefault(round_id, []).append(event.get("content", ""))
                    elif event_type == "llm_round_classified":
                        round_id = event.get("round_id", "")
                        round_text = "".join(pending_rounds.pop(round_id, []))
                        if event.get("classification") == "answer":
                            full_response.append(round_text)
                        else:
                            reasoning_response.append(round_text)
                    elif event_type == "error":
                        stream_failed = True
                    elif event_type == "done":
                        # 结构化校验完成后再发 done，保证客户端不会提前结束。
                        suppress_chunk = True
                except json.JSONDecodeError:
                    pass
            if not suppress_chunk:
                yield chunk
    except asyncio.CancelledError:
        log.info("[Session#%s] client disconnected", session_id)
        await run.trace_ctx.error("client disconnected")
        return
    except Exception as exc:
        log.exception("[Session#%s] chat failed", session_id)
        await run.trace_ctx.error(str(exc))
        yield sse_event("error", str(exc))
        yield sse_event("done")
        return

    assistant_text = "".join(full_response)
    structured_content = None
    if run.output_schema and not stream_failed:
        try:
            structured_content = parse_and_validate_structured_output(
                assistant_text, run.output_schema,
            )
        except ValueError as exc:
            await run.trace_ctx.error(str(exc))
            yield sse_event("error", str(exc))
            yield sse_event("done")
            return
    if structured_content is not None:
        # 追加业务 State 仅用于 Checkpoint 恢复与调试；MySQL 持久化逻辑保持不变。
        await update_agent_checkpoint_state(
            run.agent_executor,
            run.thread_id,
            {"structured_result": structured_content},
        )
    if assistant_text.strip():
        await execute(
            "INSERT INTO chat_messages "
            "(session_id, role, content, reasoning_content, structured_content, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                session_id, "assistant", assistant_text, "".join(reasoning_response) or None,
                json.dumps(structured_content, ensure_ascii=False) if structured_content is not None else None,
                _now(),
            ),
        )
        await run.trace_ctx.finish(assistant_text)
        if structured_content is not None:
            yield sse_event("structured_result", json.dumps(structured_content, ensure_ascii=False))
    else:
        await run.trace_ctx.error("empty response")
    yield sse_event("done")
