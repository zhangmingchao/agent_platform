"""在每次 LangChain 模型调用前后执行额度预占和结算。"""

import logging
from typing import Any, Dict, Mapping, Optional, Sequence
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage

from ..models.token_quota import TokenReservation
from ..services.token_quota_service import (
    estimated_usage,
    reserve_model_tokens,
    settle_model_tokens,
)
from .token_usage import estimate_model_tokens, extract_token_usage

log = logging.getLogger(__name__)


class ModelTokenQuotaCallback(AsyncCallbackHandler):
    """为一条用户模型配置执行逐轮每日 Token 限额控制。

    每个 Callback 实例只服务于一个 Agent 执行器；使用 ``run_id`` 关联并发或连续的
    LLM 轮次。设置 ``raise_error`` 后，额度不足会直接终止本次模型调用。
    """

    raise_error = True

    def __init__(
        self,
        model_config: Mapping[str, Any],
        user_id: int,
        tool_schemas: Sequence[Dict[str, Any]],
    ) -> None:
        """创建模型额度 Callback。

        Args:
            model_config: 当前 Agent 使用的用户模型配置。
            user_id: 当前调用所属用户 ID。
            tool_schemas: 本轮 Agent 可能提交给模型的工具 Schema。
        """
        self.model_config = dict(model_config)
        self.user_id = user_id
        self.tool_schemas = list(tool_schemas)
        self.max_output_tokens = max(1, int(model_config.get("max_tokens") or 4096))
        self.reservations: Dict[str, TokenReservation] = {}

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """在每轮聊天模型调用开始前估算请求并原子预占额度。"""
        del serialized, parent_run_id, kwargs
        current_messages = messages[0] if messages else []
        estimate = estimate_model_tokens(
            current_messages,
            self.tool_schemas,
            self.max_output_tokens,
        )
        reservation = await reserve_model_tokens(
            self.model_config,
            self.user_id,
            estimate.reserved_total_tokens,
        )
        self.reservations[str(run_id)] = reservation

    async def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """模型完成后读取供应商 usage，并按真实用量结算。"""
        del parent_run_id, kwargs
        reservation = self.reservations.pop(str(run_id), None)
        if reservation is None:
            return
        usage = extract_token_usage(response)
        if usage.total_tokens <= 0:
            usage = estimated_usage(reservation)
            log.warning(
                "[TokenQuota] provider usage missing; charged reservation model_config_id=%s tokens=%s",
                reservation.model_config_id,
                reservation.reserved_tokens,
            )
        await settle_model_tokens(reservation, usage)

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """模型失败且无法取得 usage 时，按预占量保守结算。"""
        del error, parent_run_id, kwargs
        reservation = self.reservations.pop(str(run_id), None)
        if reservation is not None:
            await settle_model_tokens(reservation, estimated_usage(reservation))
