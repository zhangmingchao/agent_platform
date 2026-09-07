import json
import unittest
from typing import Any, Dict, Optional, get_type_hints
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from backend.core.workflow_state import (
    WorkflowSegmentRunner,
    build_workflow_lifecycle_graph,
    workflow_graph_config,
    workflow_thread_id,
)
from backend.core.workflow_checkpointer import (
    get_workflow_checkpointer,
    init_workflow_checkpointer,
)
from backend.services import workflow_service


class _Publisher:
    def __init__(self):
        self.events = []

    async def publish(self, event_type, data=None, *, node_id=None):
        self.events.append((event_type, data or {}, node_id))
        return f"1-{len(self.events)}"


class WorkflowApprovalTests(unittest.IsolatedAsyncioTestCase):
    def test_lifecycle_graph_builder_has_complete_type_hints(self) -> None:
        """生命周期图构造方法应声明 Checkpointer、分段执行器和返回图类型。"""
        hints = get_type_hints(build_workflow_lifecycle_graph)
        self.assertEqual(hints["checkpointer"], BaseCheckpointSaver[str])
        self.assertIs(hints["run_segment"], WorkflowSegmentRunner)
        self.assertIs(hints["return"], CompiledStateGraph)

    def test_checkpointer_accessors_have_return_types(self) -> None:
        """Checkpointer 初始化与获取方法应返回统一的抽象基类类型。"""
        init_hints = get_type_hints(init_workflow_checkpointer)
        getter_hints = get_type_hints(get_workflow_checkpointer)
        self.assertEqual(init_hints["return"], BaseCheckpointSaver[str])
        self.assertEqual(getter_hints["return"], BaseCheckpointSaver[str])

    def test_resume_workflow_graph_has_complete_type_hints(self) -> None:
        """工作流恢复入口应完整声明参数与运行结果类型。"""
        hints = get_type_hints(workflow_service.resume_workflow_graph)
        self.assertIs(hints["run_id"], int)
        self.assertIs(hints["user_id"], int)
        self.assertEqual(hints["resume_decision"], Optional[Dict[str, Any]])
        self.assertEqual(hints["return"], Dict[str, Any])

    async def test_approval_node_persists_resume_context_and_pauses(self):
        config = {
            "nodes": [
                {"id": "start", "type": "input"},
                {"id": "review", "type": "approval", "data": {"label": "发布审核", "prompt": "确认发布？"}},
                {"id": "end", "type": "output"},
            ],
            "edges": [
                {"source": "start", "target": "review"},
                {"source": "review", "target": "end"},
            ],
        }
        calls = []

        async def fake_execute(sql, params=()):
            calls.append((sql, params))
            return 91

        publisher = _Publisher()
        with patch.object(workflow_service, "execute", side_effect=fake_execute):
            with self.assertRaises(workflow_service.WorkflowApprovalRequired) as raised:
                await workflow_service._execute_dag(7, 2, 3, config, "待发布内容", publisher)

        self.assertEqual(raised.exception.result["status"], "waiting_approval")
        update_params = next(params for sql, params in calls if "context_json=%s" in sql)
        context = json.loads(update_params[2])
        self.assertEqual(context["resume_node_id"], "end")
        self.assertEqual(context["current_input"], "待发布内容")
        self.assertEqual(publisher.events[-1][0], "approval_required")

    async def test_approve_prepares_native_graph_resume(self):
        run = {
            "id": 7,
            "status": "waiting_approval",
            "context_json": {
                "approval_step_id": 91,
                "approval_node_id": "review",
                "resume_node_id": "agent-next",
                "current_input": "审核内容",
                "step_counter": 2,
            },
        }
        execute_mock = AsyncMock(return_value=1)
        publish_mock = AsyncMock(return_value="1-1")
        with (
            patch.object(workflow_service, "get_workflow_run", AsyncMock(return_value=run)),
            patch.object(workflow_service, "execute", execute_mock),
            patch.object(workflow_service.RedisStreamEventPublisher, "publish", publish_mock),
        ):
            result = await workflow_service.decide_workflow_approval(7, 2, True, "可以上线")

        self.assertTrue(result["resume"])
        self.assertEqual(
            result["resume_decision"],
            {"approved": True, "comment": "可以上线"},
        )
        running_update = execute_mock.await_args_list[-1].args
        self.assertEqual(running_update[1][0], "running")
        saved_context = json.loads(running_update[1][2])
        self.assertEqual(saved_context["resume_node_id"], "agent-next")
        # 审批标识保留到 Command 被 StateGraph 消费，便于恢复失败时重新提交。
        self.assertEqual(saved_context["approval_step_id"], 91)

    async def test_reject_also_resumes_graph_to_terminal_node(self):
        run = {
            "id": 7,
            "status": "waiting_approval",
            "context_json": {"approval_step_id": 91, "approval_node_id": "review"},
        }
        with (
            patch.object(workflow_service, "get_workflow_run", AsyncMock(return_value=run)),
            patch.object(workflow_service, "execute", AsyncMock(return_value=1)) as execute_mock,
            patch.object(workflow_service.RedisStreamEventPublisher, "publish", AsyncMock(return_value="1-1")),
        ):
            result = await workflow_service.decide_workflow_approval(7, 2, False, "内容不合规")

        self.assertTrue(result["resume"])
        self.assertEqual(result["status"], "running")
        self.assertEqual(result["resume_decision"]["approved"], False)
        self.assertTrue(any(call.args[1][0] == "running" for call in execute_mock.await_args_list))

    async def test_run_without_config_snapshot_is_rejected(self) -> None:
        """运行记录缺少配置快照时不得回查工作流当前配置。"""
        run = {
            "id": 7,
            "workflow_id": 3,
            "status": "running",
            "input_text": "执行任务",
            "workflow_config_json": None,
        }
        execute_mock = AsyncMock(return_value=1)
        with (
            patch.object(workflow_service, "get_workflow_run", AsyncMock(return_value=run)),
            patch.object(workflow_service, "get_workflow", AsyncMock()) as get_workflow_mock,
            patch.object(workflow_service, "get_workflow_checkpointer", return_value=InMemorySaver()),
            patch.object(workflow_service.RedisStreamEventPublisher, "publish", AsyncMock(return_value="1-1")),
            patch.object(workflow_service, "execute", execute_mock),
        ):
            with self.assertRaises(HTTPException) as raised:
                await workflow_service.resume_workflow_graph(7, 2)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(
            raised.exception.detail,
            "运行记录缺少工作流配置快照，请重新创建运行记录",
        )
        get_workflow_mock.assert_not_awaited()
        self.assertTrue(
            any(call.args[1][0] == "error" for call in execute_mock.await_args_list)
        )

    async def test_workflow_graph_uses_stable_thread_and_resumes_interrupt(self):
        """同一 run 应从持久化 interrupt 恢复，而不是重新提交初始 State。"""
        calls = []

        async def run_segment(state):
            calls.append(state.get("approval_status"))
            if state.get("approval_status") != "approved":
                return {
                    "status": "waiting_approval",
                    "approval_status": "pending",
                    "approval_payload": {"prompt": "确认发布？"},
                    "resume_context": {"resume_node_id": "end"},
                }
            return {"status": "success", "output": "发布完成"}

        graph = build_workflow_lifecycle_graph(InMemorySaver(), run_segment)
        config = workflow_graph_config(7)
        initial_state = {
            "run_id": 7,
            "workflow_id": 3,
            "user_id": 2,
            "workflow_config": {"nodes": [], "edges": []},
            "initial_input": "待发布内容",
            "current_input": "待发布内容",
            "status": "running",
        }

        paused = await graph.ainvoke(initial_state, config=config)
        self.assertTrue(paused.get("__interrupt__"))
        self.assertEqual(workflow_thread_id(7), "workflow_run_7")

        completed = await graph.ainvoke(
            Command(resume={"approved": True, "comment": "可以上线"}),
            config=config,
        )
        self.assertEqual(completed["status"], "success")
        self.assertEqual(completed["output"], "发布完成")
        self.assertEqual(calls, [None, "approved"])


if __name__ == "__main__":
    unittest.main()
