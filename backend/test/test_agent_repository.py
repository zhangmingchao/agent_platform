"""Agent Repository 与领域实体测试。"""

import unittest
from typing import Optional, get_type_hints
from unittest.mock import AsyncMock, patch

from backend.models.agent import Agent
from backend.repositories import agent_repository
from backend.services.agent_service import get_agent


class AgentRepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_repository_returns_agent_entity(self):
        """Repository 应完成数据库记录到 Agent 实体的转换。"""
        row = {
            "id": 7,
            "user_id": 2,
            "name": "数据分析 Agent",
            "description": "分析业务数据",
            "system_prompt": "你是数据分析师",
            "prompt_variables": '{"language":"zh-CN"}',
            "output_schema": '{"type":"object"}',
            "model": "deepseek-chat",
            "model_config_id": None,
            "temperature": 0.3,
            "iteration_count": 6,
        }
        with (
            patch.object(agent_repository, "fetch_one", AsyncMock(return_value=row)),
            patch.object(
                agent_repository,
                "fetch_all",
                AsyncMock(side_effect=[[{"id": 1, "name": "excel"}], [{"id": 3, "name": "weather"}]]),
            ),
        ):
            agent = await agent_repository.find_agent_by_id(7, 2)

        self.assertIsInstance(agent, Agent)
        self.assertEqual(agent.id, 7)
        self.assertEqual(agent.prompt_variables["language"], "zh-CN")
        self.assertEqual(agent.skills[0]["name"], "excel")
        self.assertEqual(agent.mcps[0]["name"], "weather")

    def test_service_declares_agent_entity_return_type(self):
        """公共 get_agent 方法不应再声明返回无结构字典。"""
        self.assertEqual(get_type_hints(get_agent)["return"], Optional[Agent])


if __name__ == "__main__":
    unittest.main()
