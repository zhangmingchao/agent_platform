"""Runtime Worker Redis 队列测试。"""

import json
import unittest
from unittest.mock import AsyncMock, patch

from redis.exceptions import TimeoutError as RedisTimeoutError

from backend.runtime.queue import (
    claim_runtime_task,
    enqueue_runtime_task,
    runtime_cancel_key,
    runtime_result_key,
    wait_runtime_result,
)


class RuntimeQueueTests(unittest.IsolatedAsyncioTestCase):
    """验证 Runtime 任务和结果在 Redis 边界处的序列化结构。"""

    def test_builds_execution_scoped_keys(self):
        """结果和取消 Key 必须按 execution ID 隔离。

        返回值结构：两个字符串 Key，均包含传入的 execution ID。
        """
        self.assertEqual(
            runtime_result_key("execution-1"),
            "runtime:execution:execution-1:result",
        )
        self.assertEqual(
            runtime_cancel_key("execution-1"),
            "runtime:execution:execution-1:cancelled",
        )

    async def test_enqueues_json_task(self):
        """任务入队时应编码为 JSON，并返回当前队列长度。

        返回值结构：整数，本测试模拟 Redis 返回队列长度 3。
        """
        redis = AsyncMock()
        redis.rpush.return_value = 3
        task = {"executionId": "execution-1", "userId": 1}
        with patch("backend.runtime.queue.get_redis", return_value=redis):
            queue_size = await enqueue_runtime_task(task)
        self.assertEqual(queue_size, 3)
        payload = redis.rpush.await_args.args[1]
        self.assertEqual(json.loads(payload), task)

    async def test_claims_task_or_returns_none(self):
        """Worker 应将 Redis List 消息解析为字典，无消息时返回 None。

        返回值结构：第一次为任务字典，第二次为 ``None``。
        """
        redis = AsyncMock()
        redis.blpop.side_effect = [
            ("runtime:execution:queue", '{"executionId":"execution-1"}'),
            None,
        ]
        with patch("backend.runtime.queue.get_redis", return_value=redis):
            task = await claim_runtime_task()
            empty = await claim_runtime_task()
        self.assertEqual(task, {"executionId": "execution-1"})
        self.assertIsNone(empty)

    async def test_claim_treats_redis_socket_timeout_as_empty_queue(self):
        """Redis 阻塞读取超时不应导致 Worker 退出。

        返回值结构：``None``，表示本轮没有领取到任务。
        """
        redis = AsyncMock()
        redis.blpop.side_effect = RedisTimeoutError("socket timeout")
        with patch("backend.runtime.queue.get_redis", return_value=redis):
            task = await claim_runtime_task()
        self.assertIsNone(task)

    async def test_waits_for_json_result(self):
        """API 应将 Worker 写入的结果 JSON 解析为字典。

        返回值结构：包含 executionId 和 status 的 Runtime 结果字典。
        """
        redis = AsyncMock()
        redis.blpop.return_value = (
            "runtime:execution:execution-1:result",
            '{"executionId":"execution-1","status":"completed"}',
        )
        with patch("backend.runtime.queue.get_redis", return_value=redis):
            result = await wait_runtime_result("execution-1", 10)
        self.assertEqual(result["status"], "completed")


if __name__ == "__main__":
    unittest.main()
