"""显式任务规划图的顺序执行和状态持久化测试。"""

import unittest
from dataclasses import replace
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from backend.core.agent_state import build_agent_state
from backend.core.task_planning import create_task_planning_graph
from backend.models.task_planning import (
    TaskPlan,
    TaskPlanStatus,
    TaskPlanStep,
    TaskPlanStepStatus,
)
from backend.services.task_plan_service import fail_active_task_plan_by_trace


class _FakePlanningModel:
    """依次返回结构化计划和最终汇总答案的测试模型。"""

    def __init__(self) -> None:
        self.call_count = 0

    async def ainvoke(
        self,
        messages: List[BaseMessage],
        config: Dict[str, Any],
    ) -> AIMessage:
        """按照调用顺序返回固定消息。"""
        del messages, config
        self.call_count += 1
        if self.call_count == 1:
            return AIMessage(content=(
                '{"goal":"生成销售报告","steps":['
                '{"title":"读取数据","instruction":"读取销售数据"},'
                '{"title":"汇总报告","instruction":"根据数据生成摘要"}'
                "]}"
            ))
        return AIMessage(content="最终销售报告")


class _FakeReactGraph:
    """为每个计划步骤追加一条确定的 AI 结果。"""

    def __init__(self) -> None:
        self.call_count = 0

    async def ainvoke(
        self,
        state: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """模拟 ReAct 子图完成当前步骤。"""
        del config
        self.call_count += 1
        messages = list(state.get("messages") or [])
        messages.append(AIMessage(content=f"步骤结果-{self.call_count}"))
        return {"messages": messages}


class _TraceStub:
    """只提供规划持久化所需 Trace 主键的测试替身。"""

    run_id = 88


class TaskPlanningGraphTests(unittest.IsolatedAsyncioTestCase):
    """验证规划、逐步执行和最终汇总的控制顺序。"""

    async def test_plan_steps_execute_in_order_and_finish(self) -> None:
        """两个计划步骤应依次完成并形成唯一最终答案。"""
        llm = _FakePlanningModel()
        react_graph = _FakeReactGraph()

        async def persist_plan(
            trace_run_id: int,
            user_id: int,
            agent_id: int,
            plan: Any,
        ) -> Any:
            """模拟数据库为计划分配主键。"""
            self.assertEqual((trace_run_id, user_id, agent_id), (88, 7, 9))
            return replace(
                plan,
                id=101,
                trace_run_id=trace_run_id,
                status=TaskPlanStatus.RUNNING,
            )

        start_step = AsyncMock()
        finish_step = AsyncMock()
        finish_plan = AsyncMock()
        with (
            patch("backend.core.task_planning.create_task_plan", persist_plan),
            patch("backend.core.task_planning.start_task_plan_step", start_step),
            patch("backend.core.task_planning.finish_task_plan_step", finish_step),
            patch("backend.core.task_planning.finish_task_plan", finish_plan),
        ):
            graph = create_task_planning_graph(
                llm=llm,
                react_graph=react_graph,
                tools=[],
                final_system_prompt="你是报告助手",
                checkpointer=InMemorySaver(),
                trace_ctx=_TraceStub(),
                user_id=7,
                agent_id=9,
            )
            result = await graph.ainvoke(
                build_agent_state(
                    [HumanMessage(content="生成销售报告")],
                    current_input="生成销售报告",
                    planning_mode="explicit",
                ),
                config={
                    "configurable": {"thread_id": "planning-test"},
                    "recursion_limit": 30,
                },
            )

        self.assertEqual(llm.call_count, 2)
        self.assertEqual(react_graph.call_count, 2)
        self.assertEqual(start_step.await_count, 2)
        self.assertEqual(finish_step.await_count, 2)
        finish_plan.assert_awaited_once_with(101, TaskPlanStatus.COMPLETED)
        self.assertEqual(result["task_plan"]["status"], "completed")
        self.assertTrue(all(
            step["status"] == TaskPlanStepStatus.COMPLETED.value
            for step in result["task_plan"]["steps"]
        ))
        self.assertEqual(result["messages"][-1].content, "最终销售报告")


class TaskPlanCleanupTests(unittest.IsolatedAsyncioTestCase):
    """验证异常退出时活动计划和步骤会被回收。"""

    async def test_fail_active_plan_marks_running_and_pending_steps(self) -> None:
        """运行步骤应失败、待执行步骤应跳过，计划最终状态应失败。"""
        running_plan = TaskPlan(
            id=101,
            trace_run_id=88,
            goal="生成销售报告",
            status=TaskPlanStatus.RUNNING,
            current_step_order=1,
            steps=[
                TaskPlanStep(
                    step_key="step-1",
                    order=1,
                    title="读取数据",
                    instruction="读取销售数据",
                    status=TaskPlanStepStatus.RUNNING,
                ),
                TaskPlanStep(
                    step_key="step-2",
                    order=2,
                    title="生成报告",
                    instruction="汇总数据",
                ),
            ],
        )
        failed_plan = running_plan.with_status(TaskPlanStatus.FAILED)
        get_by_trace = AsyncMock(return_value=running_plan)
        get_plan = AsyncMock(return_value=failed_plan)
        execute = AsyncMock()
        finish_plan = AsyncMock()

        with (
            patch(
                "backend.services.task_plan_service.get_task_plan_by_trace",
                get_by_trace,
            ),
            patch("backend.services.task_plan_service.get_task_plan", get_plan),
            patch("backend.services.task_plan_service.execute", execute),
            patch("backend.services.task_plan_service.finish_task_plan", finish_plan),
        ):
            result = await fail_active_task_plan_by_trace(88, "client disconnected")

        self.assertIs(result, failed_plan)
        execute.assert_awaited_once()
        update_params = execute.await_args.args[1]
        self.assertIn(TaskPlanStepStatus.FAILED.value, update_params)
        self.assertIn(TaskPlanStepStatus.SKIPPED.value, update_params)
        finish_plan.assert_awaited_once_with(101, TaskPlanStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
