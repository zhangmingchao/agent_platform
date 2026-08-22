"""用于 Token 存储的 Redis 客户端。"""
import logging
from typing import Optional

import redis.asyncio as aioredis

from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, JWT_EXPIRE_HOURS

log = logging.getLogger("agent-platform")

_pool: Optional[aioredis.ConnectionPool] = None


async def get_redis() -> aioredis.Redis:
    """从连接池获取 Redis 连接。"""
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD or None,
            decode_responses=True,
        )
    return aioredis.Redis(connection_pool=_pool)


async def close_redis():
    """关闭时释放 Redis 连接池。"""
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None


async def set_token(token: str, user_id: int):
    """将 token → user_id 存入 Redis，TTL 与 JWT 过期时间一致。"""
    r = await get_redis()
    await r.setex(f"token:{token}", JWT_EXPIRE_HOURS * 3600, str(user_id))


async def get_token_user_id(token: str) -> Optional[int]:
    """根据 token 从 Redis 获取 user_id，未找到返回 None。"""
    r = await get_redis()
    val = await r.get(f"token:{token}")
    return int(val) if val else None


async def delete_token(token: str):
    """从 Redis 删除 token（登出）。"""
    r = await get_redis()
    await r.delete(f"token:{token}")
