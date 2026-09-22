"""为普通聊天 Agent 构建显式任务规划与逐步执行 LangGraph。"""

import json
import logging
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ..models.task_planning import (
    GeneratedTaskPlan,
    PlannedStepDraft,
    TaskPlan,
    TaskPlanStatus,
    TaskPlanStepStatus,
)
from ..services.task_plan_service import (
    create_task_plan,
    finish_task_plan,
    finish_task_plan_step,
    start_task_plan_step,
)
from .agent_state import AgentPlatformState
from .trace_handler import TraceContext

log = logging.getLogger(__name__)

_PLAN_JSON_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def _message_text(message: Any) -> str:
    """从模型消息或多模态内容中提取可持久化文本。"""
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, Mapping):
                parts.append(str(item.get("text") or item.get("content") or ""))
        return "".join(parts)
    return str(content or "")


def _parse_generated_plan(raw_text: str, fallback_goal: str) -> TaskPlan:
    """解析规划模型 JSON；格式不兼容时退化为一个可执行步骤。"""
    candidate = raw_text.strip()
    fenced = _PLAN_JSON_PATTERN.fullmatch(candidate)
    if fenced:
        candidate = fenced.group(1)
    try:
        generated = GeneratedTaskPlan.model_validate_json(candidate)
        return TaskPlan.from_generated(generated)
    except Exception as exc:
        log.warning("[TaskPlan] structured plan parse failed, using one-step fallback: %s", exc)
        generated = GeneratedTaskPlan(
            goal=fallback_goal[:500] or "完成用户任务",
            steps=[
                PlannedStepDraft(
                    title="完成用户任务",
                    instruction=fallback_goal[:2000] or "根据当前上下文完成用户任务",
                )
            ],
        )
        return TaskPlan.from_generated(generated)


def _tool_catalog(tools: Sequence[BaseTool]) -> str:
    """生成提供给规划模型的有限工具目录。"""
    if not tools:
        return "当前没有可用工具，只能基于对话上下文完成任务。"
    lines = [
        f"- {tool.name}: {str(getattr(tool, 'description', '') or '')[:500]}"
        for tool in tools
    ]
    return "\n".join(lines)[:6000]


def _step_prompt(plan: TaskPlan, step_index: int) -> str:
    """生成当前步骤的执行指令，并附带已完成步骤结果。"""
    step = plan.step_at(step_index)
    completed = [
        f"{item.order}. {item.title}: {item.result_summary[:3000]}"
        for item in plan.steps
        if item.status is TaskPlanStepStatus.COMPLETED
    ]
    completed_text = "\n".join(completed) if completed else "无"
    return (
        "你正在执行一份显式任务计划。只完成当前步骤，不要提前执行后续步骤。\n\n"
        f"总目标：{plan.goal}\n"
        f"当前步骤：{step.order}/{len(plan.steps)} {step.title}\n"
        f"执行指令：{step.instruction}\n\n"
        f"已完成步骤结果：\n{completed_text}\n\n"
        "请使用必要的工具完成当前步骤，并输出可供后续步骤使用的结果摘要。"
    )


def _summary_prompt(plan: TaskPlan) -> str:
    """生成最终汇总模型使用的提示词。"""
    result_lines = []
    for step in plan.steps:
        result = step.result_summary or step.error_text or "没有结果"
        result_lines.append(
            f"{step.order}. {step.title} [{step.status.value}]\n{result[:5000]}"
        )
    return (
        f"用户总目标：{plan.goal}\n\n"
        "以下是显式任务计划各步骤的实际执行结果：\n"
        + "\n\n".join(result_lines)
        + "\n\n请基于这些实际结果生成最终答案。不得声称执行了结果中没有完成的操作；"
        "如果有步骤失败，必须明确说明影响。"
    )


def _last_ai_text(messages: Sequence[BaseMessage], start_index: int) -> str:
    """读取子图本轮新增消息中的最后一条 AI 文本。"""
    for message in reversed(list(messages[start_index:])):
        if isinstance(message, AIMessage):
            text = _message_text(message).strip()
            if text:
                return text
    return ""


def create_task_planning_graph(
    llm: BaseChatModel,
    react_graph: CompiledStateGraph,
    tools: Sequence[BaseTool],
    final_system_prompt: str,
    checkpointer: BaseCheckpointSaver,
    trace_ctx: TraceContext,
    user_id: int,
    agent_id: int,
    max_tool_rounds: int = 6,
) -> CompiledStateGraph:
    """构建“规划、逐步执行、最终汇总”的外层 LangGraph。

    Args:
        llm: 规划和最终汇总使用的聊天模型，沿用模型额度 Callback。
        react_graph: 每个步骤复用的现有 ReAct Agent 子图。
        tools: 规划模型可以参考的工具目录。
        final_system_prompt: 最终汇总必须遵循的 Agent 系统提示词。
        checkpointer: 外层图使用的 LangGraph Checkpointer。
        trace_ctx: 当前请求的 Trace 上下文，用于关联持久化计划。
        user_id: 当前调用用户 ID。
        agent_id: 当前执行 Agent ID。
        max_tool_rounds: 每个计划步骤允许的最大 ReAct 工具调用轮次。

    Returns:
        已编译的显式任务规划图。
    """
    tool_catalog = _tool_catalog(tools)

    async def plan_task(
        state: AgentPlatformState,
        config: RunnableConfig,
    ) -> Dict[str, Any]:
        """生成、持久化任务计划并发布创建事件。"""
        goal = str(state.get("current_input") or "").strip()
        planning_prompt = (
            "你是任务规划器。请把用户目标拆成按顺序执行的最少必要步骤，最多 6 步。"
            "步骤必须具体、可执行，不要执行任务，也不要输出解释。"
            "只能返回 JSON，格式为："
            '{"goal":"目标","steps":[{"title":"步骤名","instruction":"执行指令"}]}。'
            "不要规划超出工具能力的操作。\n\n"
            f"可用工具：\n{tool_catalog}\n\n用户目标：\n{goal}"
        )
        response = await llm.ainvoke(
            [SystemMessage(content="你负责生成安全、有限、可执行的任务计划。"),
             HumanMessage(content=planning_prompt)],
            config=config,
        )
        plan = _parse_generated_plan(_message_text(response), goal)
        if trace_ctx.run_id is None:
            raise RuntimeError("Trace 尚未创建，无法持久化任务计划")
        persisted = await create_task_plan(
            trace_run_id=trace_ctx.run_id,
            user_id=user_id,
            agent_id=agent_id,
            plan=plan,
        )
        await adispatch_custom_event(
            "plan_created",
            {"plan": persisted.to_dict()},
            config=config,
        )
        return {
            "task_plan": persisted.to_dict(),
            "current_plan_step_index": 0,
            "planning_phase": "executing",
            "plan_execution_error": "",
        }

    async def prepare_plan_step(
        state: AgentPlatformState,
        config: RunnableConfig,
    ) -> Dict[str, Any]:
        """标记当前步骤开始，并向 ReAct 子图追加步骤指令。"""
        plan = TaskPlan.from_mapping(state.get("task_plan") or {})
        step_index = int(state.get("current_plan_step_index") or 0)
        step = plan.step_at(step_index).with_status(TaskPlanStepStatus.RUNNING)
        plan = plan.replace_step(step).with_status(TaskPlanStatus.RUNNING)
        if plan.id is None:
            raise RuntimeError("任务计划缺少数据库主键")
        await start_task_plan_step(plan.id, step)
        await adispatch_custom_event(
            "plan_step_started",
            {"plan_id": plan.id, "step": step.to_dict()},
            config=config,
        )
        return {
            "task_plan": plan.to_dict(),
            "messages": [HumanMessage(content=_step_prompt(plan, step_index))],
        }

    async def execute_plan_step(
        state: AgentPlatformState,
        config: RunnableConfig,
    ) -> Dict[str, Any]:
        """调用现有 ReAct 子图执行当前步骤，并持久化步骤结果。"""
        plan = TaskPlan.from_mapping(state.get("task_plan") or {})
        step_index = int(state.get("current_plan_step_index") or 0)
        step = plan.step_at(step_index)
        original_messages = list(state.get("messages") or [])
        try:
            inner_config: RunnableConfig = dict(config)
            inner_config["recursion_limit"] = max(7, max_tool_rounds * 2 + 5)
            result = await react_graph.ainvoke(state, config=inner_config)
            result_messages = list(result.get("messages") or [])
            new_messages = result_messages[len(original_messages):]
            result_text = _last_ai_text(result_messages, len(original_messages))
            if not result_text:
                raise RuntimeError("当前计划步骤没有生成可用结果")
            updated_step = step.with_status(
                TaskPlanStepStatus.COMPLETED,
                result_summary=result_text,
            )
            plan = plan.replace_step(updated_step)
            if plan.id is None:
                raise RuntimeError("任务计划缺少数据库主键")
            await finish_task_plan_step(plan.id, updated_step)
            await adispatch_custom_event(
                "plan_step_completed",
                {"plan_id": plan.id, "step": updated_step.to_dict()},
                config=config,
            )
            return {
                "messages": new_messages,
                "task_plan": plan.to_dict(),
                "current_plan_step_index": step_index + 1,
                "plan_execution_error": "",
            }
        except Exception as exc:
            error_text = str(exc)[:5000]
            failed_step = step.with_status(
                TaskPlanStepStatus.FAILED,
                error_text=error_text,
            )
            plan = plan.replace_step(failed_step).with_status(TaskPlanStatus.FAILED)
            if plan.id is not None:
                await finish_task_plan_step(plan.id, failed_step)
            await adispatch_custom_event(
                "plan_step_failed",
                {"plan_id": plan.id, "step": failed_step.to_dict()},
                config=config,
            )
            return {
                "task_plan": plan.to_dict(),
                "plan_execution_error": error_text,
            }

    def route_after_step(state: AgentPlatformState) -> str:
        """失败时进入汇总，否则继续下一步骤或结束。"""
        if state.get("plan_execution_error"):
            return "finalize"
        plan = TaskPlan.from_mapping(state.get("task_plan") or {})
        step_index = int(state.get("current_plan_step_index") or 0)
        return "next" if step_index < len(plan.steps) else "finalize"

    async def finalize_plan(
        state: AgentPlatformState,
        config: RunnableConfig,
    ) -> Dict[str, Any]:
        """根据全部步骤结果生成唯一的最终用户答案。"""
        plan = TaskPlan.from_mapping(state.get("task_plan") or {})
        failed = any(step.status is TaskPlanStepStatus.FAILED for step in plan.steps)
        final_status = TaskPlanStatus.FAILED if failed else TaskPlanStatus.COMPLETED
        try:
            response = await llm.ainvoke(
                [
                    SystemMessage(content=final_system_prompt),
                    HumanMessage(content=_summary_prompt(plan)),
                ],
                config=config,
            )
        except Exception:
            if plan.id is not None:
                await finish_task_plan(plan.id, TaskPlanStatus.FAILED)
            raise
        plan = plan.with_status(final_status)
        if plan.id is None:
            raise RuntimeError("任务计划缺少数据库主键")
        await finish_task_plan(plan.id, final_status)
        await adispatch_custom_event(
            "plan_completed",
            {"plan": plan.to_dict()},
            config=config,
        )
        return {
            "messages": [response],
            "task_plan": plan.to_dict(),
            "planning_phase": final_status.value,
        }

    builder = StateGraph(AgentPlatformState)
    builder.add_node("create_task_plan", plan_task)
    builder.add_node("prepare_plan_step", prepare_plan_step)
    builder.add_node("execute_plan_step", execute_plan_step)
    builder.add_node("finalize_plan", finalize_plan)
    builder.add_edge(START, "create_task_plan")
    builder.add_edge("create_task_plan", "prepare_plan_step")
    builder.add_edge("prepare_plan_step", "execute_plan_step")
    builder.add_conditional_edges(
        "execute_plan_step",
        route_after_step,
        {"next": "prepare_plan_step", "finalize": "finalize_plan"},
    )
    builder.add_edge("finalize_plan", END)
    return builder.compile(checkpointer=checkpointer)
