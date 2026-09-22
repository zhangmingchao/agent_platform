"""Session append-only 事件日志模型。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class SessionEventSource(str, Enum):
    """事件来源模块。"""

    AGENT_LOOP = "agent_loop"
    TOOL_PIPELINE = "tool_pipeline"
    PERMISSION = "permission"
    SYSTEM = "system"


class SessionEventType(str, Enum):
    """Session 事件类型。"""

    USER_INPUT = "user_input"
    AGENT_LOOP = "agent_loop"
    TOOL_STAGE = "tool_stage"
    PERMISSION_DECISION = "permission_decision"
    ERROR = "error"


@dataclass(frozen=True)
class SessionEventRecord:
    """一条不可变 Session 事件。

    Attributes:
        user_id: 事件所属平台用户 ID。
        event_source: 事件来源模块，例如 agent_loop 或 tool_pipeline。
        event_type: 事件类型，例如 agent_loop、tool_stage、permission_decision。
        session_id: 平台聊天会话 ID；外部 API 或工作流可以为空。
        trace_run_id: Trace Run ID，用于把事件和 Trace 关联。
        agent_id: 执行事件所属 Agent ID。
        workflow_run_id: 工作流运行 ID。
        workflow_step_id: 工作流步骤 ID。
        turn_id: 本轮 Agent 执行 ID。
        step_id: 当前 Agent 步骤 ID。
        run_id: LangChain/LangGraph 原始 run ID 或工具阶段运行 ID。
        phase: 生命周期阶段或 pipeline 阶段。
        name: 模型、工具、节点或阶段名称。
        status: 事件状态，例如 started、success、rejected、error。
        payload: 事件附加数据，只保存摘要和可审计信息。
    """

    user_id: int
    event_source: SessionEventSource
    event_type: SessionEventType
    session_id: Optional[int] = None
    trace_run_id: Optional[int] = None
    agent_id: Optional[int] = None
    workflow_run_id: Optional[int] = None
    workflow_step_id: Optional[int] = None
    turn_id: str = ""
    step_id: str = ""
    run_id: str = ""
    phase: str = ""
    name: str = ""
    status: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
