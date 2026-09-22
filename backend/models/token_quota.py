"""模型每日 Token 限额使用的强类型实体。"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class TokenQuotaMode(str, Enum):
    """模型 Token 限额模式。

    ``UNLIMITED`` 表示只统计、不拦截；``DAILY`` 表示按上海时区自然日限制。
    """

    UNLIMITED = "unlimited"
    DAILY = "daily"


@dataclass(frozen=True)
class ModelTokenUsage:
    """一次模型调用产生的 Token 用量。

    Attributes:
        input_tokens: 本次请求输入模型的 Token 数。
        output_tokens: 本次模型生成的 Token 数。
        total_tokens: 本次调用总 Token 数。
        estimated: 是否因为供应商未返回 usage 而使用预占值估算。
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated: bool = False


@dataclass(frozen=True)
class TokenEstimate:
    """模型调用前的 Token 消耗估算结果。"""

    message_tokens: int
    tool_schema_tokens: int
    protocol_overhead_tokens: int
    estimated_input_tokens: int
    max_output_tokens: int
    reserved_total_tokens: int
    estimator_name: str
    safety_factor: float


@dataclass(frozen=True)
class TokenReservation:
    """一次模型调用已经占用的当日 Token 额度。"""

    reservation_id: str
    model_config_id: int
    user_id: int
    usage_date: date
    reserved_tokens: int
    quota_mode: TokenQuotaMode


@dataclass(frozen=True)
class ModelDailyQuotaStatus:
    """模型当日 Token 用量与剩余额度状态。"""

    model_config_id: int
    usage_date: date
    quota_mode: TokenQuotaMode
    daily_token_limit: Optional[int]
    input_tokens: int
    output_tokens: int
    used_tokens: int
    request_count: int
    remaining_tokens: Optional[int]

    def to_dict(self) -> dict:
        """转换为可直接返回给 API 的 JSON 兼容结构。"""
        return {
            "model_config_id": self.model_config_id,
            "usage_date": self.usage_date.isoformat(),
            "quota_mode": self.quota_mode.value,
            "daily_token_limit": self.daily_token_limit,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "used_tokens": self.used_tokens,
            "request_count": self.request_count,
            "remaining_tokens": self.remaining_tokens,
        }


class ModelTokenQuotaExceededError(RuntimeError):
    """模型当日剩余额度无法覆盖下一次模型调用。"""

    def __init__(self, status: ModelDailyQuotaStatus, requested_tokens: int) -> None:
        """创建额度不足异常。

        Args:
            status: 拒绝调用时的当日额度状态。
            requested_tokens: 本轮准备预占的 Token 数。
        """
        self.status = status
        self.requested_tokens = requested_tokens
        super().__init__(
            "模型今日 Token 额度不足："
            f"剩余 {status.remaining_tokens or 0}，本轮预计最多需要 {requested_tokens}"
        )
