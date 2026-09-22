"""平台用户 API Key 管理接口。"""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..config import API_KEY_MANAGEMENT_RATE_LIMIT, HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS
from ..models.api_access import ApiKeyRevocationResult, ApiKeyStatus, IssuedApiKey
from ..rate_limit import RateLimitRule, enforce_rate_limit
from ..services.api_key_service import get_api_key_status, issue_api_key, revoke_api_key

router = APIRouter(prefix="/api/api-key", tags=["API Key"])
API_KEY_MANAGEMENT_RULE = RateLimitRule(
    name="api-key-management-user",
    limit=API_KEY_MANAGEMENT_RATE_LIMIT,
    window_seconds=HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS,
)


@router.get("")
async def api_get_api_key_status(
    user: Dict[str, Any] = Depends(get_current_user),
) -> ApiKeyStatus:
    """返回当前登录用户的脱敏 API Key 状态。

    Args:
        user: 由平台 JWT 认证依赖解析出的当前用户。
    """
    return await get_api_key_status(int(user["user_id"]))


@router.post("")
async def api_issue_api_key(
    user: Dict[str, Any] = Depends(get_current_user),
) -> IssuedApiKey:
    """创建或轮换当前用户的 API Key，完整密钥只返回一次。

    Args:
        user: 由平台 JWT 认证依赖解析出的当前用户。
    """
    user_id = int(user["user_id"])
    await enforce_rate_limit(API_KEY_MANAGEMENT_RULE, str(user_id))
    return await issue_api_key(user_id)


@router.delete("")
async def api_revoke_api_key(
    user: Dict[str, Any] = Depends(get_current_user),
) -> ApiKeyRevocationResult:
    """吊销当前登录用户的有效 API Key。

    Args:
        user: 由平台 JWT 认证依赖解析出的当前用户。
    """
    user_id = int(user["user_id"])
    await enforce_rate_limit(API_KEY_MANAGEMENT_RULE, str(user_id))
    return await revoke_api_key(user_id)
