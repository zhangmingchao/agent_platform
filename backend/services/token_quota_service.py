"""模型每日 Token 限额的查询、预占与结算服务。"""

import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Mapping, Optional
from zoneinfo import ZoneInfo

from ..database import execute, fetch_one
from ..models.token_quota import (
    ModelDailyQuotaStatus,
    ModelTokenQuotaExceededError,
    ModelTokenUsage,
    TokenQuotaMode,
    TokenReservation,
)
from ..redis_client import get_redis

_BUSINESS_TIMEZONE = ZoneInfo("Asia/Shanghai")

_RESERVE_SCRIPT = """
local current = redis.call('GET', KEYS[1])
if not current then
    current = tonumber(ARGV[1])
    redis.call('SET', KEYS[1], current)
else
    current = tonumber(current)
end
local requested = tonumber(ARGV[2])
local token_limit = tonumber(ARGV[3])
if current + requested > token_limit then
    redis.call('EXPIREAT', KEYS[1], tonumber(ARGV[4]))
    return {0, current}
end
local updated = redis.call('INCRBY', KEYS[1], requested)
redis.call('EXPIREAT', KEYS[1], tonumber(ARGV[4]))
return {1, updated}
"""

_SETTLE_SCRIPT = """
local current = redis.call('GET', KEYS[1])
if not current then
    current = tonumber(ARGV[1])
    redis.call('SET', KEYS[1], current)
else
    current = tonumber(current)
end
local updated = redis.call('INCRBY', KEYS[1], tonumber(ARGV[2]))
redis.call('EXPIREAT', KEYS[1], tonumber(ARGV[3]))
return updated
"""


def business_now() -> datetime:
    """返回用于每日额度分界的上海时区当前时间。"""
    return datetime.now(_BUSINESS_TIMEZONE)


def _quota_mode(model_config: Mapping[str, Any]) -> TokenQuotaMode:
    """把模型配置中的模式转换为受约束枚举。"""
    try:
        return TokenQuotaMode(str(model_config.get("quota_mode") or "unlimited"))
    except ValueError:
        return TokenQuotaMode.UNLIMITED


def _usage_key(user_id: int, model_config_id: int, usage_date: str) -> str:
    """生成用户、模型配置和自然日隔离的 Redis 用量键。"""
    return f"model-token-quota:{user_id}:{model_config_id}:{usage_date}"


def _expiry_timestamp(now: datetime) -> int:
    """生成次日零点后一小时的 Redis 过期时间。"""
    tomorrow = (now + timedelta(days=1)).date()
    expiry = datetime.combine(tomorrow, datetime.min.time(), tzinfo=_BUSINESS_TIMEZONE)
    return int((expiry + timedelta(hours=1)).timestamp())


async def get_daily_quota_status(
    model_config: Mapping[str, Any],
    user_id: int,
) -> ModelDailyQuotaStatus:
    """查询模型配置在当前自然日的已结算用量。

    Args:
        model_config: 包含模型 ID、限额模式和限额值的模型配置。
        user_id: 模型所属用户 ID，用于租户隔离。

    Returns:
        当前日期的用量、剩余量和请求次数实体。
    """
    model_config_id = int(model_config["id"])
    now = business_now()
    usage_date = now.date()
    row = await fetch_one(
        "SELECT input_tokens, output_tokens, total_tokens, request_count "
        "FROM model_daily_token_usage "
        "WHERE model_config_id=%s AND user_id=%s AND usage_date=%s",
        (model_config_id, user_id, usage_date.isoformat()),
    )
    input_tokens = int((row or {}).get("input_tokens") or 0)
    output_tokens = int((row or {}).get("output_tokens") or 0)
    used_tokens = int((row or {}).get("total_tokens") or 0)
    request_count = int((row or {}).get("request_count") or 0)
    mode = _quota_mode(model_config)
    daily_limit_value = model_config.get("daily_token_limit")
    daily_limit = int(daily_limit_value) if daily_limit_value is not None else None
    remaining = None if mode is TokenQuotaMode.UNLIMITED else max(0, (daily_limit or 0) - used_tokens)
    return ModelDailyQuotaStatus(
        model_config_id=model_config_id,
        usage_date=usage_date,
        quota_mode=mode,
        daily_token_limit=daily_limit,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        used_tokens=used_tokens,
        request_count=request_count,
        remaining_tokens=remaining,
    )


async def reserve_model_tokens(
    model_config: Mapping[str, Any],
    user_id: int,
    requested_tokens: int,
) -> TokenReservation:
    """调用模型前检查每日额度并通过 Redis 原子预占。

    Args:
        model_config: 当前调用使用的用户模型配置。
        user_id: 当前用户 ID。
        requested_tokens: 根据完整请求估算出的最大 Token 消耗。

    Returns:
        用于调用结束后结算的预占实体。

    Raises:
        ModelTokenQuotaExceededError: 当日剩余额度不足。
    """
    status = await get_daily_quota_status(model_config, user_id)
    reservation = TokenReservation(
        reservation_id=uuid.uuid4().hex,
        model_config_id=status.model_config_id,
        user_id=user_id,
        usage_date=status.usage_date,
        reserved_tokens=max(1, requested_tokens),
        quota_mode=status.quota_mode,
    )
    if status.quota_mode is TokenQuotaMode.UNLIMITED:
        return reservation

    redis = await get_redis()
    now = business_now()
    key = _usage_key(user_id, status.model_config_id, status.usage_date.isoformat())
    result = await redis.eval(
        _RESERVE_SCRIPT,
        1,
        key,
        status.used_tokens,
        reservation.reserved_tokens,
        int(status.daily_token_limit or 0),
        _expiry_timestamp(now),
    )
    allowed = bool(int(result[0]))
    current = int(result[1])
    if not allowed:
        remaining = max(0, int(status.daily_token_limit or 0) - current)
        rejected_status = ModelDailyQuotaStatus(
            model_config_id=status.model_config_id,
            usage_date=status.usage_date,
            quota_mode=status.quota_mode,
            daily_token_limit=status.daily_token_limit,
            input_tokens=status.input_tokens,
            output_tokens=status.output_tokens,
            used_tokens=current,
            request_count=status.request_count,
            remaining_tokens=remaining,
        )
        raise ModelTokenQuotaExceededError(rejected_status, reservation.reserved_tokens)
    return reservation


async def settle_model_tokens(
    reservation: TokenReservation,
    usage: ModelTokenUsage,
) -> None:
    """持久化真实用量，并将 Redis 预占调整为实际消耗。

    Args:
        reservation: 调用模型之前取得的预占实体。
        usage: 供应商返回或保守估算的一次调用用量。
    """
    now_text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    await execute(
        "INSERT INTO model_daily_token_usage "
        "(model_config_id, user_id, usage_date, input_tokens, output_tokens, "
        "total_tokens, request_count, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s) "
        "ON DUPLICATE KEY UPDATE "
        "input_tokens=input_tokens+VALUES(input_tokens), "
        "output_tokens=output_tokens+VALUES(output_tokens), "
        "total_tokens=total_tokens+VALUES(total_tokens), "
        "request_count=request_count+1, updated_at=VALUES(updated_at)",
        (
            reservation.model_config_id,
            reservation.user_id,
            reservation.usage_date.isoformat(),
            usage.input_tokens,
            usage.output_tokens,
            usage.total_tokens,
            now_text,
            now_text,
        ),
    )
    if reservation.quota_mode is TokenQuotaMode.UNLIMITED:
        return
    redis = await get_redis()
    key = _usage_key(
        reservation.user_id,
        reservation.model_config_id,
        reservation.usage_date.isoformat(),
    )
    await redis.eval(
        _SETTLE_SCRIPT,
        1,
        key,
        usage.total_tokens,
        usage.total_tokens - reservation.reserved_tokens,
        _expiry_timestamp(business_now()),
    )


def estimated_usage(reservation: TokenReservation) -> ModelTokenUsage:
    """供应商没有返回 usage 时按预占总量生成保守用量。"""
    return ModelTokenUsage(
        input_tokens=0,
        output_tokens=0,
        total_tokens=reservation.reserved_tokens,
        estimated=True,
    )
