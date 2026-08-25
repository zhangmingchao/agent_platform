"""Runtime Worker 使用的 Redis 任务队列与结果通道。"""

import json
import time
from typing import Dict, Optional

from redis.exceptions import TimeoutError as RedisTimeoutError

from ..config import RUNTIME_WORKER_QUEUE_NAME, RUNTIME_WORKER_RESULT_TTL_SECONDS
from ..redis_client import get_redis


def runtime_result_key(execution_id: str) -> str:
    """返回某次执行的 Redis 结果 List Key。

    返回值结构：字符串，格式为 ``runtime:execution:{execution_id}:result``。
    """
    return f"runtime:execution:{execution_id}:result"


def runtime_cancel_key(execution_id: str) -> str:
    """返回某次执行的 Redis 取消标记 Key。

    返回值结构：字符串，格式为 ``runtime:execution:{execution_id}:cancelled``。
    """
    return f"runtime:execution:{execution_id}:cancelled"


async def enqueue_runtime_task(task: Dict) -> int:
    """将准备完成的 Runtime 任务写入 Redis 队列尾部。

    参数 task 的核心结构：
    ``{"executionId": str, "userId": int, "timeoutSeconds": int, "context": dict}``。

    返回值结构：整数，表示任务写入后队列中等待消费的任务数量。
    """
    redis = await get_redis()
    return int(await redis.rpush(
        RUNTIME_WORKER_QUEUE_NAME,
        json.dumps(task, ensure_ascii=False, default=str),
    ))


async def claim_runtime_task(block_seconds: int = 5) -> Optional[Dict]:
    """从 Redis 队列头阻塞领取一个 Runtime 任务。

    返回值结构：有任务时返回任务字典；等待超时且没有任务时返回 ``None``。
    多个 Worker 同时调用时，同一条 List 消息只会被其中一个 Worker 领取。
    """
    redis = await get_redis()
    try:
        item = await redis.blpop(RUNTIME_WORKER_QUEUE_NAME, timeout=max(1, block_seconds))
    except RedisTimeoutError:
        # Redis socket timeout 与 BLPOP 时间接近时可能先抛异常；空队列属于正常状态。
        return None
    if not item:
        return None
    _, payload = item
    return json.loads(payload)


async def publish_runtime_result(execution_id: str, result: Dict) -> int:
    """将 Worker 执行结果写入当前 execution 的 Redis 结果通道。

    参数 result 的结构与 ``execute_runtime_task`` 返回值一致，包含 executionId、
    status、exitCode、stdout、stderr、error、result 和 artifacts。

    返回值结构：整数，表示结果写入后结果 List 中的元素数量。
    """
    redis = await get_redis()
    key = runtime_result_key(execution_id)
    pipeline = redis.pipeline(transaction=True)
    pipeline.rpush(key, json.dumps(result, ensure_ascii=False, default=str))
    pipeline.expire(key, RUNTIME_WORKER_RESULT_TTL_SECONDS)
    values = await pipeline.execute()
    return int(values[0])


async def wait_runtime_result(execution_id: str, timeout_seconds: int) -> Optional[Dict]:
    """等待 Worker 返回指定 execution 的最终结果。

    返回值结构：Worker 已完成时返回结果字典；超过等待时间时返回 ``None``。
    使用 Redis BLPOP 等待，不会在 FastAPI 中循环轮询数据库。
    """
    redis = await get_redis()
    deadline = time.monotonic() + max(1, timeout_seconds)
    key = runtime_result_key(execution_id)

    # 使用短周期 BLPOP，避免 Redis 客户端 socket_timeout 小于整个任务等待时间时
    # 把正常等待误判成连接故障。
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            item = await redis.blpop(key, timeout=max(1, min(5, int(remaining))))
        except RedisTimeoutError:
            continue
        if not item:
            continue
        _, payload = item
        return json.loads(payload)


async def cancel_runtime_task(execution_id: str, ttl_seconds: int) -> bool:
    """写入任务取消标记，避免长时间排队的任务之后仍被 Worker 执行。

    返回值结构：布尔值；Redis 成功写入取消标记时返回 ``True``。
    该标记只能阻止尚未开始的任务，不能直接终止 Worker 中已经启动的子进程。
    """
    redis = await get_redis()
    saved = await redis.set(
        runtime_cancel_key(execution_id),
        "1",
        ex=max(1, ttl_seconds),
    )
    return bool(saved)


async def is_runtime_task_cancelled(execution_id: str) -> bool:
    """检查某次 Runtime 任务是否已经被调用方标记为取消。

    返回值结构：布尔值；存在取消标记时返回 ``True``，否则返回 ``False``。
    """
    redis = await get_redis()
    return bool(await redis.exists(runtime_cancel_key(execution_id)))
