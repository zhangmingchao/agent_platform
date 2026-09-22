"""MCP 配置实体和完整操作超时测试。"""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from backend.mcp_client import McpClient, McpOperationTimeoutError
from backend.models.mcp import McpConfig, McpConfigInput
from backend.routers.mcp_configs import McpConfigPayload
from backend.services.mcp_config_service import (
    create_mcp_config,
    get_mcp_config,
    list_mcp_configs,
)


class McpConfigTests(unittest.IsolatedAsyncioTestCase):
    """验证 MCP 超时范围和业务服务的实体返回值。"""

    def test_timeout_defaults_to_30_and_is_limited_to_60(self) -> None:
        """接口默认使用 30 秒，并拒绝超过 60 秒的配置。"""
        payload = McpConfigPayload()
        self.assertEqual(payload.timeout_seconds, 30)
        with self.assertRaises(ValidationError):
            McpConfigPayload(timeout_seconds=61)

    async def test_list_and_get_return_mcp_entities(self) -> None:
        """数据库记录进入业务层后必须转换为 MCP 配置实体。"""
        row = {
            "id": 3,
            "user_id": 7,
            "name": "天气服务",
            "base_url": "http://127.0.0.1:18888",
            "endpoint": "/mcp",
            "description": "查询天气",
            "timeout_seconds": 45,
        }
        with (
            patch(
                "backend.services.mcp_config_service.fetch_all",
                AsyncMock(return_value=[row]),
            ),
            patch(
                "backend.services.mcp_config_service.fetch_one",
                AsyncMock(return_value=row),
            ),
        ):
            configs = await list_mcp_configs(7)
            config = await get_mcp_config(3, 7)

        self.assertIsInstance(configs[0], McpConfig)
        self.assertIsInstance(config, McpConfig)
        self.assertEqual(config.timeout_seconds, 45)

    async def test_create_persists_configured_timeout(self) -> None:
        """创建服务应持久化输入实体中的 MCP 整体超时。"""
        data = McpConfigInput(
            name="天气服务",
            base_url="http://127.0.0.1:18888",
            endpoint="/mcp",
            description="查询天气",
            timeout_seconds=50,
        )
        created = McpConfig(
            id=9,
            user_id=7,
            name=data.name,
            base_url=data.base_url,
            endpoint=data.endpoint,
            description=data.description,
            timeout_seconds=data.timeout_seconds,
        )
        execute = AsyncMock(return_value=9)
        with (
            patch("backend.services.mcp_config_service.execute", execute),
            patch(
                "backend.services.mcp_config_service.get_mcp_config",
                AsyncMock(return_value=created),
            ),
        ):
            result = await create_mcp_config(7, data)

        self.assertIs(result, created)
        self.assertIn(50, execute.await_args.args[1])


class McpClientTimeoutTests(unittest.IsolatedAsyncioTestCase):
    """验证 MCP 超时覆盖整个公开操作。"""

    async def test_operation_timeout_has_specific_exception(self) -> None:
        """整体操作超过配置时限后应抛出包含操作信息的专用异常。"""
        client = McpClient("http://127.0.0.1:18888", timeout_seconds=1)

        async def slow_action() -> str:
            """模拟迟迟没有完成的 MCP 操作。"""
            await asyncio.sleep(2)
            return "done"

        with self.assertRaises(McpOperationTimeoutError) as raised:
            await client._run_operation("测试调用", slow_action)

        self.assertEqual(raised.exception.timeout_seconds, 1)
        self.assertEqual(raised.exception.operation, "测试调用")


if __name__ == "__main__":
    unittest.main()
