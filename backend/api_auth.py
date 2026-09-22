"""外部接口 API Key 认证依赖。"""

from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from .config import API_KEY_AUTH_RATE_LIMIT_PER_IP, AUTH_RATE_LIMIT_WINDOW_SECONDS
from .models.api_access import ApiAuthenticatedUser
from .rate_limit import RateLimitRule, enforce_rate_limit, get_client_ip
from .services.api_key_service import authenticate_api_key

API_KEY_AUTH_RULE = RateLimitRule(
    name="api-key-auth-ip",
    limit=API_KEY_AUTH_RATE_LIMIT_PER_IP,
    window_seconds=AUTH_RATE_LIMIT_WINDOW_SECONDS,
)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_authenticated_user(
    request: Request,
    x_api_key: Optional[str] = Security(API_KEY_HEADER),
) -> ApiAuthenticatedUser:
    """通过 ``X-API-Key`` 解析外部接口调用用户。

    Args:
        request: 当前 FastAPI 请求，用于提取来源 IP 并执行认证限流。
        x_api_key: 外部调用方放在请求头中的完整 API Key。

    Returns:
        API Key 所属的强类型用户身份。

    Raises:
        HTTPException: 请求缺少密钥、密钥无效或认证请求超过限流时抛出。
    """
    await enforce_rate_limit(API_KEY_AUTH_RULE, get_client_ip(request))
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="缺少 X-API-Key 请求头",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    user = await authenticate_api_key(x_api_key)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="API Key 无效或已被吊销",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return user
