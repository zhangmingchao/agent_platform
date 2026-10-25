"""LangChain 工具执行流水线。"""

import json
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from langchain_core.tools import StructuredTool

from ..models.permission import ToolExecutionRequest, ToolRiskLevel
from ..models.session_event import SessionEventRecord, SessionEventSource, SessionEventType
from ..runtime.models import RuntimeContext
from ..services.permission_service import decide_tool_execution
from ..services.session_event_service import append_session_event

log = logging.getLogger(__name__)

_MEDIUM_RISK_TOOLS = {"ExecutePython"}
_HIGH_RISK_KEYWORDS = ("shell", "bash", "terminal", "delete", "remove", "drop")


class ToolPipelineStage(str, Enum):
    """工具执行流水线阶段。"""

    VALIDATE_ARGUMENTS = "validate_arguments"
    PERMISSION_DECISION = "permission_decision"
    BEFORE_EXECUTE = "before_execute"
    EXECUTE = "execute"
    AFTER_EXECUTE = "after_execute"
    ON_ERROR = "on_error"


def classify_tool_risk(tool_name: str) -> ToolRiskLevel:
    """根据工具名称给出默认风险等级。

    Args:
        tool_name: LangChain 工具名称。

    Returns:
        工具风险等级。未识别工具默认低风险，避免误伤只读 MCP 查询。
    """
    normalized = tool_name.strip()
    lowered = normalized.lower()
    if normalized in _MEDIUM_RISK_TOOLS:
        return ToolRiskLevel.MEDIUM
    if any(keyword in lowered for keyword in _HIGH_RISK_KEYWORDS):
        return ToolRiskLevel.HIGH
    return ToolRiskLevel.LOW


def _arguments_summary(arguments: Dict[str, Any]) -> str:
    """生成工具参数摘要，避免审计日志保存完整敏感参数。

    Args:
        arguments: 工具调用参数。

    Returns:
        描述参数键和值长度的字符串。
    """
    parts: List[str] = []
    for key, value in sorted(arguments.items()):
        if isinstance(value, str):
            parts.append(f"{key}=str:{len(value)}")
        elif isinstance(value, list):
            parts.append(f"{key}=list:{len(value)}")
        elif isinstance(value, dict):
            parts.append(f"{key}=object:{len(value)}")
        else:
            parts.append(f"{key}={type(value).__name__}")
    return ", ".join(parts)


async def _append_pipeline_event(
    context: RuntimeContext,
    tool_name: str,
    stage: ToolPipelineStage,
    status: str,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """追加工具流水线阶段事件。

    Args:
        context: 当前 Agent 运行上下文。
        tool_name: 工具名称。
        stage: 当前流水线阶段。
        status: 阶段状态。
        payload: 阶段摘要数据，避免保存完整敏感参数。
    """
    await append_session_event(
        SessionEventRecord(
            user_id=context.user_id,
            session_id=context.session_id,
            trace_run_id=context.trace_ctx.run_id if context.trace_ctx else None,
            agent_id=context.agent_id,
            workflow_run_id=context.workflow_run_id,
            workflow_step_id=context.workflow_step_id,
            event_source=SessionEventSource.TOOL_PIPELINE,
            event_type=(
                SessionEventType.PERMISSION_DECISION
                if stage is ToolPipelineStage.PERMISSION_DECISION
                else SessionEventType.TOOL_STAGE
            ),
            phase=stage.value,
            name=tool_name,
            status=status,
            payload=payload or {},
        )
    )


def _validate_arguments(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """标准化工具参数。

    Args:
        arguments: LangChain 传入的工具参数。

    Returns:
        可继续传递给原始工具的参数。
    """
    return dict(arguments)


def _merge_permission_payload(result: Any, permission: Dict[str, Any]) -> Any:
    """在不破坏普通文本工具的前提下追加权限审计信息。

    Args:
        result: 原始工具执行结果。
        permission: 本次权限决策的可序列化结构。

    Returns:
        如果原始结果是 JSON 对象字符串，则追加 ``permission`` 后重新序列化；
        否则原样返回，避免破坏 Skill 文档等文本工具输出。
    """
    if not isinstance(result, str):
        return result
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        return result
    if not isinstance(parsed, dict):
        return result
    parsed.setdefault("permission", permission)
    return json.dumps(parsed, ensure_ascii=False, default=str)


def _rejected_result(decision_reason: str, permission: Dict[str, Any]) -> str:
    """生成统一的工具拒绝返回值。

    Args:
        decision_reason: 拒绝执行的中文原因。
        permission: 本次权限决策的可序列化结构。

    Returns:
        JSON 字符串，供模型识别工具未执行原因。
    """
    return json.dumps(
        {
            "status": "rejected",
            "error": decision_reason,
            "permission": permission,
        },
        ensure_ascii=False,
    )


def wrap_tool_with_execution_pipeline(
    tool: StructuredTool,
    context: RuntimeContext,
) -> StructuredTool:
    """为单个 LangChain 工具增加统一执行流水线。

    Args:
        tool: 原始 LangChain 工具。
        context: 当前 Agent 运行上下文，包含用户、会话、权限预设和调用来源。

    Returns:
        名称、描述和参数结构保持不变的新工具；调用时会先执行权限决策。
    """
    tool_name = tool.name
    risk_level = ToolRiskLevel((tool.metadata or {}).get("risk_level")) if (tool.metadata or {}).get("plugin_process") else classify_tool_risk(tool_name)

    async def execute_with_pipeline(**kwargs: Any) -> Any:
        """按多阶段流水线执行工具。"""
        started_at = time.time()
        try:
            normalized_kwargs = _validate_arguments(kwargs)
            arguments_summary = _arguments_summary(normalized_kwargs)
            await _append_pipeline_event(
                context,
                tool_name,
                ToolPipelineStage.VALIDATE_ARGUMENTS,
                "success",
                {"argumentsSummary": arguments_summary},
            )
        except Exception as exc:
            await _append_pipeline_event(
                context,
                tool_name,
                ToolPipelineStage.ON_ERROR,
                "error",
                {"error": str(exc)[:500]},
            )
            raise

        decision = decide_tool_execution(
            ToolExecutionRequest(
                user_id=context.user_id,
                agent_id=context.agent_id,
                session_id=context.session_id,
                tool_name=tool_name,
                risk_level=risk_level,
                permission_preset=context.permission_preset,
                invocation_source=context.invocation_source,
                arguments_summary=arguments_summary,
            )
        )
        permission = decision.to_dict()
        await _append_pipeline_event(
            context,
            tool_name,
            ToolPipelineStage.PERMISSION_DECISION,
            "allowed" if decision.allowed else "rejected",
            {
                "riskLevel": risk_level.value,
                "permission": permission,
                "argumentsSummary": arguments_summary,
            },
        )
        log.info(
            "[ToolPipeline] tool=%s risk=%s allowed=%s preset=%s source=%s",
            tool_name,
            risk_level.value,
            decision.allowed,
            context.permission_preset.value,
            context.invocation_source,
        )
        if not decision.allowed:
            return _rejected_result(decision.reason, permission)

        await _append_pipeline_event(
            context,
            tool_name,
            ToolPipelineStage.BEFORE_EXECUTE,
            "started",
            {"sandboxMode": permission.get("sandboxMode")},
        )
        try:
            await _append_pipeline_event(
                context,
                tool_name,
                ToolPipelineStage.EXECUTE,
                "started",
                {"argumentsSummary": arguments_summary},
            )
            result = await tool.ainvoke(normalized_kwargs)
            duration_ms = int((time.time() - started_at) * 1000)
            await _append_pipeline_event(
                context,
                tool_name,
                ToolPipelineStage.AFTER_EXECUTE,
                "success",
                {
                    "durationMs": duration_ms,
                    "resultType": type(result).__name__,
                },
            )
            return _merge_permission_payload(result, permission)
        except Exception as exc:
            await _append_pipeline_event(
                context,
                tool_name,
                ToolPipelineStage.ON_ERROR,
                "error",
                {"error": str(exc)[:500]},
            )
            raise

    return StructuredTool.from_function(
        coroutine=execute_with_pipeline,
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
        metadata=tool.metadata,
    )


def wrap_tools_with_execution_pipeline(
    tools: List[StructuredTool],
    context: Optional[RuntimeContext],
) -> List[StructuredTool]:
    """为工具列表统一接入执行流水线。

    Args:
        tools: 已构建完成的 LangChain 工具列表。
        context: 当前运行上下文；缺少上下文时返回原工具列表。

    Returns:
        接入权限判断、拒绝返回和 JSON 审计合并后的工具列表。
    """
    if context is None:
        return tools
    return [wrap_tool_with_execution_pipeline(tool, context) for tool in tools]
