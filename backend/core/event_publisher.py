"""基于 Redis Stream 的工作流事件发布器。

每次工作流运行使用独立的 Stream，执行器只负责发布事件，SSE 接口负责读取事件，
从而让 Agent 的执行生命周期与浏览器连接生命周期相互独立。
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..config import WORKFLOW_EVENT_STREAM_MAXLEN, WORKFLOW_EVENT_STREAM_TTL_SECONDS
from ..redis_client import get_redis


def workflow_event_stream_key(run_id: int) -> str:
    """返回指定工作流运行对应的 Redis Stream Key。"""
    return f"agent:run:{run_id}:events"


class RedisStreamEventPublisher:
    """按顺序发布某一次工作流运行产生的事件。

    Redis 自动生成的 Stream Entry ID 就是对外使用的事件 ID。工作流存在并行分支时，
    多个协程可能同时发布事件，因此使用异步锁保证 sequence 与 XADD 顺序一致。
    """

    def __init__(self, run_id: int):
        self.run_id = run_id
        self._sequence = 0
        self._lock = asyncio.Lock()

    async def publish(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        *,
        node_id: Optional[str] = None,
    ) -> str:
        """写入一条事件并返回 Redis Stream 自动生成的事件 ID。

        type/runId/nodeId/sequence 作为可检索的固定字段保存，具体业务内容统一放在
        payload 中，便于后续扩展事件结构而不频繁修改 Stream Schema。
        """
        payload = data or {}
        async with self._lock:
            # sequence 是一次 run 内的业务顺序号；Stream ID 则用于传输和读取定位。
            self._sequence += 1
            redis = await get_redis()

            # XADD 与 EXPIRE 放入同一个事务管道，避免新增事件后忘记刷新过期时间。
            pipeline = redis.pipeline(transaction=True)
            pipeline.xadd(
                workflow_event_stream_key(self.run_id),
                {
                    "type": event_type,
                    "runId": str(self.run_id),
                    "nodeId": node_id or "",
                    "sequence": str(self._sequence),
                    "payload": json.dumps(payload, ensure_ascii=False, default=str),
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                },
                maxlen=WORKFLOW_EVENT_STREAM_MAXLEN,
                # 使用近似裁剪，避免 Redis 为严格长度付出额外维护成本。
                approximate=True,
            )
            pipeline.expire(
                workflow_event_stream_key(self.run_id),
                WORKFLOW_EVENT_STREAM_TTL_SECONDS,
            )
            results = await pipeline.execute()
            return str(results[0])
