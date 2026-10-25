"""Python Runtime 使用的数据模型。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from ..models.permission import PermissionPreset

if TYPE_CHECKING:
    from ..core.trace_handler import TraceContext


@dataclass(frozen=True)
class RuntimeContext:
    """绑定一次工具执行所属的用户、会话或工作流上下文。

    Attributes:
        user_id: 工具调用所属用户 ID。
        workspace_id: 用户容器内工作目录标识。
        session_id: 平台聊天会话 ID，外部 API 或工作流场景可以为空。
        workflow_run_id: 工作流运行 ID。
        workflow_step_id: 工作流步骤 ID。
        node_id: 当前执行节点标识。
        agent_id: 工具调用所属 Agent ID，用于权限审计。
        permission_preset: 本次运行采用的权限预设。
        invocation_source: 调用来源，例如 platform、api 或 workflow。
        trace_ctx: 当前 Trace 上下文，仅进程内工具执行使用，不写入 Runtime 队列。
    """

    user_id: int
    # workspace_id 只区分同一用户容器内的工作目录，不用于创建独立容器。
    workspace_id: Optional[str] = None
    session_id: Optional[int] = None
    workflow_run_id: Optional[int] = None
    workflow_step_id: Optional[int] = None
    node_id: Optional[str] = None
    agent_id: Optional[int] = None
    permission_preset: PermissionPreset = PermissionPreset.STANDARD
    invocation_source: str = "platform"
    trace_ctx: Optional["TraceContext"] = None
    # 0 为顶层 Agent，1 为子任务；服务端禁止子任务继续委托。
    delegation_depth: int = 0
