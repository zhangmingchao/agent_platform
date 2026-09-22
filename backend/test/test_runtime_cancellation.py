"""Agent 取消时 Python Runtime 排队任务的补偿测试。"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from backend.runtime.models import RuntimeContext
from backend.services.runtime_service import execute_python_code


class RuntimeCancellationTests(unittest.IsolatedAsyncioTestCase):
    """验证 Agent 终止后不会遗留尚未执行的 Runtime 任务。"""

    async def test_cancelled_wait_marks_queued_task_cancelled(self) -> None:
        """等待结果时被取消应写 Redis 标记并更新 queued 数据库记录。"""
        task = {
            "executionId": "execution-1",
            "timeoutSeconds": 30,
        }
        cancel_task = AsyncMock(return_value=True)
        execute = AsyncMock(return_value=0)
        with (
            patch(
                "backend.services.runtime_service.prepare_runtime_execution",
                AsyncMock(return_value=task),
            ),
            patch(
                "backend.services.runtime_service.enqueue_runtime_task",
                AsyncMock(),
            ),
            patch(
                "backend.services.runtime_service.wait_runtime_result",
                AsyncMock(side_effect=asyncio.CancelledError),
            ),
            patch(
                "backend.services.runtime_service.cancel_runtime_task",
                cancel_task,
            ),
            patch("backend.services.runtime_service.execute", execute),
        ):
            with self.assertRaises(asyncio.CancelledError):
                await execute_python_code(
                    RuntimeContext(user_id=7, workspace_id="chat-1"),
                    "result = {'ok': True}",
                )

        cancel_task.assert_awaited_once()
        self.assertEqual(execute.await_args.args[1][0], "cancelled")
        self.assertEqual(execute.await_args.args[1][3], "execution-1")


if __name__ == "__main__":
    unittest.main()
