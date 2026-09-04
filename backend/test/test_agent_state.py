import unittest
from typing import get_type_hints
from unittest.mock import AsyncMock

from langchain_core.messages import HumanMessage

from backend.core.agent_state import (
    AgentPlatformState,
    build_agent_state,
    update_agent_checkpoint_state,
)


class AgentPlatformStateTests(unittest.IsolatedAsyncioTestCase):
    def test_custom_state_keeps_required_react_fields(self):
        """自定义 State 必须保留 create_react_agent 要求的内置字段。"""
        hints = get_type_hints(AgentPlatformState)
        self.assertIn("messages", hints)
        self.assertIn("remaining_steps", hints)
        self.assertIn("runtime_file_ids", hints)
        self.assertIn("structured_result", hints)

    def test_build_agent_state_normalizes_business_context(self):
        """文件和 Skill 标识应去空、去重，并保留输入顺序。"""
        message = HumanMessage(content="分析文件")
        state = build_agent_state(
            [message],
            runtime_file_ids=["file-1", "file-1", " file-2 "],
            available_skills=["Excel分析", "Excel分析"],
            current_input="分析文件",
            current_node_id="chat",
        )
        self.assertEqual(state["messages"], [message])
        self.assertEqual(state["runtime_file_ids"], ["file-1", "file-2"])
        self.assertEqual(state["available_skills"], ["Excel分析"])
        self.assertEqual(state["loaded_skills"], [])
        self.assertEqual(state["current_node_id"], "chat")

    async def test_checkpoint_update_is_non_blocking_on_failure(self):
        """Checkpoint 写入失败时不得破坏现有业务响应。"""
        executor = AsyncMock()
        executor.aupdate_state.side_effect = RuntimeError("checkpoint unavailable")
        updated = await update_agent_checkpoint_state(
            executor,
            "session_1_message_2",
            {"structured_result": {"ok": True}},
        )
        self.assertFalse(updated)


if __name__ == "__main__":
    unittest.main()

