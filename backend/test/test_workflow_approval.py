import unittest
from typing import get_type_hints
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from backend.core import workflow_checkpointer
from backend.core.workflow_checkpointer import close_workflow_checkpointer, get_workflow_checkpointer, init_workflow_checkpointer
from backend.core.workflow_native_engine import NativeWorkflowState
from backend.core.workflow_state import workflow_graph_config, workflow_thread_id
from backend.models.workflow import WorkflowRun
from backend.services import workflow_service


class WorkflowApprovalTests(unittest.IsolatedAsyncioTestCase):
    """验证原生动态 LangGraph 的 Checkpointer 和审批入口。"""

    def test_checkpointer_accessors_have_return_types(self) -> None:
        """Checkpointer 初始化与获取方法应返回统一抽象类型。"""
        self.assertEqual(get_type_hints(init_workflow_checkpointer)["return"], BaseCheckpointSaver[str])
        self.assertEqual(get_type_hints(get_workflow_checkpointer)["return"], BaseCheckpointSaver[str])

    async def test_checkpointer_failure_never_falls_back_to_memory(self) -> None:
        """Redis Checkpointer 初始化失败时，任何环境都必须拒绝继续运行。"""
        await close_workflow_checkpointer()
        context = AsyncMock()
        context.__aenter__.side_effect = ConnectionError("redis unavailable")
        with patch.object(workflow_checkpointer.AsyncRedisSaver, "from_conn_string", return_value=context):
            with self.assertRaises(ConnectionError):
                await init_workflow_checkpointer()
        with self.assertRaises(RuntimeError):
            get_workflow_checkpointer()

    async def test_run_without_config_snapshot_is_rejected(self) -> None:
        """运行记录缺少配置快照时不得读取工作流当前配置。"""
        run = WorkflowRun(id=7, workflow_id=3, status="running", input_text="执行任务")
        with (
            patch.object(workflow_service, "find_workflow_run_entity", AsyncMock(return_value=run)),
            patch.object(workflow_service, "get_workflow", AsyncMock()) as get_workflow_mock,
            patch.object(workflow_service, "get_workflow_checkpointer", return_value=InMemorySaver()),
            patch.object(workflow_service.RedisStreamEventPublisher, "publish", AsyncMock(return_value="1-1")),
            patch.object(workflow_service, "execute", AsyncMock(return_value=1)),
        ):
            with self.assertRaises(HTTPException) as raised:
                await workflow_service.resume_workflow_graph(7, 2)
        self.assertEqual(raised.exception.status_code, 409)
        get_workflow_mock.assert_not_awaited()

    def test_native_state_contains_resume_fields(self) -> None:
        """原生 State 应保留工作流恢复所需的基础字段。"""
        hints = get_type_hints(NativeWorkflowState)
        self.assertIn("node_outputs", hints)
        self.assertIn("approval_payload", hints)
        self.assertEqual(workflow_thread_id(7), "workflow_run_v2_7")
        self.assertEqual(workflow_graph_config(7)["configurable"]["thread_id"], "workflow_run_v2_7")


if __name__ == "__main__":
    unittest.main()
