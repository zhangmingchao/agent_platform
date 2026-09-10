"""独立 Runtime Worker 任务处理测试。"""

import unittest
from unittest.mock import AsyncMock, patch

from backend.runtime_worker import process_runtime_task


class RuntimeWorkerTests(unittest.IsolatedAsyncioTestCase):
    """验证 Worker 对正常任务和排队取消任务的处理。"""

    async def test_processes_and_publishes_runtime_result(self) -> None:
        """正常任务应交给执行器，并将相同结果发布到 Redis。

        返回值结构：标准 Runtime 结果字典，status 为 completed。
        """
        task = {"executionId": "execution-1"}
        expected = {
            "executionId": "execution-1",
            "status": "completed",
            "exitCode": 0,
            "stdout": "ok",
            "stderr": "",
            "error": "",
            "result": {"ok": True},
            "artifacts": [],
        }
        with (
            patch("backend.runtime_worker.is_runtime_task_cancelled", new=AsyncMock(return_value=False)),
            patch("backend.runtime_worker.execute_runtime_task", new=AsyncMock(return_value=expected)),
            patch("backend.runtime_worker.publish_runtime_result", new=AsyncMock()) as publish,
        ):
            result = await process_runtime_task(task)
        self.assertEqual(result, expected)
        publish.assert_awaited_once_with("execution-1", expected)

    async def test_skips_cancelled_runtime_task(self) -> None:
        """已取消的排队任务不应进入 Python 执行器。

        返回值结构：标准 Runtime 失败字典，error 说明任务已取消。
        """
        task = {"executionId": "execution-2"}
        with (
            patch("backend.runtime_worker.is_runtime_task_cancelled", new=AsyncMock(return_value=True)),
            patch("backend.runtime_worker.execute_runtime_task", new=AsyncMock()) as execute_task,
            patch("backend.runtime_worker.execute", new=AsyncMock()),
            patch("backend.runtime_worker.publish_runtime_result", new=AsyncMock()),
        ):
            result = await process_runtime_task(task)
        self.assertEqual(result["status"], "failed")
        self.assertIn("已取消", result["error"])
        execute_task.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
