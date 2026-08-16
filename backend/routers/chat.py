"""Chat router — LangChain/LangGraph streaming endpoint with local trace."""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ..core.agent_factory import create_agent_instance, get_model_name
from ..core.streaming import stream_agent_response, sse_event
from ..core.trace_handler import TraceContext
from ..database import execute, fetch_one
from ..services.agent_service import get_agent
from ..services.mcp_config_service import get_agent_mcps
from ..services.skill_service import get_agent_skills

router = APIRouter(prefix="/api/chat", tags=["Chat"])
log = logging.getLogger("agent-platform")


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def _load_model_config(agent, user_id):
    model_config_id = agent.get("model_config_id")
    if not model_config_id:
        return None
    from ..services.model_service import get_model
    return await get_model(model_config_id, user_id)


async def _create_chat_response(user: dict, message: str, session_id: int):
    session = await fetch_one(
        "SELECT id, agent_id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"]),
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在，请重新创建会话")

    agent = await get_agent(session["agent_id"], user["user_id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    await execute(
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

    skills_data = await get_agent_skills(agent["id"])
    mcps_data = await get_agent_mcps(agent["id"])
    model_config = await _load_model_config(agent, user["user_id"])

    agent_executor = create_agent_instance(agent, skills_data, mcps_data, model_config)

    max_tool_rounds = max(1, min(int(agent.get("iteration_count") or 6), 100))
    thread_id = f"session_{session_id}"
    model_name = get_model_name(agent, model_config)

    trace_ctx = TraceContext(
        session_id=session_id,
        user_id=user["user_id"],
        agent_id=agent["id"],
        model_name=model_name,
    )
    await trace_ctx.start(message)

    async def generate():
        full_response = []
        try:
            async for chunk in stream_agent_response(
                agent_executor=agent_executor,
                user_message=message,
                thread_id=thread_id,
                max_tool_rounds=max_tool_rounds,
                trace_ctx=trace_ctx,
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
            await trace_ctx.error("client disconnected")
            return
        except Exception as exc:
            log.exception("[Session#%s] chat failed", session_id)
            await trace_ctx.error(str(exc))
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
            await trace_ctx.finish(assistant_text)
        else:
            await trace_ctx.error("empty response")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/stream")
async def api_chat_stream_post(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id")
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    if not isinstance(session_id, int):
        raise HTTPException(status_code=400, detail="需要有效的 session_id")
    return await _create_chat_response(user, message, session_id)


@router.get("/stream")
async def api_chat_stream(
    message: str = Query(...),
    session_id: int = Query(...),
    user: dict = Depends(get_current_user),
):
    return await _create_chat_response(user, message, session_id)
