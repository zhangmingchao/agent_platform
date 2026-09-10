"""工作流领域实体和 Repository 转换测试。"""

import unittest
from unittest.mock import AsyncMock, patch

from backend.models.workflow import (
    WorkflowDefinition,
    WorkflowResumeContext,
    WorkflowRun,
)
from backend.repositories import workflow_repository


class WorkflowModelTests(unittest.IsolatedAsyncioTestCase):
    """验证数据库 Mapping 仅在 Repository 边界转换为工作流实体。"""

    def test_definition_parses_config_json(self) -> None:
        """工作流定义应将配置 JSON 转换为可读实体字段。"""
        workflow = WorkflowDefinition.from_mapping({
            "id": 3,
            "name": "审批流程",
            "description": "发布前审批",
            "mode": "graph",
            "config_json": '{"nodes": [], "edges": []}',
            "is_active": 1,
        })
        self.assertEqual(workflow.id, 3)
        self.assertEqual(workflow.config, {"nodes": [], "edges": []})
        self.assertTrue(workflow.is_active)

    def test_resume_context_distinguishes_runtime_fields(self) -> None:
        """审批恢复字段应通过属性访问，不再依赖字符串键。"""
        context = WorkflowResumeContext.from_value({
            "resume_node_id": "agent-next",
            "current_input": "审批内容",
            "step_counter": 4,
            "approval_step_id": 91,
        })
        self.assertEqual(context.resume_node_id, "agent-next")
        self.assertEqual(context.current_input, "审批内容")
        self.assertEqual(context.step_counter, 4)
        self.assertEqual(context.approval_step_id, 91)

    def test_run_requires_immutable_config_snapshot(self) -> None:
        """运行实体缺少配置快照时应拒绝继续执行。"""
        run = WorkflowRun(
            id=7,
            workflow_id=3,
            status="running",
            input_text="开始",
        )
        with self.assertRaisesRegex(ValueError, "缺少工作流配置快照"):
            run.require_workflow_config()

    async def test_repository_returns_workflow_run_entity(self) -> None:
        """Repository 应返回 WorkflowRun，而不是数据库字典。"""
        row = {
            "id": 7,
            "workflow_id": 3,
            "status": "waiting_approval",
            "input_text": "开始",
            "workflow_config_json": '{"nodes": [], "edges": []}',
            "context_json": '{"resume_node_id": "agent-next"}',
        }
        with (
            patch.object(workflow_repository, "fetch_one", AsyncMock(return_value=row)),
            patch.object(workflow_repository, "fetch_all", AsyncMock(return_value=[])),
        ):
            run = await workflow_repository.find_workflow_run_entity(7, 2)
        self.assertIsInstance(run, WorkflowRun)
        assert run is not None
        self.assertEqual(run.resume_context.resume_node_id, "agent-next")
        self.assertEqual(run.workflow_config, {"nodes": [], "edges": []})


if __name__ == "__main__":
    unittest.main()
