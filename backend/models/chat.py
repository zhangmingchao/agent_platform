"""聊天准备阶段使用的强类型业务实体。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional

from .mcp import McpConfig
from .task_planning import PlanningMode

if TYPE_CHECKING:
    from ..core.trace_handler import TraceContext
    from langgraph.graph.state import CompiledStateGraph


def _required_int(data: Mapping[str, Any], field_name: str) -> int:
    """读取必需整数，数据库字段缺失时尽早暴露数据问题。"""
    value = data.get(field_name)
    if value is None:
        raise ValueError(f"缺少必需字段: {field_name}")
    return int(value)


@dataclass(frozen=True)
class ChatUser:
    """当前通过认证的聊天用户。"""

    user_id: int
    username: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ChatUser":
        return cls(
            user_id=_required_int(data, "user_id"),
            username=str(data.get("username") or ""),
        )


@dataclass(frozen=True)
class ChatSession:
    """聊天会话执行所需的最小字段集合。"""

    id: int
    agent_id: int

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ChatSession":
        return cls(id=_required_int(data, "id"), agent_id=_required_int(data, "agent_id"))


@dataclass(frozen=True)
class ModelConfig:
    """用户选择的模型配置；包含调用模型所需的完整字段。"""

    id: int
    raw: Dict[str, Any] = field(repr=False)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ModelConfig":
        return cls(id=_required_int(data, "id"), raw=dict(data))

    def to_factory_dict(self) -> Dict[str, Any]:
        return dict(self.raw)


@dataclass(frozen=True)
class SkillConfig:
    """当前 Agent 关联的 Skill 配置。"""

    id: int
    name: str
    raw: Dict[str, Any] = field(repr=False)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SkillConfig":
        return cls(
            id=_required_int(data, "id"),
            name=str(data.get("name") or ""),
            raw=dict(data),
        )


@dataclass(frozen=True)
class RuntimeFile:
    """用户本轮允许 Agent 访问的 Runtime 文件。"""

    id: str
    file_name: str
    mime_type: Optional[str]
    size_bytes: Optional[int]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RuntimeFile":
        return cls(
            id=str(data.get("id") or ""),
            file_name=str(data.get("file_name") or ""),
            mime_type=data.get("mime_type"),
            size_bytes=(int(data["size_bytes"]) if data.get("size_bytes") is not None else None),
        )

    def to_attachment(self) -> Dict[str, Any]:
        """转换为写入聊天消息附件字段的安全结构，不包含宿主机路径。"""
        return {
            "kind": "runtime_file",
            "id": self.id,
            "name": self.file_name,
            "mimeType": self.mime_type,
            "size": self.size_bytes,
        }


@dataclass(frozen=True)
class ChatHistoryMessage:
    """从 MySQL 恢复的一条模型上下文消息。"""

    role: str
    content: str
    attachments: Any = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ChatHistoryMessage":
        return cls(
            role=str(data.get("role") or ""),
            content=str(data.get("content") or ""),
            attachments=data.get("attachments"),
        )


@dataclass(frozen=True)
class AgentStateContext:
    """注入 LangGraph 自定义 State 的聊天业务字段。

    Attributes:
        runtime_file_ids: 本轮允许 Runtime 工具访问的文件 ID。
        available_skills: 当前 Agent 已授权使用的 Skill 名称。
        loaded_skills: 本轮已经读取的 Skill 名称。
        current_input: 当前用户目标或工作流节点输入。
        current_node_id: 当前业务节点标识。
        planning_mode: 当前 Agent 是否启用显式任务规划。
    """

    runtime_file_ids: List[str]
    available_skills: List[str]
    loaded_skills: List[str]
    current_input: str
    current_node_id: str = "chat"
    planning_mode: PlanningMode = PlanningMode.DISABLED


@dataclass(frozen=True)
class PreparedChatRun:
    """执行一次聊天请求所需的全部强类型运行时数据。

    Attributes:
        agent_executor: 已经编译的 LangGraph Agent 执行器。
        history_messages: 本次发送给 Agent 的聊天历史。
        max_tool_rounds: 最大工具迭代次数。
        thread_id: 本次 LangGraph 执行使用的线程标识。
        trace_ctx: 本次执行关联的 Trace 上下文。
        output_schema: Agent 最终输出需要满足的 JSON Schema。
        state_context: 注入 LangGraph State 的业务上下文。
        execution_timeout_seconds: Agent 整体执行允许的最大秒数。
    """

    agent_executor: CompiledStateGraph
    history_messages: List[ChatHistoryMessage]
    max_tool_rounds: int
    thread_id: str
    trace_ctx: TraceContext
    output_schema: Optional[Dict[str, Any]]
    state_context: AgentStateContext
    execution_timeout_seconds: int = 120
