"""聊天路由 — 提供 LangGraph 流式聊天的 HTTP 接口。"""
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..auth import get_current_user
from ..config import CHAT_RATE_LIMIT, HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS
from ..rate_limit import RateLimitRule, enforce_rate_limit
from ..redis_client import acquire_stream_lock, release_stream_lock
from ..services.chat_service import stream_chat

router = APIRouter(prefix="/api/chat", tags=["Chat"])
CHAT_STREAM_RULE = RateLimitRule(
    name="chat-stream-user",
    limit=CHAT_RATE_LIMIT,
    window_seconds=HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS,
)

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}

MAX_IMAGES = 3
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_RUNTIME_FILES = 10


def _validate_chat_request(message: object, session_id: object) -> None:
    """校验聊天消息和会话 ID。

    Args:
        message: 从请求体中读取、尚未完成类型校验的聊天消息。
        session_id: 从请求体中读取、尚未完成类型校验的会话 ID。
    """
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    if not isinstance(session_id, int):
        raise HTTPException(status_code=400, detail="需要有效的 session_id")


def _validate_images(images: object) -> List[str]:
    """校验图片 Base64 列表。

    Args:
        images: 从请求体中读取、尚未完成类型校验的图片列表。

    Returns:
        过滤无效图片并完成数量、大小校验后的 Base64 字符串列表。
    """
    if not images or not isinstance(images, list):
        return []
    if len(images) > MAX_IMAGES:
        raise HTTPException(status_code=400, detail=f"单次最多发送 {MAX_IMAGES} 张图片")
    cleaned = []
    for img in images:
        if not isinstance(img, str) or not img.startswith("data:image/"):
            continue
        if len(img) > MAX_IMAGE_SIZE * 1.4:
            raise HTTPException(status_code=400, detail=f"单张图片不能超过 {MAX_IMAGE_SIZE // 1024}KB")
        cleaned.append(img)
    return cleaned


def _validate_file_ids(file_ids: object) -> List[str]:
    """校验 Runtime 文件 ID 列表，并去除重复项。

    Args:
        file_ids: 从请求体中读取、尚未完成类型校验的 Runtime 文件 ID 列表。

    Returns:
        去除空值和重复项后的 Runtime 文件 ID 列表。
    """
    if file_ids is None:
        return []
    if not isinstance(file_ids, list) or any(not isinstance(item, str) for item in file_ids):
        raise HTTPException(status_code=400, detail="file_ids 必须是字符串列表")
    cleaned = list(dict.fromkeys(item.strip() for item in file_ids if item.strip()))
    if len(cleaned) > MAX_RUNTIME_FILES:
        raise HTTPException(status_code=400, detail=f"单次最多使用 {MAX_RUNTIME_FILES} 个文件")
    return cleaned


async def _guarded_stream(
    generator: AsyncIterable[str],
    session_id: int,
) -> AsyncGenerator[str, None]:
    """包装异步数据流，确保流结束后释放会话锁。

    Args:
        generator: 按顺序产生 SSE 字符串数据块的异步可迭代对象。
        session_id: 当前流式聊天对应的会话 ID，用于释放会话锁。

    Yields:
        上游异步数据流产生的 SSE 字符串数据块。
    """
    try:
        async for chunk in generator:
            yield chunk
    finally:
        await release_stream_lock(session_id)


@router.post("/stream")
async def api_chat_stream_post(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
) -> StreamingResponse:
    body = await request.json()
    message = body.get("message", "")
    session_id = body.get("session_id")
    images = _validate_images(body.get("images"))
    file_ids = _validate_file_ids(body.get("file_ids"))
    _validate_chat_request(message, session_id)
    await enforce_rate_limit(CHAT_STREAM_RULE, str(user["user_id"]))

    acquired = await acquire_stream_lock(session_id)
    if not acquired:
        raise HTTPException(status_code=429, detail="该会话正在生成回复，请等待完成或停止当前生成")

    return StreamingResponse(
        _guarded_stream(
            stream_chat(
                user=user, message=message, session_id=session_id,
                images=images, file_ids=file_ids,
            ),
            session_id,
        ),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/stream")
async def api_chat_stream(
    message: str = Query(...),
    session_id: int = Query(...),
    user: Dict[str, Any] = Depends(get_current_user),
) -> StreamingResponse:
    _validate_chat_request(message, session_id)
    await enforce_rate_limit(CHAT_STREAM_RULE, str(user["user_id"]))

    acquired = await acquire_stream_lock(session_id)
    if not acquired:
        raise HTTPException(status_code=429, detail="该会话正在生成回复，请等待完成或停止当前生成")

    return StreamingResponse(
        _guarded_stream(
            stream_chat(user=user, message=message, session_id=session_id),
            session_id,
        ),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
