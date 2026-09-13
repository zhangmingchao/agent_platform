"""基于 Redis 的分布式固定窗口接口限流。"""

import hashlib
import logging
import time
from dataclasses import dataclass

from fastapi import HTTPException, Request
from redis.exceptions import RedisError

from .config import TRUST_PROXY_HEADERS
from .redis_client import get_redis

log = logging.getLogger(__name__)

_RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""


@dataclass(frozen=True)
class RateLimitRule:
    """接口限流规则。

    Attributes:
        name: Redis Key 使用的稳定规则名称。
        limit: 一个固定时间窗口内允许的最大请求数。
        window_seconds: 固定时间窗口的秒数。
    """

    name: str
    limit: int
    window_seconds: int


@dataclass(frozen=True)
class RateLimitDecision:
    """一次限流判断结果。

    Attributes:
        allowed: 本次请求是否允许继续执行。
        remaining: 当前窗口剩余可用次数。
        retry_after_seconds: 当前窗口距离重置还剩多少秒。
    """

    allowed: bool
    remaining: int
    retry_after_seconds: int


def get_client_ip(request: Request) -> str:
    """获取请求来源 IP，仅在显式启用时信任代理头。

    Args:
        request: 当前 FastAPI HTTP 请求。

    Returns:
        用于登录和注册限流的客户端 IP 字符串。
    """
    if TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(rule: RateLimitRule, identity: str) -> RateLimitDecision:
    """在 Redis 中原子增加计数并返回限流判断。

    Args:
        rule: 当前接口使用的限流规则实体。
        identity: 用户 ID、用户名或来源 IP 等限流主体。

    Returns:
        包含是否放行、剩余次数和重试时间的判断实体。
    """
    if rule.limit <= 0 or rule.window_seconds <= 0:
        raise ValueError("限流次数和窗口必须大于 0")
    identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    window_id = int(time.time()) // rule.window_seconds
    key = f"rate-limit:{rule.name}:{identity_hash}:{window_id}"
    redis = await get_redis()
    count_raw, ttl_raw = await redis.eval(
        _RATE_LIMIT_SCRIPT,
        1,
        key,
        rule.window_seconds,
    )
    count = int(count_raw)
    ttl = max(1, int(ttl_raw))
    return RateLimitDecision(
        allowed=count <= rule.limit,
        remaining=max(0, rule.limit - count),
        retry_after_seconds=ttl,
    )


async def enforce_rate_limit(rule: RateLimitRule, identity: str) -> None:
    """执行限流判断，拒绝超限请求或 Redis 不可用时的高风险请求。

    Args:
        rule: 当前接口使用的限流规则实体。
        identity: 当前限流主体的稳定标识。
    """
    try:
        decision = await check_rate_limit(rule, identity)
    except RedisError as exc:
        log.exception("限流 Redis 不可用: rule=%s", rule.name)
        raise HTTPException(status_code=503, detail="安全限流服务暂时不可用") from exc
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后重试",
            headers={"Retry-After": str(decision.retry_after_seconds)},
        )
