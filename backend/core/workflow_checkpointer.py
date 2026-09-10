"""工作流专用 Redis Checkpointer 生命周期管理。"""

import logging
from contextlib import AbstractAsyncContextManager
from typing import Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from ..config import WORKFLOW_CHECKPOINT_REDIS_URL, WORKFLOW_CHECKPOINT_TTL_MINUTES

log = logging.getLogger(__name__)

_checkpointer_context: Optional[AbstractAsyncContextManager[AsyncRedisSaver]] = None
_workflow_checkpointer: Optional[BaseCheckpointSaver[str]] = None


async def init_workflow_checkpointer() -> BaseCheckpointSaver[str]:
    """初始化工作流 Redis Checkpointer。

    Redis Stack、RediSearch 或 RedisJSON 不可用时直接抛出异常，使应用启动失败。
    任何环境都不允许回退到内存模式，避免人工审批产生不可恢复的运行状态。
    """
    global _checkpointer_context, _workflow_checkpointer
    if _workflow_checkpointer is not None:
        return _workflow_checkpointer

    _checkpointer_context = AsyncRedisSaver.from_conn_string(
        WORKFLOW_CHECKPOINT_REDIS_URL,
        ttl={
            "default_ttl": WORKFLOW_CHECKPOINT_TTL_MINUTES,
            "refresh_on_read": True,
        },
        checkpoint_prefix="agent_platform:workflow:checkpoint",
        checkpoint_write_prefix="agent_platform:workflow:checkpoint_write",
    )
    try:
        _workflow_checkpointer = await _checkpointer_context.__aenter__()
    except Exception:
        # 初始化失败的上下文不能继续复用；保留原始异常供启动日志定位。
        _checkpointer_context = None
        _workflow_checkpointer = None
        log.exception(
            "工作流 Redis Checkpointer 初始化失败，应用拒绝启动；"
            "请确认 Redis Stack、RediSearch 与 RedisJSON 可用"
        )
        raise
    log.info("工作流 Redis Checkpointer 初始化完成")
    return _workflow_checkpointer


def get_workflow_checkpointer() -> BaseCheckpointSaver[str]:
    """返回已经初始化的工作流 Checkpointer。"""
    if _workflow_checkpointer is None:
        raise RuntimeError("工作流 Redis Checkpointer 尚未初始化")
    return _workflow_checkpointer


async def close_workflow_checkpointer() -> None:
    """关闭 Checkpointer 自己持有的 Redis 连接。"""
    global _checkpointer_context, _workflow_checkpointer
    if _checkpointer_context is not None:
        await _checkpointer_context.__aexit__(None, None, None)
    _checkpointer_context = None
    _workflow_checkpointer = None
    log.info("工作流 Redis Checkpointer 已关闭")
