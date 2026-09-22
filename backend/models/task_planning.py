"""显式任务规划使用的领域实体和模型输出 Schema。"""

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, List, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field


class PlanningMode(str, Enum):
    """Agent 任务规划模式。"""

    DISABLED = "disabled"
    EXPLICIT = "explicit"


class TaskPlanStatus(str, Enum):
    """一次显式任务计划的执行状态。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPlanStepStatus(str, Enum):
    """计划中单个步骤的执行状态。"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlannedStepDraft(BaseModel):
    """规划模型生成的单个步骤 Schema。

    Attributes:
        title: 面向用户展示的简短步骤名称。
        instruction: 交给 ReAct Agent 执行的完整步骤指令。
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=100)
    instruction: str = Field(min_length=1, max_length=2000)


class GeneratedTaskPlan(BaseModel):
    """规划模型必须返回的结构化计划 Schema。

    Attributes:
        goal: 对本轮用户目标的准确概括。
        steps: 按执行顺序排列的有限步骤列表。
    """

    model_config = ConfigDict(extra="forbid")

    goal: str = Field(min_length=1, max_length=500)
    steps: List[PlannedStepDraft] = Field(min_length=1, max_length=6)


@dataclass(frozen=True)
class TaskPlanStep:
    """一次任务计划中的可执行步骤。

    Attributes:
        step_key: 本次计划内稳定的步骤标识，例如 ``step-1``。
        order: 从 1 开始的执行顺序。
        title: 面向用户展示的步骤名称。
        instruction: 交给执行 Agent 的具体指令。
        status: 当前执行状态。
        result_summary: 步骤完成后的文本结果。
        error_text: 步骤失败时的错误信息。
        id: 数据库步骤主键；尚未持久化时为空。
    """

    step_key: str
    order: int
    title: str
    instruction: str
    status: TaskPlanStepStatus = TaskPlanStepStatus.PENDING
    result_summary: str = ""
    error_text: str = ""
    id: Optional[int] = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TaskPlanStep":
        """从数据库记录或 LangGraph State 构造步骤实体。"""
        return cls(
            id=int(value["id"]) if value.get("id") is not None else None,
            step_key=str(value.get("step_key") or ""),
            order=int(value.get("step_order") or value.get("order") or 0),
            title=str(value.get("title") or ""),
            instruction=str(value.get("instruction") or ""),
            status=TaskPlanStepStatus(str(value.get("status") or "pending")),
            result_summary=str(value.get("result_summary") or ""),
            error_text=str(value.get("error_text") or ""),
        )

    def with_status(
        self,
        status: TaskPlanStepStatus,
        *,
        result_summary: str = "",
        error_text: str = "",
    ) -> "TaskPlanStep":
        """返回更新执行状态后的新步骤实体。"""
        return replace(
            self,
            status=status,
            result_summary=result_summary or self.result_summary,
            error_text=error_text or self.error_text,
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为数据库、State 和 SSE 可复用的 JSON 结构。"""
        return {
            "id": self.id,
            "step_key": self.step_key,
            "order": self.order,
            "title": self.title,
            "instruction": self.instruction,
            "status": self.status.value,
            "result_summary": self.result_summary,
            "error_text": self.error_text,
        }


@dataclass(frozen=True)
class TaskPlan:
    """一次 Agent 请求生成并执行的显式任务计划。

    Attributes:
        goal: 本轮需要完成的总目标。
        steps: 按顺序执行的步骤实体列表。
        status: 整体计划状态。
        current_step_order: 当前或最近执行到的步骤序号。
        id: 数据库计划主键；尚未持久化时为空。
        trace_run_id: 关联的 Trace 运行主键。
    """

    goal: str
    steps: List[TaskPlanStep]
    status: TaskPlanStatus = TaskPlanStatus.PENDING
    current_step_order: int = 0
    id: Optional[int] = None
    trace_run_id: Optional[int] = None

    @classmethod
    def from_generated(cls, generated: GeneratedTaskPlan) -> "TaskPlan":
        """将规划模型输出转换为平台领域实体。"""
        steps = [
            TaskPlanStep(
                step_key=f"step-{index}",
                order=index,
                title=item.title.strip(),
                instruction=item.instruction.strip(),
            )
            for index, item in enumerate(generated.steps, start=1)
        ]
        return cls(goal=generated.goal.strip(), steps=steps)

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
        steps: Optional[List[TaskPlanStep]] = None,
    ) -> "TaskPlan":
        """从数据库记录或 LangGraph State 构造计划实体。"""
        raw_steps = value.get("steps") or []
        plan_steps = steps or [TaskPlanStep.from_mapping(item) for item in raw_steps]
        return cls(
            id=int(value["id"]) if value.get("id") is not None else None,
            trace_run_id=(
                int(value["trace_run_id"])
                if value.get("trace_run_id") is not None else None
            ),
            goal=str(value.get("goal") or ""),
            status=TaskPlanStatus(str(value.get("status") or "pending")),
            current_step_order=int(value.get("current_step_order") or 0),
            steps=plan_steps,
        )

    def step_at(self, index: int) -> TaskPlanStep:
        """按照从 0 开始的列表下标返回待执行步骤。"""
        return self.steps[index]

    def replace_step(self, updated_step: TaskPlanStep) -> "TaskPlan":
        """返回替换指定步骤后的新计划实体。"""
        updated_steps = [
            updated_step if item.step_key == updated_step.step_key else item
            for item in self.steps
        ]
        return replace(
            self,
            steps=updated_steps,
            current_step_order=updated_step.order,
        )

    def with_status(self, status: TaskPlanStatus) -> "TaskPlan":
        """返回更新整体状态后的新计划实体。"""
        return replace(self, status=status)

    def to_dict(self) -> dict[str, Any]:
        """转换为数据库、State 和 SSE 可复用的 JSON 结构。"""
        return {
            "id": self.id,
            "trace_run_id": self.trace_run_id,
            "goal": self.goal,
            "status": self.status.value,
            "current_step_order": self.current_step_order,
            "steps": [step.to_dict() for step in self.steps],
        }
