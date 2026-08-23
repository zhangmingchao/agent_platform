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

MAX_IMAGES = 3
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB


def _validate_chat_request(message, session_id):
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    if not isinstance(session_id, int):
        raise HTTPException(status_code=400, detail="需要有效的 session_id")


def _validate_images(images):
    """校验图片 base64 列表，返回清洗后的列表。"""
    if not images or not isinstance(images, list):
        return []
    if len(images) > MAX_IMAGES:
        raise HTTPException(status_code=400, detail=f"单次最多发送 {MAX_IMAGES} 张图片")
    cleaned = []
    for img in images:
        if not isinstance(img, str) or not img.startswith("data:image/"):
            continue
        if len(img) > MAX_IMAGE_SIZE * 1.4:  # base64 膨胀系数约 1.33
            raise HTTPException(status_code=400, detail=f"单张图片不能超过 {MAX_IMAGE_SIZE // 1024}KB")
        cleaned.append(img)
    return cleaned


@router.post("/stream")
async def api_chat_stream_post(request: Request, user: dict = Depends(get_current_user)):
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id")
    images = _validate_images(body.get("images"))
    _validate_chat_request(message, session_id)
    return StreamingResponse(
        stream_chat(user=user, message=message, session_id=session_id, images=images),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/stream")
async def api_chat_stream(
    message: str = Query(...),
    session_id: int = Query(...),
    user: dict = Depends(get_current_user),
):
    _validate_chat_request(message, session_id)
    return StreamingResponse(
        stream_chat(user=user, message=message, session_id=session_id),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
