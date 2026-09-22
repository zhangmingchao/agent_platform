"""Agent Loop 生命周期事件模型。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class AgentLoopPhase(str, Enum):
    """Agent 执行循环中的稳定生命周期阶段。"""

    TURN_START = "turn/start"
    STEP_START = "step/start"
    LLM_START = "llm/start"
    LLM_END = "llm/end"
    TOOL_START = "tool/start"
    TOOL_END = "tool/end"
    STEP_END = "step/end"
    TURN_END = "turn/end"
    TURN_ERROR = "turn/error"
    TURN_TIMEOUT = "turn/timeout"
    TURN_CANCELLED = "turn/cancelled"


@dataclass(frozen=True)
class AgentLoopEvent:
    """一次 Agent Loop 生命周期事件。

    Attributes:
        phase: 生命周期阶段。
        turn_id: 本轮用户请求对应的稳定标识。
        step_id: 当前步骤标识；turn 级事件可以为空。
        step_no: 当前步骤序号，从 1 开始；turn 级事件可以为空。
        run_id: LangChain/LangGraph 原始事件运行 ID。
        name: 当前模型、工具或节点名称。
        metadata: 额外审计信息，要求可 JSON 序列化。
    """

    phase: AgentLoopPhase
    turn_id: str
    step_id: Optional[str] = None
    step_no: Optional[int] = None
    run_id: Optional[str] = None
    name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_sse_metadata(self) -> Dict[str, Any]:
        """转换为 SSE 元数据，不包含空值字段。"""
        data: Dict[str, Any] = {
            "phase": self.phase.value,
            "turn_id": self.turn_id,
            **self.metadata,
        }
        if self.step_id is not None:
            data["step_id"] = self.step_id
        if self.step_no is not None:
            data["step_no"] = self.step_no
        if self.run_id:
            data["run_id"] = self.run_id
        if self.name:
            data["name"] = self.name
        return data
