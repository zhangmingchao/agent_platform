"""聊天运行实体的字段转换测试。"""

import unittest
from typing import get_type_hints

from langgraph.graph.state import CompiledStateGraph

from backend.core.agent_factory import create_agent_instance
from backend.models.agent import Agent
from backend.models.chat import (
    ChatSession,
    PreparedChatRun,
    RuntimeFile,
)
from backend.services.chat_service import prepare_chat_run


class ChatModelTests(unittest.TestCase):
    def test_session_and_agent_rows_are_converted_to_entities(self) -> None:
        """数据库字典进入聊天业务层后应转换为可属性访问的实体。"""
        session = ChatSession.from_mapping({"id": "10", "agent_id": 20})
        agent = Agent.from_mapping({
            "id": 20,
            "system_prompt": "你是助手",
            "prompt_variables": {"language": "zh-CN"},
            "output_schema": {"type": "object"},
            "model_config_id": 3,
            "iteration_count": 8,
        })

        self.assertEqual(session.id, 10)
        self.assertEqual(session.agent_id, 20)
        self.assertEqual(agent.id, 20)
        self.assertEqual(agent.prompt_variables["language"], "zh-CN")
        self.assertEqual(agent.iteration_count, 8)

    def test_runtime_file_attachment_does_not_expose_storage_path(self) -> None:
        """文件实体转附件时不能把宿主机存储路径发送给模型。"""
        runtime_file = RuntimeFile.from_mapping({
            "id": "file-1",
            "file_name": "销售数据.xlsx",
            "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "size_bytes": 1024,
            "storage_path": "/private/data/file-1.xlsx",
        })

        attachment = runtime_file.to_attachment()
        self.assertEqual(attachment["id"], "file-1")
        self.assertNotIn("storage_path", attachment)

    def test_prepare_chat_run_declares_entity_return_type(self) -> None:
        """聊天准备函数应明确声明返回 PreparedChatRun，而不是普通 dict。"""
        self.assertIs(prepare_chat_run.__annotations__["return"], PreparedChatRun)

    def test_agent_factory_declares_compiled_graph_return_type(self) -> None:
        """Agent 工厂应明确声明返回 LangGraph 编译执行器。"""
        self.assertIs(get_type_hints(create_agent_instance)["return"], CompiledStateGraph)


if __name__ == "__main__":
    unittest.main()
