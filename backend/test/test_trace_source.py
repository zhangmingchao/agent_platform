"""Trace 调用来源测试。"""

import unittest
from unittest.mock import AsyncMock, patch

from backend.core.trace_handler import TraceContext
from backend.models.api_access import InvocationSource


class TraceSourceTests(unittest.IsolatedAsyncioTestCase):
    """验证 platform、api 和 workflow 来源会写入 Trace Run。"""

    async def test_api_source_is_written_when_trace_starts(self) -> None:
        """外部聊天 Trace 的 INSERT 参数必须包含 api 来源。"""
        execute = AsyncMock(return_value=99)
        context = TraceContext(
            session_id=None,
            user_id=7,
            agent_id=8,
            invocation_source=InvocationSource.API,
            request_id="request-123",
        )

        with patch("backend.core.trace_handler.execute", execute):
            trace_id = await context.start("你好")

        self.assertEqual(trace_id, 99)
        self.assertEqual(execute.await_args.args[1][3], "api")
        self.assertEqual(execute.await_args.args[1][4], "request-123")
        self.assertIn("request_id", execute.await_args.args[0])

    async def test_cancelled_and_timeout_use_distinct_trace_statuses(self) -> None:
        """用户取消和系统超时必须保存成不同的 Trace 状态。"""
        execute = AsyncMock()
        context = TraceContext(session_id=1, user_id=7, agent_id=8)
        context.run_id = 99

        with patch("backend.core.trace_handler.execute", execute):
            await context.cancelled("client disconnected")
            await context.timeout("Agent 执行超过 120 秒")

        statuses = [call.args[1][0] for call in execute.await_args_list]
        self.assertEqual(statuses, ["cancelled", "timeout"])


if __name__ == "__main__":
    unittest.main()
