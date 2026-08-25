"""独立 Runtime Worker 进程入口。

本进程从 Redis List 领取 Runtime 任务，并调用本地受限子进程执行器。它与 FastAPI
分开启动，因此代码执行产生的 CPU、内存和子进程生命周期不再由 API 进程直接管理。
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

from .database import close_pool, execute, init_db
from .redis_client import close_redis, get_redis
from .runtime.queue import (
    claim_runtime_task,
    is_runtime_task_cancelled,
    publish_runtime_result,
)
from .services.runtime_service import execute_runtime_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("runtime-worker")


def _now() -> str:
    """返回可写入 MySQL DATETIME 字段的 UTC 时间字符串。

    返回值结构：``YYYY-MM-DD HH:MM:SS`` 格式的字符串。
    """
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _failed_result(execution_id: str, error: str) -> Dict:
    """构造 Worker 调度层异常对应的标准失败结果。

    返回值结构：包含 executionId、status、exitCode、stdout、stderr、error、
    result 和 artifacts 的字典；其中 status 固定为 failed。
    """
    return {
        "executionId": execution_id,
        "status": "failed",
        "exitCode": None,
        "stdout": "",
        "stderr": "",
        "error": error,
        "result": None,
        "artifacts": [],
    }


async def process_runtime_task(task: Dict) -> Dict:
    """处理一条已从 Redis 领取的任务并发布最终结果。

    如果任务在排队期间被 API 标记为取消，则不会启动 Python 子进程。执行过程中出现
    未被执行服务处理的异常时，本方法负责补写数据库失败状态。

    返回值结构：标准 Runtime 结果字典，包含 executionId、status、exitCode、
    stdout、stderr、error、result 和 artifacts。
    """
    execution_id = str(task.get("executionId") or "")
    if not execution_id:
        raise ValueError("Runtime 队列任务缺少 executionId")

    if await is_runtime_task_cancelled(execution_id):
        result = _failed_result(execution_id, "Runtime 任务在开始执行前已取消")
        await execute(
            "UPDATE code_executions SET status=%s, error_text=%s, finished_at=%s WHERE id=%s",
            ("failed", result["error"], _now(), execution_id),
        )
        await publish_runtime_result(execution_id, result)
        return result

    try:
        result = await execute_runtime_task(task)
    except Exception as exc:
        log.exception("[Execution#%s] Runtime Worker 执行失败", execution_id)
        result = _failed_result(execution_id, str(exc))
        await execute(
            "UPDATE code_executions SET status=%s, error_text=%s, finished_at=%s WHERE id=%s",
            ("failed", str(exc)[:5000], _now(), execution_id),
        )

    await publish_runtime_result(execution_id, result)
    return result


async def run_runtime_worker() -> None:
    """持续消费 Redis Runtime 队列，直到进程被停止。

    返回值结构：正常运行时不会返回；收到任务取消或进程取消信号时返回 ``None``。
    每个 Worker 进程一次执行一个任务，可启动多个 Worker 进程提高并发度。
    """
    # Worker 可以先于 API 启动，因此自行确保数据库及 Runtime 表已经初始化。
    await init_db()
    redis = await get_redis()
    await redis.ping()
    log.info("Runtime Worker 已启动，等待 Redis 队列任务")

    try:
        while True:
            task = await claim_runtime_task(block_seconds=5)
            if task is None:
                continue
            execution_id = task.get("executionId", "unknown")
            log.info("[Execution#%s] 已领取 Runtime 任务", execution_id)
            result = await process_runtime_task(task)
            log.info("[Execution#%s] 执行结束，status=%s", execution_id, result["status"])
    except asyncio.CancelledError:
        log.info("Runtime Worker 收到停止信号")
    finally:
        await close_redis()
        await close_pool()


def main() -> None:
    """启动 Runtime Worker 的 asyncio 事件循环。

    返回值结构：无返回值；Worker 退出时返回 ``None``。
    """
    try:
        asyncio.run(run_runtime_worker())
    except KeyboardInterrupt:
        log.info("Runtime Worker 已停止")


if __name__ == "__main__":
    main()
