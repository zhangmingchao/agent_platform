"""Agent 整体执行时间控制测试。"""

import asyncio
import unittest
from collections.abc import AsyncGenerator

from backend.core.execution_control import (
    AgentExecutionTimeoutError,
    stream_with_total_timeout,
)


class AgentExecutionControlTests(unittest.IsolatedAsyncioTestCase):
    """验证 Agent 共享截止时间和异常边界。"""

    async def test_stream_uses_one_total_deadline(self) -> None:
        """连续事件的累计耗时达到上限后应抛出 Agent 专用超时异常。"""

        async def slow_events() -> AsyncGenerator[int, None]:
            """产生一个事件后继续阻塞，用于验证期限不会按事件重置。"""
            yield 1
            await asyncio.sleep(2)
            yield 2

        received = []
        with self.assertRaises(AgentExecutionTimeoutError) as raised:
            async for event in stream_with_total_timeout(slow_events(), 1):
                received.append(event)

        self.assertEqual(received, [1])
        self.assertEqual(raised.exception.timeout_seconds, 1)

    async def test_upstream_timeout_before_deadline_is_preserved(self) -> None:
        """工具等上游组件主动抛出的 TimeoutError 不应被误报为 Agent 总超时。"""

        async def failed_events() -> AsyncGenerator[int, None]:
            """立即抛出上游自己的超时错误。"""
            raise TimeoutError("tool timeout")
            if False:
                yield 1

        with self.assertRaisesRegex(TimeoutError, "tool timeout"):
            async for _event in stream_with_total_timeout(failed_events(), 10):
                pass


if __name__ == "__main__":
    unittest.main()
