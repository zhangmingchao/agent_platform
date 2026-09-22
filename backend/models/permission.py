"""Agent 工具执行权限模型。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SandboxMode(str, Enum):
    """工具执行时可使用的文件系统沙箱模式。"""

    READ_ONLY = "read_only"
    WORKSPACE_WRITE = "workspace_write"
    FULL_ACCESS = "full_access"


class ApprovalPolicy(str, Enum):
    """工具执行前的审批策略。"""

    ASK = "ask"
    NEVER = "never"


class PermissionPreset(str, Enum):
    """面向用户展示的权限预设。"""

    SAFE = "safe"
    STANDARD = "standard"
    AUTO = "auto"
    DEVELOPER = "developer"


class ToolRiskLevel(str, Enum):
    """工具调用的风险等级。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApprovalStatus(str, Enum):
    """单次工具调用的审批结果。"""

    NOT_REQUIRED = "not_required"
    ALLOWED_ONCE = "allowed_once"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"


class NetworkPolicy(str, Enum):
    """工具执行时的网络访问策略。"""

    DISABLED = "disabled"
    ALLOWLIST = "allowlist"
    UNRESTRICTED = "unrestricted"


@dataclass(frozen=True)
class PermissionPresetSpec:
    """权限预设展开后的底层策略。

    Attributes:
        preset: 权限预设标识。
        sandbox_mode: 工具执行时采用的文件系统沙箱模式。
        approval_policy: 高风险工具调用的审批策略。
        allowed_tools: 显式允许的工具名列表；为空表示按风险等级判断。
        denied_tools: 显式拒绝的工具名列表，优先级高于风险等级。
        readable_paths: 允许读取的路径前缀，供 Runtime 或未来沙箱执行器使用。
        writable_paths: 允许写入的路径前缀，供 Runtime 或未来沙箱执行器使用。
        network_policy: 网络访问策略。
        allowed_domains: 网络白名单域名；仅 allowlist 策略下生效。
        blocked_commands: 命令级风险关键字，用于 Shell 类工具接入时阻断高危动作。
        name: 面向前端展示的中文名称。
        description: 面向用户解释该预设影响范围的说明。
    """

    preset: PermissionPreset
    sandbox_mode: SandboxMode
    approval_policy: ApprovalPolicy
    name: str
    description: str
    allowed_tools: List[str] = field(default_factory=list)
    denied_tools: List[str] = field(default_factory=list)
    readable_paths: List[str] = field(default_factory=list)
    writable_paths: List[str] = field(default_factory=list)
    network_policy: NetworkPolicy = NetworkPolicy.DISABLED
    allowed_domains: List[str] = field(default_factory=list)
    blocked_commands: List[str] = field(default_factory=list)

    def policy_snapshot(self) -> Dict[str, object]:
        """返回可写入审计日志的权限规则快照。"""
        return {
            "allowedTools": list(self.allowed_tools),
            "deniedTools": list(self.denied_tools),
            "readablePaths": list(self.readable_paths),
            "writablePaths": list(self.writable_paths),
            "networkPolicy": self.network_policy.value,
            "allowedDomains": list(self.allowed_domains),
            "blockedCommands": list(self.blocked_commands),
        }


@dataclass(frozen=True)
class ToolExecutionRequest:
    """一次工具调用的权限判断上下文。

    Attributes:
        user_id: 发起工具调用的平台用户 ID。
        agent_id: 工具调用所属 Agent ID。
        session_id: 平台聊天会话 ID；外部 API 或工作流场景可以为空。
        tool_name: LangChain/MCP 暴露给模型的工具名称。
        risk_level: 当前工具调用的风险等级。
        permission_preset: 本次调用使用的权限预设。
        invocation_source: 调用来源，例如 platform、api 或 workflow。
        arguments_summary: 工具参数摘要，只记录审计所需信息，不保存完整敏感内容。
    """

    user_id: int
    agent_id: Optional[int]
    session_id: Optional[int]
    tool_name: str
    risk_level: ToolRiskLevel
    permission_preset: PermissionPreset
    invocation_source: str
    arguments_summary: str = ""


@dataclass(frozen=True)
class ToolExecutionDecision:
    """工具执行权限决策。

    Attributes:
        allowed: 是否允许继续执行真实工具。
        sandbox_mode: 本次工具应使用的沙箱模式。
        approval_policy: 本次工具适用的审批策略。
        approval_status: 审批链路的最终状态。
        reason: 允许或拒绝的中文原因。
        risk_level: 当前工具风险等级，便于写入 Trace。
        permission_preset: 决策来源的权限预设。
        policy_snapshot: 本次决策使用的细粒度规则快照。
    """

    allowed: bool
    sandbox_mode: SandboxMode
    approval_policy: ApprovalPolicy
    approval_status: ApprovalStatus
    reason: str
    risk_level: ToolRiskLevel
    permission_preset: PermissionPreset
    policy_snapshot: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """转换为可序列化结构，用于工具返回值和 Trace 审计。"""
        return {
            "allowed": self.allowed,
            "sandboxMode": self.sandbox_mode.value,
            "approvalPolicy": self.approval_policy.value,
            "approvalStatus": self.approval_status.value,
            "reason": self.reason,
            "riskLevel": self.risk_level.value,
            "permissionPreset": self.permission_preset.value,
            "policy": dict(self.policy_snapshot),
        }
