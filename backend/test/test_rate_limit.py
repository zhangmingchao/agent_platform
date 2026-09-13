"""Redis 分布式限流测试。"""

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from backend.rate_limit import RateLimitRule, check_rate_limit, enforce_rate_limit


class RateLimitTests(unittest.IsolatedAsyncioTestCase):
    """验证固定窗口计数实体和 HTTP 拒绝行为。"""

    async def test_check_rate_limit_returns_entity(self) -> None:
        """未超过阈值时应返回剩余次数和窗口 TTL。"""
        redis = AsyncMock()
        redis.eval.return_value = [2, 42]
        rule = RateLimitRule(name="test", limit=5, window_seconds=60)

        with patch("backend.rate_limit.get_redis", AsyncMock(return_value=redis)):
            decision = await check_rate_limit(rule, "user-1")

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.remaining, 3)
        self.assertEqual(decision.retry_after_seconds, 42)

    async def test_enforce_rate_limit_returns_429_and_retry_after(self) -> None:
        """超过阈值时应返回 429，并告知客户端何时重试。"""
        redis = AsyncMock()
        redis.eval.return_value = [6, 30]
        rule = RateLimitRule(name="test", limit=5, window_seconds=60)

        with patch("backend.rate_limit.get_redis", AsyncMock(return_value=redis)):
            with self.assertRaises(HTTPException) as raised:
                await enforce_rate_limit(rule, "user-1")

        self.assertEqual(raised.exception.status_code, 429)
        self.assertEqual(raised.exception.headers, {"Retry-After": "30"})


if __name__ == "__main__":
    unittest.main()
