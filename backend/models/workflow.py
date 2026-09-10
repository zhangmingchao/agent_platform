"""工作流定义、运行记录与恢复上下文实体。"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional


def _json_mapping(value: Any) -> Optional[Dict[str, Any]]:
    """将数据库 JSON 值转换为字典。

    参数：
    - ``value``：数据库返回的 JSON 字符串、Mapping 或空值。

    返回值：合法 JSON 对象对应的字典；无值或格式错误时返回 ``None``。
    """
    if value is None:
        return None
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return dict(parsed) if isinstance(parsed, Mapping) else None
    return None


@dataclass(frozen=True)
class WorkflowDefinition:
    """数据库中的工作流定义实体。

    字段：
    - ``id``：工作流主键；
    - ``name``：工作流名称；
    - ``description``：工作流说明；
    - ``mode``：顺序或图式执行模式；
    - ``config``：创建、编辑工作流时保存的节点配置；
    - ``is_active``：是否允许创建新运行；
    - ``created_at`` / ``updated_at``：创建和更新时间。
    """

    id: int
    name: str
    description: str
    mode: str
    config: Dict[str, Any]
    is_active: bool
    created_at: Any = None
    updated_at: Any = None

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "WorkflowDefinition":
        """将数据库记录转换为工作流定义实体。

        参数：
        - ``row``：包含工作流字段的数据库 Mapping。
        """
        return cls(
            id=int(row["id"]),
            name=str(row.get("name") or ""),
            description=str(row.get("description") or ""),
            mode=str(row.get("mode") or "sequential"),
            config=_json_mapping(row.get("config_json") or row.get("config")) or {},
            is_active=bool(row.get("is_active", 1)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为保持现有 HTTP 协议兼容的响应字典。"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "mode": self.mode,
            "config": self.config,
            "is_active": int(self.is_active),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class WorkflowResumeContext:
    """人工审批暂停后恢复自定义 DAG 所需的现场实体。

    字段：
    - ``resume_node_id``：审批通过后继续执行的节点；
    - ``current_input``：恢复节点接收的输入；
    - ``step_counter``：恢复前已经使用的步骤序号；
    - ``approval_step_id``：数据库审批步骤 ID；
    - ``approval_node_id``：触发暂停的工作流节点 ID；
    - ``approval_label`` / ``approval_prompt``：审批展示信息。
    """

    resume_node_id: Optional[str] = None
    current_input: str = ""
    step_counter: int = 0
    approval_step_id: Optional[int] = None
    approval_node_id: Optional[str] = None
    approval_label: str = ""
    approval_prompt: str = ""

    @classmethod
    def from_value(cls, value: Any) -> "WorkflowResumeContext":
        """从数据库 JSON 值构造恢复上下文。

        参数：
        - ``value``：JSON 字符串、Mapping、实体或空值。
        """
        if isinstance(value, cls):
            return value
        data = _json_mapping(value) or {}
        return cls(
            resume_node_id=data.get("resume_node_id"),
            current_input=str(data.get("current_input") or ""),
            step_counter=int(data.get("step_counter") or 0),
            approval_step_id=(
                int(data["approval_step_id"])
                if data.get("approval_step_id") is not None
                else None
            ),
            approval_node_id=data.get("approval_node_id"),
            approval_label=str(data.get("approval_label") or ""),
            approval_prompt=str(data.get("approval_prompt") or ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为写入 MySQL JSON 和 LangGraph State 的字典。"""
        return {
            "resume_node_id": self.resume_node_id,
            "current_input": self.current_input,
            "step_counter": self.step_counter,
            "approval_step_id": self.approval_step_id,
            "approval_node_id": self.approval_node_id,
            "approval_label": self.approval_label,
            "approval_prompt": self.approval_prompt,
        }


@dataclass(frozen=True)
class WorkflowRun:
    """一次工作流运行及其配置快照实体。

    字段：
    - ``id`` / ``workflow_id``：运行和工作流主键；
    - ``status``：running、waiting_approval、success、error 等状态；
    - ``input_text`` / ``output_text``：本次运行输入和最终输出；
    - ``workflow_config``：创建运行时冻结的工作流配置快照；
    - ``resume_context``：审批暂停现场；
    - ``steps``：已经持久化的执行步骤。
    """

    id: int
    workflow_id: int
    status: str
    input_text: str
    output_text: Optional[str] = None
    error_text: Optional[str] = None
    current_node_id: Optional[str] = None
    workflow_config: Optional[Dict[str, Any]] = None
    resume_context: WorkflowResumeContext = field(default_factory=WorkflowResumeContext)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Any = None
    finished_at: Any = None
    created_at: Any = None

    @classmethod
    def from_mapping(
        cls,
        row: Mapping[str, Any],
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> "WorkflowRun":
        """将运行记录和步骤列表转换为实体。

        参数：
        - ``row``：数据库运行记录；
        - ``steps``：该运行已产生的步骤记录。
        """
        return cls(
            id=int(row["id"]),
            workflow_id=int(row["workflow_id"]),
            status=str(row.get("status") or ""),
            input_text=str(row.get("input_text") or ""),
            output_text=row.get("output_text"),
            error_text=row.get("error_text"),
            current_node_id=row.get("current_node_id"),
            workflow_config=_json_mapping(row.get("workflow_config_json")),
            resume_context=WorkflowResumeContext.from_value(row.get("context_json")),
            steps=list(steps or []),
            started_at=row.get("started_at"),
            finished_at=row.get("finished_at"),
            created_at=row.get("created_at"),
        )

    def require_workflow_config(self) -> Dict[str, Any]:
        """返回配置快照；缺少快照时抛出明确的数据约束错误。"""
        if self.workflow_config is None:
            raise ValueError("运行记录缺少工作流配置快照，请重新创建运行记录")
        return self.workflow_config

    def to_dict(self) -> Dict[str, Any]:
        """转换为保持现有工作流运行 HTTP 协议兼容的响应字典。"""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "error_text": self.error_text,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "created_at": self.created_at,
            "current_node_id": self.current_node_id,
            "context_json": self.resume_context.to_dict(),
            "workflow_config_json": self.workflow_config,
            "steps": self.steps,
        }
