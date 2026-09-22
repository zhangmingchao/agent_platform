"""模型每日 Token 限额与用量提取测试。"""

import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from backend.core.token_usage import estimate_model_tokens, extract_token_usage
from backend.models.token_quota import (
    ModelTokenQuotaExceededError,
    ModelTokenUsage,
    TokenQuotaMode,
    TokenReservation,
)
from backend.services.token_quota_service import reserve_model_tokens, settle_model_tokens


class TokenUsageTests(unittest.TestCase):
    """验证调用前估算和调用后 usage 标准化。"""

    def test_estimate_includes_messages_tools_and_output_budget(self) -> None:
        """预占总量应包含完整消息、工具 Schema、协议开销和最大输出。"""
        estimate = estimate_model_tokens(
            [HumanMessage(content="查询订单 10001")],
            [{"type": "function", "function": {"name": "query_order"}}],
            max_output_tokens=100,
        )

        self.assertGreater(estimate.message_tokens, 0)
        self.assertGreater(estimate.tool_schema_tokens, 0)
        self.assertEqual(
            estimate.reserved_total_tokens,
            estimate.estimated_input_tokens + 100,
        )

    def test_extracts_usage_from_ai_message(self) -> None:
        """应将 AIMessage 的 usage_metadata 转换为用量实体。"""
        message = AIMessage(
            content="完成",
            usage_metadata={"input_tokens": 12, "output_tokens": 3, "total_tokens": 15},
        )

        usage = extract_token_usage(message)

        self.assertEqual(usage, ModelTokenUsage(12, 3, 15))

    def test_extracts_usage_from_llm_result(self) -> None:
        """Callback 的 LLMResult 应从 generation.message 中提取 usage。"""
        message = AIMessage(
            content="完成",
            usage_metadata={"input_tokens": 20, "output_tokens": 5, "total_tokens": 25},
        )
        result = SimpleNamespace(
            generations=[[SimpleNamespace(message=message)]],
            llm_output=None,
        )

        self.assertEqual(extract_token_usage(result).total_tokens, 25)


class TokenQuotaServiceTests(unittest.IsolatedAsyncioTestCase):
    """验证每日额度的 Redis 原子预占和 MySQL 结算。"""

    model_config = {
        "id": 8,
        "quota_mode": "daily",
        "daily_token_limit": 1000,
    }

    async def test_daily_quota_reservation_succeeds(self) -> None:
        """Redis返回允许时应生成每日模式预占实体。"""
        redis = AsyncMock()
        redis.eval.return_value = [1, 700]
        with (
            patch(
                "backend.services.token_quota_service.fetch_one",
                AsyncMock(return_value={"total_tokens": 400}),
            ),
            patch(
                "backend.services.token_quota_service.get_redis",
                AsyncMock(return_value=redis),
            ),
        ):
            reservation = await reserve_model_tokens(self.model_config, 3, 300)

        self.assertEqual(reservation.quota_mode, TokenQuotaMode.DAILY)
        self.assertEqual(reservation.reserved_tokens, 300)
        redis.eval.assert_awaited_once()

    async def test_daily_quota_reservation_rejects_when_remaining_is_insufficient(self) -> None:
        """Redis原子判断额度不足时应抛出可识别的业务异常。"""
        redis = AsyncMock()
        redis.eval.return_value = [0, 900]
        with (
            patch(
                "backend.services.token_quota_service.fetch_one",
                AsyncMock(return_value={"total_tokens": 900}),
            ),
            patch(
                "backend.services.token_quota_service.get_redis",
                AsyncMock(return_value=redis),
            ),
        ):
            with self.assertRaises(ModelTokenQuotaExceededError) as raised:
                await reserve_model_tokens(self.model_config, 3, 200)

        self.assertEqual(raised.exception.status.remaining_tokens, 100)
        self.assertEqual(raised.exception.requested_tokens, 200)

    async def test_unlimited_mode_skips_redis_but_still_returns_reservation(self) -> None:
        """不限额模型不应访问 Redis，但仍需产生后续记账所需的预占实体。"""
        config = {"id": 9, "quota_mode": "unlimited", "daily_token_limit": None}
        get_redis_mock = AsyncMock()
        with (
            patch(
                "backend.services.token_quota_service.fetch_one",
                AsyncMock(return_value=None),
            ),
            patch("backend.services.token_quota_service.get_redis", get_redis_mock),
        ):
            reservation = await reserve_model_tokens(config, 3, 250)

        self.assertEqual(reservation.quota_mode, TokenQuotaMode.UNLIMITED)
        get_redis_mock.assert_not_awaited()

    async def test_settlement_persists_usage_and_releases_unused_reservation(self) -> None:
        """真实用量小于预占量时应写入数据库并从 Redis 扣回差额。"""
        reservation = TokenReservation(
            reservation_id="reservation-1",
            model_config_id=8,
            user_id=3,
            usage_date=date(2026, 9, 18),
            reserved_tokens=500,
            quota_mode=TokenQuotaMode.DAILY,
        )
        execute_mock = AsyncMock(return_value=1)
        redis = AsyncMock()
        redis.eval.return_value = 700
        with (
            patch("backend.services.token_quota_service.execute", execute_mock),
            patch(
                "backend.services.token_quota_service.get_redis",
                AsyncMock(return_value=redis),
            ),
        ):
            await settle_model_tokens(reservation, ModelTokenUsage(150, 50, 200))

        execute_mock.assert_awaited_once()
        redis_arguments = redis.eval.await_args.args
        self.assertIn(-300, redis_arguments)


if __name__ == "__main__":
    unittest.main()
