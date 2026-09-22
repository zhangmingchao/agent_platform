"""Agent 工具权限决策服务。"""

from typing import Mapping

from ..models.permission import (
    ApprovalPolicy,
    ApprovalStatus,
    NetworkPolicy,
    PermissionPreset,
    PermissionPresetSpec,
    SandboxMode,
    ToolExecutionDecision,
    ToolExecutionRequest,
    ToolRiskLevel,
)


PERMISSION_PRESETS: Mapping[PermissionPreset, PermissionPresetSpec] = {
    PermissionPreset.SAFE: PermissionPresetSpec(
        preset=PermissionPreset.SAFE,
        sandbox_mode=SandboxMode.READ_ONLY,
        approval_policy=ApprovalPolicy.NEVER,
        name="安全模式",
        description="只允许低风险只读工具，高风险工具会直接拒绝。",
        denied_tools=["ExecutePython"],
        readable_paths=["/workspace/input"],
        writable_paths=[],
        network_policy=NetworkPolicy.DISABLED,
        blocked_commands=["rm", "curl", "wget", "ssh", "docker", "kubectl"],
    ),
    PermissionPreset.STANDARD: PermissionPresetSpec(
        preset=PermissionPreset.STANDARD,
        sandbox_mode=SandboxMode.WORKSPACE_WRITE,
        approval_policy=ApprovalPolicy.ASK,
        name="标准模式",
        description="允许工作区内写入；高风险工具需要交互式审批。",
        readable_paths=["/workspace/input", "/workspace/output"],
        writable_paths=["/workspace/output"],
        network_policy=NetworkPolicy.ALLOWLIST,
        allowed_domains=[],
        blocked_commands=["rm -rf", "mkfs", "dd", "shutdown", "reboot"],
    ),
    PermissionPreset.AUTO: PermissionPresetSpec(
        preset=PermissionPreset.AUTO,
        sandbox_mode=SandboxMode.WORKSPACE_WRITE,
        approval_policy=ApprovalPolicy.NEVER,
        name="自动模式",
        description="适合无人值守；中低风险工具可执行，高风险工具直接拒绝。",
        readable_paths=["/workspace/input", "/workspace/output"],
        writable_paths=["/workspace/output"],
        network_policy=NetworkPolicy.DISABLED,
        blocked_commands=["rm -rf", "mkfs", "dd", "shutdown", "reboot", "curl", "wget", "ssh"],
    ),
    PermissionPreset.DEVELOPER: PermissionPresetSpec(
        preset=PermissionPreset.DEVELOPER,
        sandbox_mode=SandboxMode.FULL_ACCESS,
        approval_policy=ApprovalPolicy.ASK,
        name="开发者模式",
        description="允许更宽执行边界；高风险工具仍需要审批。",
        readable_paths=["/workspace", "/tmp"],
        writable_paths=["/workspace/output", "/tmp"],
        network_policy=NetworkPolicy.ALLOWLIST,
        allowed_domains=[],
        blocked_commands=["rm -rf /", "mkfs", "dd if=", "shutdown", "reboot"],
    ),
}


def normalize_permission_preset(value: object) -> PermissionPreset:
    """将接口或数据库中的权限预设值规范化为枚举。

    Args:
        value: 外部传入的权限预设字符串或枚举值。

    Returns:
        有效的权限预设；空值默认返回标准模式。

    Raises:
        ValueError: 传入值不是系统支持的权限预设时抛出。
    """
    if isinstance(value, PermissionPreset):
        return value
    raw_value = str(value or PermissionPreset.STANDARD.value)
    return PermissionPreset(raw_value)


def preset_spec(preset: PermissionPreset) -> PermissionPresetSpec:
    """读取权限预设详情。

    Args:
        preset: 需要展开的权限预设。

    Returns:
        预设对应的沙箱模式、审批策略和展示信息。
    """
    return PERMISSION_PRESETS[preset]


def decide_tool_execution(request: ToolExecutionRequest) -> ToolExecutionDecision:
    """根据权限预设和工具风险等级生成单次执行决策。

    Args:
        request: 本次工具调用的用户、Agent、会话、来源和风险上下文。

    Returns:
        工具执行决策实体；只有 ``allowed=True`` 时调用方才可以执行真实工具。
    """
    spec = preset_spec(request.permission_preset)
    policy_snapshot = spec.policy_snapshot()
    if request.tool_name in spec.denied_tools:
        return ToolExecutionDecision(
            allowed=False,
            sandbox_mode=spec.sandbox_mode,
            approval_policy=spec.approval_policy,
            approval_status=ApprovalStatus.REJECTED,
            reason="当前权限预设显式拒绝该工具",
            risk_level=request.risk_level,
            permission_preset=request.permission_preset,
            policy_snapshot=policy_snapshot,
        )
    if spec.allowed_tools and request.tool_name not in spec.allowed_tools:
        return ToolExecutionDecision(
            allowed=False,
            sandbox_mode=spec.sandbox_mode,
            approval_policy=spec.approval_policy,
            approval_status=ApprovalStatus.REJECTED,
            reason="当前权限预设未将该工具列入允许清单",
            risk_level=request.risk_level,
            permission_preset=request.permission_preset,
            policy_snapshot=policy_snapshot,
        )

    if request.risk_level is ToolRiskLevel.LOW:
        return ToolExecutionDecision(
            allowed=True,
            sandbox_mode=spec.sandbox_mode,
            approval_policy=spec.approval_policy,
            approval_status=ApprovalStatus.NOT_REQUIRED,
            reason="低风险工具不需要审批",
            risk_level=request.risk_level,
            permission_preset=request.permission_preset,
            policy_snapshot=policy_snapshot,
        )

    if request.risk_level is ToolRiskLevel.MEDIUM:
        if spec.sandbox_mode is SandboxMode.READ_ONLY:
            return ToolExecutionDecision(
                allowed=False,
                sandbox_mode=spec.sandbox_mode,
                approval_policy=spec.approval_policy,
                approval_status=ApprovalStatus.REJECTED,
                reason="当前安全模式为只读，拒绝执行会产生副作用的工具",
                risk_level=request.risk_level,
                permission_preset=request.permission_preset,
                policy_snapshot=policy_snapshot,
            )
        return ToolExecutionDecision(
            allowed=True,
            sandbox_mode=spec.sandbox_mode,
            approval_policy=spec.approval_policy,
            approval_status=ApprovalStatus.NOT_REQUIRED,
            reason="中风险工具允许在当前沙箱边界内执行",
            risk_level=request.risk_level,
            permission_preset=request.permission_preset,
            policy_snapshot=policy_snapshot,
        )

    if spec.approval_policy is ApprovalPolicy.NEVER:
        return ToolExecutionDecision(
            allowed=False,
            sandbox_mode=spec.sandbox_mode,
            approval_policy=spec.approval_policy,
            approval_status=ApprovalStatus.REJECTED,
            reason="当前审批策略为 never，高风险工具默认拒绝",
            risk_level=request.risk_level,
            permission_preset=request.permission_preset,
            policy_snapshot=policy_snapshot,
        )

    return ToolExecutionDecision(
        allowed=False,
        sandbox_mode=spec.sandbox_mode,
        approval_policy=spec.approval_policy,
        approval_status=ApprovalStatus.UNAVAILABLE,
        reason="高风险工具需要审批，但当前版本尚未接入交互式审批通道",
        risk_level=request.risk_level,
        permission_preset=request.permission_preset,
        policy_snapshot=policy_snapshot,
    )
