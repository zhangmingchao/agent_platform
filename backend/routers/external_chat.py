"""通过用户 API Key 调用的无状态 Agent 聊天接口。"""

from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..api_auth import get_api_authenticated_user
from ..config import EXTERNAL_API_CHAT_RATE_LIMIT, HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS
from ..models.api_access import ApiAuthenticatedUser, ExternalChatRequest
from ..rate_limit import RateLimitRule, enforce_rate_limit
from ..services.chat_service import prepare_api_chat_run, stream_api_chat

router = APIRouter(prefix="/api/v1", tags=["External Agent API"])
EXTERNAL_CHAT_RULE = RateLimitRule(
    name="external-chat-api-key",
    limit=EXTERNAL_API_CHAT_RATE_LIMIT,
    window_seconds=HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS,
)
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.post("/agents/{agent_id}/chat/stream")
async def api_external_chat_stream(
    agent_id: int,
    chat_request: ExternalChatRequest,
    user: ApiAuthenticatedUser = Depends(get_api_authenticated_user),
) -> StreamingResponse:
    """使用调用方提供的完整历史执行一次无状态流式聊天。

    Args:
        agent_id: 当前 API Key 用户拥有的 Agent ID。
        chat_request: 调用方维护的完整 user/assistant 消息历史。
        user: 由 ``X-API-Key`` 认证依赖解析出的用户实体。

    Returns:
        使用现有 Agent SSE 事件协议返回的流式响应。
    """
    await enforce_rate_limit(EXTERNAL_CHAT_RULE, user.api_key_id)
    request_id = uuid4().hex
    run = await prepare_api_chat_run(user, agent_id, request_id, chat_request)
    return StreamingResponse(
        stream_api_chat(run, chat_request),
        media_type="text/event-stream",
        headers={**SSE_HEADERS, "X-Request-ID": request_id},
    )
