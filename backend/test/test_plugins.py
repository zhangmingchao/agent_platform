"""统一容器插件的配置、安装就绪门禁、Skill 和用户绑定行为回归。"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from backend.core.agent_factory import build_all_tools
from backend.core.plugin_tools import build_plugin_tools
from backend.core.tools import build_skill_tools
from backend.database import close_pool, execute, fetch_one
from backend.models.plugin import PluginConfigInput, PluginDebugInput, PluginField, PluginFieldOption, PluginSettings
from backend.plugins.configuration import validate_fields
from backend.plugins.examples import export_builtin
from backend.plugins.registry import get_manifest
from backend.plugins.packages import public_tool_name
from backend.routers.plugins import router
from backend.runtime.models import RuntimeContext
from backend.security import decrypt_plugin_token, encrypt_plugin_token
from backend.services import plugin_service as service
from backend.services.agent_service import create_agent


class PluginUnitTests(unittest.IsolatedAsyncioTestCase):
    """不连接外部服务的凭据、配置、安装门禁与工具工厂测试。"""

    def test_secrets_encrypted_and_authenticated(self) -> None:
        """随机 nonce 生成不同密文，错误主密钥不能解密。"""
        secret = 'test-token-"quoted"'
        first = encrypt_plugin_token(secret)
        self.assertNotIn(secret, first)
        self.assertNotEqual(first, encrypt_plugin_token(secret))
        self.assertEqual(decrypt_plugin_token(first), secret)
        with patch("backend.security.MODEL_API_KEY_ENCRYPTION_KEY", "A" * 43), self.assertRaises(ValueError):
            decrypt_plugin_token(first)

    def test_invalid_urls_and_numeric_bounds(self) -> None:
        """通用配置根据 BI 声明校验地址和数值范围，不再接受旧扁平请求。"""
        manifest = get_manifest("bi-metadata")
        for values in ({"base_url": "file:///etc/passwd"}, {"base_url": "http://user:pass@host"}, {"base_url": "https://host?token=x"}, {"timeout_seconds": 1000}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                validate_fields(manifest.fields, PluginConfigInput(values=values), PluginSettings(), complete=False)
        with self.assertRaises(ValidationError):
            PluginConfigInput(base_url="https://legacy.test")

    def test_skill_reads_installed_version_and_expands_names(self) -> None:
        """Skill 从用户安装目录读取，工具占位符替换为命名空间名称。"""
        from backend.plugins.packages import check_package
        with tempfile.TemporaryDirectory() as directory, patch("backend.plugins.storage.RUNTIME_DATA_DIR", directory):
            root = Path(directory) / "users/7/workspaces/plugins/bi-metadata/1.0.0/package"
            check_package(export_builtin("bi-metadata"), root)
            tools = build_skill_tools([{"id": 9, "name": "bi-metadata", "description": "old"}], ["bi-metadata"], {"bi-metadata": get_manifest("bi-metadata")}, 7)
            content = tools[0].invoke({"command": "bi-metadata"})
            self.assertIn("plugin__bi_metadata__BiCli", content)
            self.assertNotIn("{{tool:", content)
            self.assertIn("error", json.loads(tools[1].invoke({"skill_name": "bi-metadata", "path": "../config.py"})))

    def test_generic_field_types_defaults_and_required_values(self) -> None:
        """五种配置控件保留合法 0/False，拒绝未知字段或错误类型。"""
        fields = [PluginField(key="name", label="名称", kind="string", required=True, max_length=5),
                  PluginField(key="count", label="数量", kind="integer", default=0, minimum=0, maximum=5),
                  PluginField(key="active", label="开关", kind="boolean", default=False),
                  PluginField(key="mode", label="模式", kind="select", default="a", options=[PluginFieldOption(label="A", value="a")])]
        result = validate_fields(fields, PluginConfigInput(values={"name": " 测试 "}), PluginSettings(), complete=True)
        self.assertEqual(result.values, {"name": "测试", "count": 0, "active": False, "mode": "a"})
        for invalid in ({"name": " "}, {"name": "123456"}, {"count": True}, {"count": 6}, {"active": 1}, {"mode": "b"}, {"other": "x"}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_fields(fields, PluginConfigInput(values=invalid), result, complete=True)

    def test_multiple_secrets_are_independent(self) -> None:
        """多个密钥独立保留、清除，不回显到实体 repr 或公开序列化。"""
        fields = [PluginField(key="access_key", label="访问密钥", kind="secret"), PluginField(key="sign_key", label="签名密钥", kind="secret")]
        previous = PluginSettings(secrets={"access_key": "first", "sign_key": "second"})
        result = validate_fields(fields, PluginConfigInput(secrets={"sign_key": ""}, clear_secrets=["access_key"]), previous, complete=False)
        self.assertEqual(result.secrets, {"access_key": "", "sign_key": "second"})
        self.assertNotIn("second", repr(result))
        self.assertNotIn("secrets", result.model_dump())
        with self.assertRaises(ValueError):
            validate_fields(fields, PluginConfigInput(values={"access_key": "wrong"}), previous, complete=False)

    async def test_uninstalled_builtin_cannot_execute_or_enable(self) -> None:
        """配置或目录存在不能替代安装状态，未安装禁止启用、保存和调试。"""
        with patch.object(service, "list_packages", AsyncMock(return_value=[])), patch.object(service, "fetch_one", AsyncMock(return_value=None)):
            view = await service.get_plugin(7, "json-tools")
        self.assertEqual(view.package_status, "not_installed")
        self.assertFalse(view.installed)
        self.assertFalse(view.enabled)
        with patch.object(service, "list_packages", AsyncMock(return_value=[])), patch.object(service, "installed_package", AsyncMock(side_effect=ValueError("missing"))):
            for call in (service.toggle_plugin(7, "json-tools", True, 0), service.save_plugin(7, "json-tools", PluginConfigInput()), service.diagnose_plugin(7, "json-tools", PluginDebugInput(input={"content": "{}"}))):
                with self.assertRaises(HTTPException) as error:
                    await call
                self.assertEqual(error.exception.status_code, 409)

    async def test_builtin_tool_is_always_process_adapter(self) -> None:
        """内置 JSON 不在宿主处理文本，工具桥接只提交用户容器执行任务。"""
        entry = service.RuntimePlugin(plugin_id="json-tools", manifest=get_manifest("json-tools"), settings=PluginSettings())
        with patch("backend.services.plugin_package_service.execute_process_plugin", AsyncMock(return_value='{"ok":true,"data":{"formatted":"{}"},"error":null}')) as execute, patch("backend.core.plugin_tools.record_plugin_call", AsyncMock()):
            tool = build_plugin_tools(RuntimeContext(user_id=7), [entry])[0]
            await tool.ainvoke({"content": "{}"})
        self.assertEqual(tool.name, "plugin__json_tools__JsonFormat")
        execute.assert_awaited_once()
        self.assertEqual(execute.await_args.args[1].source, "builtin")

    async def test_duplicate_tool_names_fail_clearly(self) -> None:
        """MCP 与插件同名时明确失败，避免错误分发。"""
        entry = service.RuntimePlugin(plugin_id="json-tools", manifest=get_manifest("json-tools"), settings=PluginSettings())
        duplicate = build_plugin_tools(RuntimeContext(user_id=7), [entry])
        with patch.object(service, "load_runtime_plugins", AsyncMock(return_value=service.RuntimePlugins(entries=[entry]))), patch("backend.core.agent_factory.build_mcp_langchain_tools", AsyncMock(return_value=duplicate)):
            with self.assertRaisesRegex(ValueError, "plugin__json_tools__JsonFormat"):
                await build_all_tools([], [], RuntimeContext(user_id=7, agent_id=8))

    def test_legacy_rows_do_not_restore_credentials(self) -> None:
        """历史 BI 专用列不再恢复为当前配置或凭据。"""
        stored = service.StoredPlugin.model_validate({"user_id":7,"plugin_id":"bi-metadata","values_json":None,"secrets_json":None,"base_url":"https://legacy.test","encrypted_token":"old","enabled":True,"revision":1,"health_status":"untested","health_message":"","updated_at":datetime.now()})
        self.assertEqual(stored.values, {})
        self.assertEqual(stored.encrypted_secrets, {})

    def test_redaction_preserves_json(self) -> None:
        """转义后的凭据仍应脱敏。"""
        secret = 'token-"special"'
        result = service.redact_plugin_output(json.dumps({"data": [secret]}), secrets=[secret])
        self.assertEqual(json.loads(result)["data"], ["[已隐藏]"])

    async def test_plugin_routes_require_authentication(self) -> None:
        """目录和安装接口均不可匿名调用。"""
        app = FastAPI(); app.include_router(router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
            self.assertEqual((await client.get("/api/plugins")).status_code, 401)
            self.assertEqual((await client.post("/api/plugins/json-tools/install")).status_code, 401)


@unittest.skipUnless(os.getenv("PLUGIN_DB_TEST") == "1", "设置 PLUGIN_DB_TEST=1 运行临时用户数据库测试")
class PluginDatabaseTests(unittest.IsolatedAsyncioTestCase):
    """验证配置和绑定事务；ready 记录仅用于状态测试，真实执行由 Docker 集成测试覆盖。"""

    async def test_lifecycle_and_isolation(self) -> None:
        """安装状态、密钥生命周期、乐观锁、绑定、卸载前门禁和跨用户不可见。"""
        users: list[int] = []
        try:
            for _ in range(2):
                users.append(await execute("INSERT INTO users (username,password,created_at) VALUES (%s,%s,UTC_TIMESTAMP())", ("plugin-test-" + uuid4().hex[:16], "disabled-test")))
            first, second = users
            for pid in ("json-tools", "bi-metadata"):
                manifest = get_manifest(pid)
                await execute("INSERT INTO plugin_packages (user_id,plugin_id,version,digest,manifest_json,status,active,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,'ready',1,UTC_TIMESTAMP(),UTC_TIMESTAMP())", (first,pid,manifest.version,"f"*64,manifest.model_dump_json()))
            data = PluginConfigInput(values={"base_url":"https://example.test"}, secrets={"token":"fixture-secret"})
            saved = await service.save_plugin(first,"bi-metadata",data)
            self.assertNotIn("fixture-secret",saved.model_dump_json())
            row = await fetch_one("SELECT secrets_json FROM plugin_configs WHERE user_id=%s AND plugin_id='bi-metadata'",(first,))
            self.assertNotIn("fixture-secret",row["secrets_json"])
            self.assertFalse((await service.get_plugin(second,"bi-metadata")).installed)
            with self.assertRaises(HTTPException):
                await service.save_plugin(first,"bi-metadata",data)
            saved = await service.save_plugin(first,"bi-metadata",PluginConfigInput(secrets={"token":""},revision=saved.revision))
            self.assertEqual((await service._stored(first,"bi-metadata")).settings().secrets["token"],"fixture-secret")
            saved = await service.toggle_plugin(first,"bi-metadata",True,saved.revision)
            agent = await create_agent(first,{"name":"fixture","plugin_ids":["bi-metadata"]})
            snapshot = await service.load_runtime_plugins(RuntimeContext(user_id=first,agent_id=agent.id))
            self.assertEqual(snapshot.plugin_ids,["bi-metadata"])
            self.assertEqual(snapshot.entries[0].manifest.executor,"python-process")
            self.assertEqual((await service.load_runtime_plugins(RuntimeContext(user_id=second,agent_id=agent.id))).entries,[])
            with self.assertRaises(HTTPException):
                await service.remove_plugin(first,"bi-metadata",saved.revision)
            saved = await service.toggle_plugin(first,"bi-metadata",False,saved.revision)
            self.assertEqual((await service.load_runtime_plugins(RuntimeContext(user_id=first,agent_id=agent.id))).entries,[])
            await service.bind_agent_plugins(agent.id,first,[])
            saved = await service.save_plugin(first,"bi-metadata",PluginConfigInput(clear_secrets=["token"],revision=saved.revision))
            self.assertEqual(saved.configured_secrets,[])
            await service.remove_plugin(first,"bi-metadata",saved.revision)
            self.assertTrue((await service.get_plugin(first,"bi-metadata")).installed)
            self.assertNotIn("fixture-secret",json.dumps([item.model_dump(mode="json") for item in await service.list_activity(first,"bi-metadata")]))
            await service.toggle_plugin(first,"json-tools",True,0)
            await execute("DELETE FROM plugin_packages WHERE user_id=%s AND plugin_id='json-tools'",(first,))
            self.assertFalse((await service.get_plugin(first,"json-tools")).enabled)
        finally:
            for user_id in users:
                await execute("DELETE FROM agents WHERE user_id=%s",(user_id,))
                await execute("DELETE FROM users WHERE id=%s",(user_id,))
            await close_pool()


if __name__ == "__main__":
    unittest.main()
