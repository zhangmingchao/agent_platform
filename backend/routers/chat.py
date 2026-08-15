import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ..crewai_engine import chat_stream
from ..database import execute, fetch_all, fetch_one
from ..services.crew_service import get_crew
from ..services.flow_service import get_flow
from ..services.trace_service import create_trace, finish_trace

router = APIRouter(prefix="/api/chat", tags=["Chat"])
log = logging.getLogger("agent-platform")


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def _create_chat_response(user: Dict, message: str, session_id: int):
    session = await fetch_one(
        "SELECT id, target_type, target_id FROM chat_sessions WHERE id=%s AND user_id=%s",
        (session_id, user["user_id"]),
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在，请重新创建会话")
    if session["target_type"] == "crew":
        target = await get_crew(session["target_id"], user["user_id"], runtime=True)
    else:
        target = await get_flow(session["target_id"], user["user_id"])
    if not target or not target.get("enabled", True):
        raise HTTPException(status_code=404, detail="执行目标不存在或已禁用")

    history = await fetch_all(
        "SELECT role, content FROM chat_messages WHERE session_id=%s ORDER BY id", (session_id,)
    )
    history_messages = [{"role": item["role"], "content": item["content"]} for item in history]
    await execute(
        "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
        (session_id, "user", message, _now()),
    )
    if not history:
        title = message[:50].replace("\n", " ").strip() or "新对话"
        await execute("UPDATE chat_sessions SET title=%s WHERE id=%s", (title, session_id))

    model = ""
    if session["target_type"] == "crew" and target.get("agents"):
        model = target["agents"][0].get("model", "")
    trace_id = await create_trace(
        user_id=user["user_id"], target_type=session["target_type"],
        target_id=session["target_id"], target_name=target.get("name", ""),
        session_id=session_id, user_message=message, model=model,
    )
    trace_started = time.time()

    async def generate():
        current_phase_response = []
        final_response = None
        try:
            async for chunk in chat_stream(
                target_type=session["target_type"], target_definition=target,
                user_id=user["user_id"], user_message=message,
                history_messages=history_messages, session_id=session_id, trace_id=trace_id,
            ):
                if chunk.startswith("data:"):
                    try:
                        event = json.loads(chunk[5:].strip())
                        if event.get("type") == "phase_start":
                            current_phase_response = []
                        elif event.get("type") == "chunk":
                            current_phase_response.append(event.get("content", ""))
                        elif event.get("type") == "result":
                            final_response = event.get("content", "")
                    except json.JSONDecodeError:
                        pass
                yield chunk
        except asyncio.CancelledError:
            partial_response = final_response if final_response is not None else "".join(current_phase_response)
            await finish_trace(trace_id, "cancelled", partial_response, "客户端断开连接", int((time.time() - trace_started) * 1000))
            return
        except Exception as exc:
            log.exception("[Trace#%s] CrewAI 执行失败", trace_id)
            partial_response = final_response if final_response is not None else "".join(current_phase_response)
            await finish_trace(trace_id, "error", partial_response, str(exc), int((time.time() - trace_started) * 1000))
            yield f"data:{json.dumps({'type': 'error', 'content': str(exc)}, ensure_ascii=False)}\n\n"
            return

        assistant_text = final_response if final_response is not None else "".join(current_phase_response)
        if assistant_text.strip():
            await execute(
                "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (%s, %s, %s, %s)",
                (session_id, "assistant", assistant_text, _now()),
            )
        await finish_trace(trace_id, "success", assistant_text, duration_ms=int((time.time() - trace_started) * 1000))

    return StreamingResponse(generate(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no",
    })


@router.post("/stream")
async def api_chat_stream_post(
    request: Request,
    user: Dict = Depends(get_current_user),
):
    body = await request.json()
    message, session_id = body.get("message", ""), body.get("session_id")
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    if not isinstance(session_id, int):
        raise HTTPException(status_code=400, detail="需要有效的 session_id")
    return await _create_chat_response(user, message, session_id)


@router.get("/stream")
async def api_chat_stream_get(
    message: str = Query(...),
    session_id: int = Query(...),
    token: Optional[str] = Query(None),
    user: Dict = Depends(get_current_user),
):
    return await _create_chat_response(user, message, session_id)
