"""聊天编排服务，负责会话记忆、Agent 执行与数据持久化。"""
import asyncio
import json
import logging
from datetime import datetime

from fastapi import HTTPException

from ..core.agent_factory import create_agent_instance, get_model_name
from ..core.streaming import stream_agent_response, sse_event
from ..core.trace_handler import TraceContext
from ..database import execute, fetch_all, fetch_one
from .agent_service import get_agent
from .mcp_config_service import get_agent_mcps
from .skill_service import get_agent_skills

log = logging.getLogger("agent-platform")


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def _load_model_config(agent, user_id):
    model_config_id = agent.get("model_config_id")
    if not model_config_id:
        return None
    from .model_service import get_model
    return await get_model(model_config_id, user_id)


async def prepare_chat_run(user: dict, message: str, session_id: int) -> dict:
    """加载执行一次聊天请求所需的全部运行时数据。"""
    session = await fetch_one(
        "SELECT id, agent_id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"]),
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在，请重新创建会话")

    agent = await get_agent(session["agent_id"], user["user_id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    user_message_id = await execute(
        "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
        (session_id, "user", message, _now()),
    )

    msg_count = await fetch_one(
        "SELECT COUNT(*) as cnt FROM chat_messages WHERE session_id=%s AND role='user'",
        (session_id,),
    )
    if msg_count and msg_count["cnt"] == 1:
        title = message[:50].replace("\n", " ").strip() or "新对话"
        await execute("UPDATE chat_sessions SET title=%s WHERE id=%s", (title, session_id))

    # chat_messages 是持久化的会话记忆；每次执行前从 MySQL 恢复历史，
    # 可以保证 FastAPI 进程重启后 Agent 仍然能接上上下文。
    history_messages = await fetch_all(
        "SELECT role, content FROM chat_messages "
        "WHERE session_id=%s AND role IN ('user', 'assistant') "
        "ORDER BY created_at ASC, id ASC",
        (session_id,),
    )

    skills_data = await get_agent_skills(agent["id"])
    mcps_data = await get_agent_mcps(agent["id"])
    model_config = await _load_model_config(agent, user["user_id"])
    agent_executor = await create_agent_instance(agent, skills_data, mcps_data, model_config)

    max_tool_rounds = max(1, min(int(agent.get("iteration_count") or 6), 100))
    # 每次请求使用新的 LangGraph thread_id，因为完整历史已经由 MySQL 提供。
    # 如果这里复用 session_id，同进程内还会叠加 InMemorySaver 里的状态，
    # 可能导致模型看到重复上下文。
    thread_id = f"session_{session_id}_message_{user_message_id}"

    trace_ctx = TraceContext(
        session_id=session_id,
        user_id=user["user_id"],
        agent_id=agent["id"],
        model_name=get_model_name(agent, model_config),
    )
    await trace_ctx.start(message)

    return {
        "agent_executor": agent_executor,
        "history_messages": history_messages,
        "max_tool_rounds": max_tool_rounds,
        "thread_id": thread_id,
        "trace_ctx": trace_ctx,
    }


async def stream_chat(user: dict, message: str, session_id: int):
    """运行 Agent 并生成 SSE 数据块，同时持久化助手回复。"""
    run = await prepare_chat_run(user, message, session_id)
    full_response = []

    try:
        async for chunk in stream_agent_response(
            agent_executor=run["agent_executor"],
            user_message=message,
            thread_id=run["thread_id"],
            history_messages=run["history_messages"],
            max_tool_rounds=run["max_tool_rounds"],
            trace_ctx=run["trace_ctx"],
        ):
            if chunk.startswith("data:"):
                payload = chunk[5:]
                if payload.endswith("\n\n"):
                    payload = payload[:-2]
                try:
                    event = json.loads(payload)
                    if event.get("type") == "chunk":
                        full_response.append(event.get("content", ""))
                except json.JSONDecodeError:
                    pass
            yield chunk
    except asyncio.CancelledError:
        log.info("[Session#%s] client disconnected", session_id)
        await run["trace_ctx"].error("client disconnected")
        return
    except Exception as exc:
        log.exception("[Session#%s] chat failed", session_id)
        await run["trace_ctx"].error(str(exc))
        yield sse_event("error", str(exc))
        yield sse_event("done")
        return

    assistant_text = "".join(full_response)
    if assistant_text.strip():
        await execute(
            "INSERT INTO chat_messages (session_id, role, content, created_at) "
            "VALUES (%s, %s, %s, %s)",
            (session_id, "assistant", assistant_text, _now()),
        )
        await run["trace_ctx"].finish(assistant_text)
    else:
        await run["trace_ctx"].error("empty response")
