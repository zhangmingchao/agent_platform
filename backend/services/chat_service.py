"""聊天编排服务，负责会话记忆、Agent 执行与数据持久化。"""
import asyncio
import json
import logging
from datetime import datetime
from dataclasses import replace
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
    ModelConfig,
    PreparedChatRun,
    RuntimeFile,
    SkillConfig,
)
from ..models.api_access import (
    ApiAuthenticatedUser,
    ExternalChatRequest,
    InvocationSource,
)
from ..models.mcp import McpConfig
from ..models.task_planning import PlanningMode
from ..database import execute, fetch_all, fetch_one
from .agent_service import get_agent
from .mcp_config_service import get_agent_mcps
from .skill_service import get_agent_skills
from .runtime_service import get_runtime_files
from .task_plan_service import fail_active_task_plan_by_trace

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


async def _prepare_agent_run(
    current_user: ChatUser,
    agent: Agent,
    user_message: str,
    history_messages: List[ChatHistoryMessage],
    thread_id: str,
    runtime_context: RuntimeContext,
    *,
    session_id: Optional[int],
    invocation_source: InvocationSource,
    runtime_file_ids: Optional[List[str]] = None,
    template_session_id: str = "",
    current_node_id: str = "chat",
    request_id: Optional[str] = None,
    client_conversation_id: Optional[str] = None,
) -> PreparedChatRun:
    """构建平台聊天和外部 API 共用的 Agent 单次运行实体。

    Args:
        current_user: 已通过平台 JWT 或 API Key 认证的用户实体。
        agent: 当前用户拥有的 Agent 配置实体。
        user_message: 本轮最新一条用户消息，用于提示词变量和 Trace。
        history_messages: 需要发送给模型的完整 user/assistant 历史。
        thread_id: 本次 LangGraph 执行使用的唯一线程标识。
        runtime_context: Runtime 工具使用的用户与工作空间上下文。
        session_id: 平台会话 ID；API 调用固定为 ``None``。
        invocation_source: 本次执行来源，用于 Trace 区分 platform 或 api。
        runtime_file_ids: 本次允许 Runtime 工具访问的文件 ID。
        template_session_id: 渲染系统提示词 ``session_id`` 变量时使用的值。
        current_node_id: 写入 Agent State 的当前业务节点标识。
        request_id: 对外暴露的一次请求唯一编号，仅外部 API 调用使用。
        client_conversation_id: 外部调用方自己的会话关联标识。

    Returns:
        已装配 Agent、历史、Trace 和业务 State 的强类型运行实体。
    """
    skill_rows: List[Dict[str, Any]] = await get_agent_skills(agent.id)
    mcps: List[McpConfig] = await get_agent_mcps(agent.id)
    skills = [SkillConfig.from_mapping(item) for item in skill_rows]
    model_config = await _load_model_config(agent, current_user.user_id)
    skills_data = [dict(item.raw) for item in skills]
    mcps_data = [item.to_factory_dict() for item in mcps]
    model_config_data = model_config.to_factory_dict() if model_config else None
    runtime_variables = {
        "user_input": user_message,
        "username": current_user.username,
        "user_id": current_user.user_id,
        "session_id": template_session_id,
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }
    rendered_prompt = render_prompt_template(
        agent.system_prompt, agent.prompt_variables, runtime_variables,
    )
    log.info("系统提示词模版变量渲染完成: agent_id=%s source=%s", agent.id, invocation_source.value)
    runtime_agent = agent.with_system_prompt(
        append_schema_instruction(rendered_prompt, agent.output_schema),
    )

    trace_ctx = TraceContext(
        session_id=session_id,
        user_id=current_user.user_id,
        agent_id=agent.id,
        model_name=get_model_name(runtime_agent, model_config_data),
        invocation_source=invocation_source,
        request_id=request_id,
        client_conversation_id=client_conversation_id,
    )
    await trace_ctx.start(user_message)
    runtime_context = replace(
        runtime_context,
        agent_id=agent.id,
        permission_preset=agent.permission_preset,
        invocation_source=invocation_source.value,
        trace_ctx=trace_ctx,
    )
    try:
        agent_executor_graph: CompiledStateGraph = await create_agent_instance(
            runtime_agent,
            skills_data,
            mcps_data,
            model_config_data,
            runtime_context=runtime_context,
            trace_ctx=trace_ctx,
            # 计划步骤不能被最终结构化输出 Schema 约束；Schema 只用于最终汇总。
            planning_execution_prompt=rendered_prompt,
        )
    except Exception as exc:
        await trace_ctx.error(str(exc))
        raise

    return PreparedChatRun(
        agent_executor=agent_executor_graph,
        history_messages=history_messages,
        max_tool_rounds=max(1, min(agent.iteration_count, 100)),
        execution_timeout_seconds=agent.execution_timeout_seconds,
        thread_id=thread_id,
        trace_ctx=trace_ctx,
        output_schema=agent.output_schema,
        state_context=AgentStateContext(
            runtime_file_ids=list(runtime_file_ids or []),
            available_skills=[item.name for item in skills],
            loaded_skills=[],
            current_input=user_message,
            current_node_id=current_node_id,
            planning_mode=agent.planning_mode,
        ),
    )


async def prepare_chat_run(
    user: Dict[str, Any],
    message: str,
    session_id: int,
    images: Optional[List[str]] = None,
    file_ids: Optional[List[str]] = None,
) -> PreparedChatRun:
    """加载并组装执行一次聊天请求所需的强类型运行时数据。"""
    current_user: ChatUser = ChatUser.from_mapping(user)
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
    runtime_files :list[RuntimeFile] = [RuntimeFile.from_mapping(item) for item in runtime_file_rows]

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

    # 每次请求使用新的 LangGraph thread_id，因为完整历史已经由 MySQL 提供。
    # 如果这里复用 session_id，同进程内还会叠加 InMemorySaver 里的状态，
    # 可能导致模型看到重复上下文。
    thread_id = f"session_{session_id}_message_{user_message_id}"
    return await _prepare_agent_run(
        current_user=current_user,
        agent=agent,
        user_message=message,
        history_messages=history_messages,
        thread_id=thread_id,
        runtime_context=RuntimeContext(
            user_id=current_user.user_id,
            workspace_id=f"session-{session_id}",
            session_id=session_id,
        ),
        session_id=session_id,
        invocation_source=InvocationSource.PLATFORM,
        runtime_file_ids=[item.id for item in runtime_files],
        template_session_id=str(session_id),
        current_node_id="chat",
    )


async def prepare_api_chat_run(
    user: ApiAuthenticatedUser,
    agent_id: int,
    request_id: str,
    chat_request: ExternalChatRequest,
) -> PreparedChatRun:
    """根据 API Key 用户和调用方历史准备无状态 Agent 执行。

    Args:
        user: 由 API Key 认证得到的当前用户实体。
        agent_id: 外部调用方希望执行的 Agent ID。
        request_id: 服务端为本次 API 调用生成的唯一请求 ID。
        chat_request: 已完成角色、长度和最后一条消息校验的请求实体。

    Returns:
        不依赖平台会话和消息表的 Agent 运行实体。
    """
    agent: Optional[Agent] = await get_agent(agent_id, user.user_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    current_user = ChatUser(user_id=user.user_id, username=user.username)
    history_messages = [
        ChatHistoryMessage(role=message.role, content=message.content)
        for message in chat_request.messages
    ]
    return await _prepare_agent_run(
        current_user=current_user,
        agent=agent,
        user_message=chat_request.latest_user_message(),
        history_messages=history_messages,
        thread_id=f"api_{request_id}",
        runtime_context=RuntimeContext(
            user_id=user.user_id,
            workspace_id=f"api-{request_id}",
            node_id="api",
        ),
        session_id=None,
        invocation_source=InvocationSource.API,
        template_session_id=chat_request.client_conversation_id or request_id,
        current_node_id="api",
        request_id=request_id,
        client_conversation_id=chat_request.client_conversation_id,
    )


async def _fail_task_plan_for_run(
    run: PreparedChatRun,
    error_text: str,
) -> None:
    """在聊天异常结束时回收当前请求关联的显式任务计划。

    Args:
        run: 当前聊天运行实体，提供规划模式和 Trace 主键。
        error_text: 本次运行失败或被取消的原因。
    """
    if run.state_context.planning_mode is not PlanningMode.EXPLICIT:
        return
    trace_run_id = run.trace_ctx.run_id
    if trace_run_id is None:
        return
    try:
        await fail_active_task_plan_by_trace(trace_run_id, error_text)
    except Exception as exc:
        # 计划回收属于异常路径的补偿操作，失败时记录日志但不覆盖原始错误。
        log.exception(
            "[TaskPlan] cleanup failed | trace_run_id=%s | error=%s",
            trace_run_id,
            exc,
        )


async def _stream_prepared_chat(
    run: PreparedChatRun,
    user_message: str,
    images: Optional[List[str]],
    persist_session_id: Optional[int],
    emit_completion_event: bool = False,
) -> AsyncGenerator[str, None]:
    """执行已准备的 Agent 运行，并按入口策略决定是否持久化消息。

    Args:
        run: 已装配执行器、历史、Trace 和 State 的运行实体。
        user_message: 本轮最新用户消息。
        images: 平台聊天当前轮附带的 Base64 图片；API 入口传 ``None``。
        persist_session_id: 需要保存助手消息的平台会话 ID；API 入口传 ``None``。
        emit_completion_event: 是否为外部调用方追加包含完整回答的完成事件。

    Yields:
        Agent 执行期间产生的 SSE 数据块。
    """
    full_response: List[str] = []
    reasoning_response: List[str] = []
    # Token 先按 LLM 轮次暂存，收到分类事件后再进入正式回答或执行说明。
    pending_rounds: Dict[str, List[str]] = {}
    stream_failed = False
    stream_error_text = "Agent stream failed"
    execution_label = (
        f"Session#{persist_session_id}"
        if persist_session_id is not None
        else f"API#{run.thread_id}"
    )

    try:
        async for chunk in stream_agent_response(
            agent_executor=run.agent_executor,
            user_message=user_message,
            thread_id=run.thread_id,
            history_messages=run.history_messages,
            max_tool_rounds=run.max_tool_rounds,
            execution_timeout_seconds=run.execution_timeout_seconds,
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
                        stream_error_text = str(event.get("content") or stream_error_text)
                    elif event_type == "done":
                        # 结构化校验完成后再发 done，保证客户端不会提前结束。
                        suppress_chunk = True
                except json.JSONDecodeError:
                    pass
            if not suppress_chunk:
                yield chunk
    except asyncio.CancelledError:
        log.info("[%s] client disconnected", execution_label)
        await _fail_task_plan_for_run(run, "client disconnected")
        await run.trace_ctx.cancelled("client disconnected")
        return
    except Exception as exc:
        log.exception("[%s] chat failed", execution_label)
        await _fail_task_plan_for_run(run, str(exc))
        await run.trace_ctx.error(str(exc))
        yield sse_event("error", str(exc))
        yield sse_event("done")
        return

    if stream_failed:
        await _fail_task_plan_for_run(run, stream_error_text)
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
            await _fail_task_plan_for_run(run, str(exc))
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
        if persist_session_id is not None:
            await execute(
                "INSERT INTO chat_messages "
                "(session_id, role, content, reasoning_content, structured_content, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    persist_session_id,
                    "assistant",
                    assistant_text,
                    "".join(reasoning_response) or None,
                    json.dumps(structured_content, ensure_ascii=False)
                    if structured_content is not None else None,
                    _now(),
                ),
            )
        await run.trace_ctx.finish(assistant_text)
        if emit_completion_event:
            yield sse_event(
                "response_completed",
                assistant_text,
                reasoning_content="".join(reasoning_response),
                structured_content=structured_content,
            )
        if structured_content is not None:
            yield sse_event("structured_result", json.dumps(structured_content, ensure_ascii=False))
    else:
        await _fail_task_plan_for_run(run, "empty response")
        await run.trace_ctx.error("empty response")
    yield sse_event("done")


async def stream_chat(
    user: Dict[str, Any],
    message: str,
    session_id: int,
    images: Optional[List[str]] = None,
    file_ids: Optional[List[str]] = None,
) -> AsyncGenerator[str, None]:
    """执行平台聊天，历史和本轮回复均由平台会话负责持久化。

    Args:
        user: 平台 JWT 认证得到的当前用户信息。
        message: 本轮用户消息。
        session_id: 平台负责维护的会话 ID。
        images: 本轮附带的 Base64 图片列表。
        file_ids: 本轮允许 Runtime 工具读取的文件 ID。

    Yields:
        Agent 执行期间产生的 SSE 数据块。
    """
    run = await prepare_chat_run(user, message, session_id, images, file_ids)
    async for chunk in _stream_prepared_chat(run, message, images, session_id):
        yield chunk


async def stream_api_chat(
    run: PreparedChatRun,
    chat_request: ExternalChatRequest,
) -> AsyncGenerator[str, None]:
    """执行外部无状态聊天，不写入平台会话和消息表。

    Args:
        run: 通过 API Key 用户和调用方历史准备的运行实体。
        chat_request: 外部调用方提交的完整历史实体。

    Yields:
        Agent 执行期间产生的 SSE 数据块。
    """
    async for chunk in _stream_prepared_chat(
        run,
        chat_request.latest_user_message(),
        images=None,
        persist_session_id=None,
        emit_completion_event=True,
    ):
        yield chunk
