"""动态原生 LangGraph 工作流编译器测试。"""

import unittest
from typing import Any, Dict, List

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from backend.core.workflow_native_engine import (
    NativeWorkflowEngine,
    NativeWorkflowState,
)
from backend.core.workflow_state import workflow_graph_config
from backend.models.workflow import WorkflowResumeContext


class _EventPublisher:
    """记录编译器发布事件的测试发布器。"""

    def __init__(self) -> None:
        """初始化事件列表。"""
        self.events: List[Dict[str, Any]] = []

    async def publish(
        self,
        event_type: str,
        data: Dict[str, Any] | None = None,
        *,
        node_id: str | None = None,
    ) -> str:
        """记录事件并返回模拟 Stream ID。"""
        self.events.append({"type": event_type, "data": data or {}, "node_id": node_id})
        return f"1-{len(self.events)}"


class NativeWorkflowEngineTests(unittest.IsolatedAsyncioTestCase):
    """验证前端节点会被动态编译成真实 LangGraph 节点。"""

    @staticmethod
    def _initial_state(config: Dict[str, Any]) -> NativeWorkflowState:
        """创建动态工作流测试初始 State。"""
        return {
            "run_id": 7,
            "workflow_id": 3,
            "user_id": 2,
            "workflow_config": config,
            "initial_input": "开始",
            "node_outputs": {},
            "status": "running",
        }

    async def test_compiles_linear_nodes_and_propagates_output(self) -> None:
        """输入、Agent 和输出节点应成为真实图节点并传递结果。"""
        config = {
            "nodes": [
                {"id": "input", "type": "input"},
                {"id": "agent", "type": "agent", "data": {}},
                {"id": "output", "type": "output"},
            ],
            "edges": [
                {"source": "input", "target": "agent"},
                {"source": "agent", "target": "output"},
            ],
        }

        async def run_agent(
            node: Dict[str, Any],
            state: NativeWorkflowState,
            node_input: str,
            order: int,
        ) -> str:
            """返回带节点信息的模拟 Agent 输出。"""
            return f"{node_input}-agent-{order}"

        async def prepare_approval(
            node: Dict[str, Any],
            state: NativeWorkflowState,
            node_input: str,
            order: int,
        ) -> WorkflowResumeContext:
            """线性测试不会调用审批回调。"""
            raise AssertionError("unexpected approval")

        engine = NativeWorkflowEngine(config, _EventPublisher(), run_agent, prepare_approval)
        graph = engine.compile(InMemorySaver())
        result = await graph.ainvoke(self._initial_state(config), config=workflow_graph_config(701))
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["output"], "开始-agent-1")

    async def test_condition_routes_only_selected_agent(self) -> None:
        """结构化条件应通过原生 conditional edges 只调度命中分支。"""
        config = {
            "nodes": [
                {"id": "input", "type": "input"},
                {
                    "id": "condition",
                    "type": "condition",
                    "data": {"conditions": [
                        {"type": "structured", "field": "type", "operator": "eq", "value": "1"},
                        {"type": "else"},
                    ]},
                },
                {"id": "agent-a", "type": "agent", "data": {}},
                {"id": "agent-b", "type": "agent", "data": {}},
            ],
            "edges": [
                {"source": "input", "target": "condition"},
                {"source": "condition", "target": "agent-a", "sourceHandle": "cond-0"},
                {"source": "condition", "target": "agent-b", "sourceHandle": "cond-1"},
            ],
        }
        calls: List[str] = []

        async def run_agent(
            node: Dict[str, Any],
            state: NativeWorkflowState,
            node_input: str,
            order: int,
        ) -> str:
            """记录被条件路由调度的 Agent。"""
            calls.append(node["id"])
            return node["id"]

        async def prepare_approval(
            node: Dict[str, Any],
            state: NativeWorkflowState,
            node_input: str,
            order: int,
        ) -> WorkflowResumeContext:
            """条件测试不会调用审批回调。"""
            raise AssertionError("unexpected approval")

        state = self._initial_state(config)
        state["initial_input"] = '{"type": 1}'
        graph = NativeWorkflowEngine(config, _EventPublisher(), run_agent, prepare_approval).compile(
            InMemorySaver()
        )
        await graph.ainvoke(state, config=workflow_graph_config(702))
        self.assertEqual(calls, ["agent-a"])

    async def test_parallel_branches_join_before_output(self) -> None:
        """并行节点的分支输出应通过 barrier 汇合后再进入输出节点。"""
        config = {
            "nodes": [
                {"id": "input", "type": "input"},
                {"id": "parallel", "type": "parallel"},
                {"id": "agent-a", "type": "agent", "data": {}},
                {"id": "agent-b", "type": "agent", "data": {}},
                {"id": "output", "type": "output"},
            ],
            "edges": [
                {"source": "input", "target": "parallel"},
                {"source": "parallel", "target": "agent-a"},
                {"source": "parallel", "target": "agent-b"},
                {"source": "agent-a", "target": "output"},
                {"source": "agent-b", "target": "output"},
            ],
        }

        async def run_agent(
            node: Dict[str, Any],
            state: NativeWorkflowState,
            node_input: str,
            order: int,
        ) -> str:
            """返回分支节点 ID 作为输出。"""
            return node["id"]

        async def prepare_approval(
            node: Dict[str, Any],
            state: NativeWorkflowState,
            node_input: str,
            order: int,
        ) -> WorkflowResumeContext:
            """并行测试不会调用审批回调。"""
            raise AssertionError("unexpected approval")

        graph = NativeWorkflowEngine(config, _EventPublisher(), run_agent, prepare_approval).compile(
            InMemorySaver()
        )
        result = await graph.ainvoke(self._initial_state(config), config=workflow_graph_config(703))
        self.assertEqual(result["output"], "agent-a\n\n---\n\nagent-b")

    async def test_approval_interrupt_resumes_without_repreparing(self) -> None:
        """审批恢复应从 interrupt 继续，不能重复执行审批准备节点。"""
        config = {
            "nodes": [
                {"id": "input", "type": "input"},
                {"id": "approval", "type": "approval", "data": {"label": "审核"}},
                {"id": "output", "type": "output"},
            ],
            "edges": [
                {"source": "input", "target": "approval"},
                {"source": "approval", "target": "output"},
            ],
        }
        prepare_calls = 0

        async def run_agent(
            node: Dict[str, Any],
            state: NativeWorkflowState,
            node_input: str,
            order: int,
        ) -> str:
            """审批测试不会调用 Agent。"""
            raise AssertionError("unexpected agent")

        async def prepare_approval(
            node: Dict[str, Any],
            state: NativeWorkflowState,
            node_input: str,
            order: int,
        ) -> WorkflowResumeContext:
            """记录审批准备次数并返回暂停现场。"""
            nonlocal prepare_calls
            prepare_calls += 1
            return WorkflowResumeContext(
                approval_step_id=91,
                approval_node_id="approval",
                approval_label="审核",
                approval_prompt="确认？",
                current_input=node_input,
                step_counter=order,
            )

        graph = NativeWorkflowEngine(config, _EventPublisher(), run_agent, prepare_approval).compile(
            InMemorySaver()
        )
        graph_config = workflow_graph_config(704)
        paused = await graph.ainvoke(self._initial_state(config), config=graph_config)
        self.assertTrue(paused.get("__interrupt__"))
        completed = await graph.ainvoke(
            Command(resume={"approved": True, "comment": "通过"}),
            config=graph_config,
        )
        self.assertEqual(completed["status"], "success")
        self.assertEqual(completed["output"], "开始")
        self.assertEqual(prepare_calls, 1)


if __name__ == "__main__":
    unittest.main()
