"""工作流专用 Redis Checkpointer 生命周期管理。"""

import logging

from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.checkpoint.memory import InMemorySaver

from ..config import WORKFLOW_CHECKPOINT_REDIS_URL, WORKFLOW_CHECKPOINT_TTL_MINUTES

log = logging.getLogger(__name__)

_checkpointer_context = None
_workflow_checkpointer = None


async def init_workflow_checkpointer():
    """初始化工作流 Checkpointer，Redis Stack 不可用时安全回退到内存。

    回退只用于保证旧环境仍能运行；日志会明确提示此时不具备跨进程恢复能力。
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
        log.info("工作流 Redis Checkpointer 初始化完成")
    except Exception as exc:
        _checkpointer_context = None
        _workflow_checkpointer = InMemorySaver()
        log.warning(
            "工作流 Redis Checkpointer 初始化失败，已回退到内存模式；"
            "跨进程恢复暂不可用，请确认 Redis Stack 已启用 | error=%s",
            exc,
        )
    return _workflow_checkpointer


def get_workflow_checkpointer():
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
