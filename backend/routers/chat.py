"""聊天路由 — 提供 LangGraph 流式聊天的 HTTP 接口。"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ..services.chat_service import stream_chat

router = APIRouter(prefix="/api/chat", tags=["Chat"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _validate_chat_request(message, session_id):
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    if not isinstance(session_id, int):
        raise HTTPException(status_code=400, detail="需要有效的 session_id")


def _chat_response(user: dict, message: str, session_id: int):
    return StreamingResponse(
        stream_chat(user=user, message=message, session_id=session_id),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post("/stream")
async def api_chat_stream_post(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id")
    _validate_chat_request(message, session_id)
    return _chat_response(user, message, session_id)


@router.get("/stream")
async def api_chat_stream(
    message: str = Query(...),
    session_id: int = Query(...),
    user: dict = Depends(get_current_user),
):
    _validate_chat_request(message, session_id)
    return _chat_response(user, message, session_id)
