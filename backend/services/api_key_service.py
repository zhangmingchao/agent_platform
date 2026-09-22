"""用户 API Key 的生成、哈希验证、状态查询与吊销服务。"""

import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Optional, Tuple

from ..database import execute, fetch_one
from ..models.api_access import (
    ApiAuthenticatedUser,
    ApiKeyRevocationResult,
    ApiKeyStatus,
    IssuedApiKey,
)

API_KEY_SCHEME = "ap_live_"


def _now() -> datetime:
    """返回数据库记录使用的 UTC 时间。"""
    return datetime.utcnow()


def _hash_api_key(api_key: str) -> str:
    """计算完整 API Key 的 SHA-256 哈希。

    Args:
        api_key: 完整 API Key 明文。

    Returns:
        用于数据库存储和常量时间比较的十六进制哈希。
    """
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _parse_api_key(api_key: str) -> Optional[Tuple[str, str]]:
    """解析 API Key 中用于查询的公开 ID 和 secret。

    Args:
        api_key: HTTP Header 中收到的完整 API Key。

    Returns:
        格式正确时返回 ``(key_id, secret)``，否则返回 ``None``。
    """
    if not api_key.startswith(API_KEY_SCHEME) or "." not in api_key:
        return None
    public_part, secret = api_key.split(".", 1)
    key_id = public_part[len(API_KEY_SCHEME):]
    if len(key_id) != 16 or not secret or len(api_key) > 200:
        return None
    return key_id, secret


async def issue_api_key(user_id: int) -> IssuedApiKey:
    """为用户创建或轮换唯一 API Key，旧密钥会立即失效。

    Args:
        user_id: 当前平台登录用户 ID。

    Returns:
        只在本次响应中包含完整明文的签发结果实体。
    """
    key_id = secrets.token_hex(8)
    secret = secrets.token_urlsafe(32)
    api_key = f"{API_KEY_SCHEME}{key_id}.{secret}"
    key_prefix = f"{API_KEY_SCHEME}{key_id}"
    created_at = _now()
    existing = await fetch_one(
        "SELECT id FROM user_api_keys WHERE user_id=%s",
        (user_id,),
    )
    if existing:
        await execute(
            "UPDATE user_api_keys SET key_id=%s, key_prefix=%s, key_hash=%s, "
            "status='active', created_at=%s, updated_at=%s, last_used_at=NULL, revoked_at=NULL "
            "WHERE user_id=%s",
            (key_id, key_prefix, _hash_api_key(api_key), created_at, created_at, user_id),
        )
    else:
        await execute(
            "INSERT INTO user_api_keys "
            "(user_id, key_id, key_prefix, key_hash, status, created_at, updated_at, "
            "last_used_at, revoked_at) VALUES (%s, %s, %s, %s, 'active', %s, %s, NULL, NULL)",
            (user_id, key_id, key_prefix, _hash_api_key(api_key), created_at, created_at),
        )
    return IssuedApiKey(
        api_key=api_key,
        key_prefix=key_prefix,
        created_at=created_at,
    )


async def get_api_key_status(user_id: int) -> ApiKeyStatus:
    """查询用户 API Key 的脱敏状态。

    Args:
        user_id: 当前平台登录用户 ID。

    Returns:
        不包含哈希和明文的状态实体。
    """
    row = await fetch_one(
        "SELECT key_prefix, status, created_at, last_used_at "
        "FROM user_api_keys WHERE user_id=%s",
        (user_id,),
    )
    if not row:
        return ApiKeyStatus(configured=False)
    return ApiKeyStatus(
        configured=True,
        key_prefix=str(row.get("key_prefix") or ""),
        status=str(row.get("status") or ""),
        created_at=row.get("created_at"),
        last_used_at=row.get("last_used_at"),
    )


async def revoke_api_key(user_id: int) -> ApiKeyRevocationResult:
    """吊销用户当前有效的 API Key。

    Args:
        user_id: 当前平台登录用户 ID。

    Returns:
        表示是否实际吊销密钥的结果实体。
    """
    existing = await fetch_one(
        "SELECT id FROM user_api_keys WHERE user_id=%s AND status='active'",
        (user_id,),
    )
    if not existing:
        return ApiKeyRevocationResult(revoked=False)
    now = _now()
    await execute(
        "UPDATE user_api_keys SET status='revoked', revoked_at=%s, updated_at=%s "
        "WHERE user_id=%s AND status='active'",
        (now, now, user_id),
    )
    return ApiKeyRevocationResult(revoked=True)


async def authenticate_api_key(api_key: str) -> Optional[ApiAuthenticatedUser]:
    """验证 API Key 并返回对应用户实体。

    Args:
        api_key: 从 ``X-API-Key`` 请求头读取的完整密钥。

    Returns:
        验证成功时返回用户身份实体，失败时返回 ``None``。
    """
    parsed = _parse_api_key(api_key.strip())
    if parsed is None:
        return None
    key_id, _ = parsed
    row = await fetch_one(
        "SELECT k.user_id, k.key_hash, u.username "
        "FROM user_api_keys k JOIN users u ON u.id=k.user_id "
        "WHERE k.key_id=%s AND k.status='active'",
        (key_id,),
    )
    if not row or not hmac.compare_digest(
        str(row.get("key_hash") or ""),
        _hash_api_key(api_key.strip()),
    ):
        return None
    await execute(
        "UPDATE user_api_keys SET last_used_at=%s WHERE key_id=%s",
        (_now(), key_id),
    )
    return ApiAuthenticatedUser(
        user_id=int(row["user_id"]),
        username=str(row.get("username") or ""),
        api_key_id=key_id,
    )
