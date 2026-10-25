"""BI 工具统一通过插件安装版本和容器任务执行，禁止回到宿主子进程入口。"""

import json
import unittest
from unittest.mock import AsyncMock, patch

from backend.core.agent_factory import build_all_tools
from backend.core.plugin_tools import build_plugin_tools
from backend.models.plugin import PluginSettings
from backend.plugins.registry import get_manifest
from backend.plugins.packages import public_tool_name
from backend.runtime.models import RuntimeContext
from backend.services.plugin_service import RuntimePlugin, RuntimePlugins


class BiCliToolTests(unittest.IsolatedAsyncioTestCase):
    """验证绑定才能注册、参数 Schema 与共享容器执行适配。"""

    async def test_environment_never_registers_unbound_bi_tool(self) -> None:
        """即使旧 BI 环境开关存在，未绑定 Agent 不应获得全局宿主工具。"""
        with patch("backend.services.plugin_service.load_runtime_plugins", AsyncMock(return_value=RuntimePlugins())), patch.dict("os.environ", {"BI_CLI_ENABLED": "true"}):
            tools = await build_all_tools([], [], RuntimeContext(user_id=7))
        self.assertNotIn("BiCli", [tool.name for tool in tools])
        self.assertNotIn(public_tool_name("bi-metadata", "BiCli"), [tool.name for tool in tools])

    async def test_builtin_bi_uses_process_task_and_user_snapshot(self) -> None:
        """内置 BI 和上传插件使用同一进程适配器，Token 仅注入当前执行快照。"""
        context = RuntimeContext(user_id=7)
        manifest = get_manifest("bi-metadata")
        settings = PluginSettings(values={"base_url": "https://example.test"}, secrets={"token": "fixture-token"})
        with patch("backend.services.plugin_package_service.execute_process_plugin", AsyncMock(return_value='{"ok":true,"data":{},"error":null}')) as execute, patch("backend.core.plugin_tools.record_plugin_call", AsyncMock()):
            tool = build_plugin_tools(context, [RuntimePlugin(plugin_id=manifest.id, manifest=manifest, settings=settings)])[0]
            result = await tool.ainvoke({"arguments": ["metadata", "events", "list", "--product-key", "fixture"]})
        self.assertTrue(json.loads(result)["ok"])
        self.assertEqual(tool.name, "plugin__bi_metadata__BiCli")
        self.assertTrue(tool.metadata["plugin_process"])
        self.assertEqual(execute.await_args.args[0].user_id, 7)
        self.assertEqual(execute.await_args.args[-1], {"token": "fixture-token"})
        self.assertEqual(execute.await_args.args[1].executor, "python-process")


if __name__ == "__main__":
    unittest.main()
