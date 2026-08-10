import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ..chat_engine import chat_stream
from ..database import execute, fetch_all, fetch_one
from ..services.agent_service import get_agent
from ..services.mcp_config_service import get_agent_mcps
from ..services.skill_service import get_agent_skills
from ..services.trace_service import create_trace, finish_trace

router = APIRouter(prefix="/api/chat", tags=["Chat"])
log = logging.getLogger("agent-platform")


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def _create_chat_response(request: Request, message: str, session_id: int):
    user = get_current_user(request)

    session = await fetch_one(
        "SELECT id, agent_id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"]),
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在，请重新创建会话")

    agent = await get_agent(session["agent_id"], user["user_id"])
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")

    history = await fetch_all(
        "SELECT role, content FROM chat_messages WHERE session_id=%s ORDER BY id ASC",
        (session_id,),
    )
    history_messages = [{"role": item["role"], "content": item["content"]} for item in history]

    await execute(
        "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
        (session_id, "user", message, _now()),
    )
    if not history:
        title = message[:50].replace("\n", " ").strip() or "新对话"
        await execute("UPDATE chat_sessions SET title=%s WHERE id=%s", (title, session_id))

    skills_data = await get_agent_skills(agent["id"])
    mcps_data = await get_agent_mcps(agent["id"])
    trace_id = await create_trace(
        user_id=user["user_id"],
        agent_id=agent["id"],
        session_id=session_id,
        user_message=message,
        model=agent.get("model", ""),
    )
    trace_started = time.time()

    async def generate():
        full_response = []
        try:
            async for chunk in chat_stream(
                agent=agent,
                skills=skills_data,
                mcp_configs=mcps_data,
                user_message=message,
                history_messages=history_messages,
                session_id=session_id,
                trace_id=trace_id,
            ):
                if chunk.startswith("data:"):
                    payload_text = chunk[5:]
                    if payload_text.endswith("\n\n"):
                        payload_text = payload_text[:-2]
                    try:
                        event = json.loads(payload_text)
                        if event.get("type") == "chunk":
                            full_response.append(event.get("content", ""))
                    except json.JSONDecodeError:
                        # 兼容旧版 chat_stream 产生的纯文本 SSE 数据。
                        if payload_text:
                            full_response.append(payload_text)
                yield chunk
        except asyncio.CancelledError:
            # 用户刷新、切换页面或关闭浏览器时会取消 SSE；这是正常断开，不是服务异常。
            log.info("[会话#%s] 客户端已断开 SSE 连接", session_id)
            await finish_trace(
                trace_id,
                "cancelled",
                output_text="".join(full_response),
                error_text="客户端断开连接",
                duration_ms=int((time.time() - trace_started) * 1000),
            )
            return
        except Exception as exc:
            log.exception("[Trace#%s] 对话执行失败", trace_id)
            await finish_trace(
                trace_id,
                "error",
                output_text="".join(full_response),
                error_text=str(exc),
                duration_ms=int((time.time() - trace_started) * 1000),
            )
            raise

        assistant_text = "".join(full_response)
        if assistant_text.strip():
            await execute(
                "INSERT INTO chat_messages (session_id, role, content, created_at) "
                "VALUES (%s, %s, %s, %s)",
                (session_id, "assistant", assistant_text, _now()),
            )
        await finish_trace(
            trace_id,
            "success",
            output_text=assistant_text,
            duration_ms=int((time.time() - trace_started) * 1000),
        )

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
async def api_chat_stream_post(request: Request):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id")
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    if not isinstance(session_id, int):
        raise HTTPException(status_code=400, detail="需要有效的 session_id")
    return await _create_chat_response(request, message, session_id)


@router.get("/stream")
async def api_chat_stream(
    request: Request,
    message: str = Query(...),
    session_id: int = Query(...),
    token: Optional[str] = Query(None),
):
    return await _create_chat_response(request, message, session_id)
