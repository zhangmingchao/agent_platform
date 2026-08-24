"""Python Runtime 使用的数据模型。"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RuntimeContext:
    """绑定一次工具执行所属的用户、会话或工作流上下文。"""

    user_id: int
    session_id: Optional[int] = None
    workflow_run_id: Optional[int] = None
    workflow_step_id: Optional[int] = None
    node_id: Optional[str] = None
