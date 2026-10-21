"""插件回归：凭据、固定执行器、技能合并、用户隔离及配置生命周期。"""

import asyncio
import json
import os
import unittest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from backend.auth import get_current_user
from backend.bi_cli.models import BiCliSettings
from backend.core.agent_factory import build_all_tools
from backend.core.bi_cli_tool import BiCliProcessResult, _execute_bi_cli_process, build_bi_cli_tools
from backend.core.tools import build_skill_tools
from backend.database import close_pool, execute, fetch_one
from backend.models.plugin import PluginConfigInput, PluginDebugInput, PluginField, PluginFieldOption, PluginManifest, PluginProbeInput, PluginSettings
from backend.plugins.configuration import validate_fields
from backend.plugins.executors import get_executor
from backend.plugins import registry
from backend.plugins.registry import read_plugin_skill
from backend.routers.plugins import router
from backend.runtime.models import RuntimeContext
from backend.security import decrypt_plugin_token, encrypt_plugin_token
from backend.services import plugin_service as service
from backend.services.agent_service import create_agent, get_agent


class PluginUnitTests(unittest.IsolatedAsyncioTestCase):
    """无需外部服务的插件协议、配置与工具加载测试。"""

    def test_secrets_encrypted_and_authenticated(self) -> None:
        """随机 nonce 生成不同密文；错误主密钥不能解密。"""
        secret = 'test-token-"quoted"'
        first = encrypt_plugin_token(secret)
        self.assertNotIn(secret, first)
        self.assertNotEqual(first, encrypt_plugin_token(secret))
        self.assertEqual(decrypt_plugin_token(first), secret)
        with patch("backend.security.MODEL_API_KEY_ENCRYPTION_KEY", "A" * 43):
            with self.assertRaises(ValueError):
                decrypt_plugin_token(first)

    def test_invalid_urls_and_numeric_bounds(self) -> None:
        """配置地址禁止携带凭据，时间与输出大小采用有限范围。"""
        for address in ("file:///etc/passwd", "http://user:pass@host", "https://host?token=x", "https://host:bad"):
            with self.assertRaises(ValidationError):
                PluginConfigInput(base_url=address)
        with self.assertRaises(ValidationError):
            PluginConfigInput(timeout_seconds=1000)

    def test_skill_merges_and_path_is_allowlisted(self) -> None:
        """同名数据库 Skill 被插件版本替代；插件不能读取任意文件。"""
        tools = build_skill_tools([{"id": 9, "name": "bi-metadata", "description": "old"}], ["bi-metadata"])
        self.assertEqual([tool.name for tool in tools], ["Skill", "SkillFile"])
        content = tools[0].invoke({"command": "bi-metadata"})
        self.assertIn("BiCli", content)
        with self.assertRaises(ValueError):
            read_plugin_skill("bi-metadata", "../../config.py")
        self.assertIn("error", json.loads(tools[1].invoke({"skill_name": "bi-metadata", "path": "../config.py"})))

    def test_generic_field_types_defaults_and_required_values(self) -> None:
        """声明驱动校验支持五种控件，合法的 0/False 不能被当作空值。"""
        fields = [PluginField(key="name", label="名称", kind="string", required=True, max_length=5),
                  PluginField(key="count", label="数量", kind="integer", required=True, default=0, minimum=0, maximum=5),
                  PluginField(key="active", label="开关", kind="boolean", required=True, default=False),
                  PluginField(key="mode", label="模式", kind="select", default="a", options=[PluginFieldOption(label="模式 A", value="a")])]
        result = validate_fields(fields, PluginConfigInput(values={"name": " 测试 "}), PluginSettings(), complete=True)
        self.assertEqual(result.values, {"name": "测试", "count": 0, "active": False, "mode": "a"})
        for invalid in ({"name": "      "}, {"name": "123456"}, {"count": True}, {"count": 6}, {"count": ""}, {"active": 1}, {"active": ""}, {"mode": "b"}, {"undeclared": "value"}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_fields(fields, PluginConfigInput(values=invalid), result, complete=True)

    def test_multiple_secrets_are_independent(self) -> None:
        """每个密钥分别保留、替换和清除，并拒绝错误通道、冲突和超长输入。"""
        fields = [PluginField(key="access_key", label="访问密钥", kind="secret", max_length=10),
                  PluginField(key="sign_key", label="签名密钥", kind="secret"),
                  PluginField(key="name", label="名称", kind="string")]
        previous = PluginSettings(secrets={"access_key": "first", "sign_key": "second"})
        result = validate_fields(fields, PluginConfigInput(secrets={"sign_key": ""}, clear_secrets=["access_key"]), previous, complete=False)
        self.assertEqual(result.secrets, {"access_key": "", "sign_key": "second"})
        self.assertNotIn("second", repr(result))
        self.assertNotIn("secrets", result.model_dump())
        for invalid in (PluginConfigInput(values={"access_key": "wrong"}), PluginConfigInput(secrets={"name": "wrong"}),
                        PluginConfigInput(secrets={"access_key": "new"}, clear_secrets=["access_key"]),
                        PluginConfigInput(secrets={"access_key": "a" * 11}), PluginConfigInput(clear_secrets=["unknown"])):
            with self.assertRaises(ValueError):
                validate_fields(fields, invalid, previous, complete=False)

    def test_generic_url_field_and_optional_configuration(self) -> None:
        """任意命名的地址字段使用公共校验；没有配置项的插件也能返回实体。"""
        fields = [PluginField(key="endpoint", label="端点", kind="string", format="url")]
        valid = validate_fields(fields, PluginConfigInput(values={"endpoint": "https://example.test/"}), PluginSettings(), complete=True)
        self.assertEqual(valid.values["endpoint"], "https://example.test")
        with self.assertRaises(ValueError):
            validate_fields(fields, PluginConfigInput(values={"endpoint": "https://user:pass@example.test"}), PluginSettings(), complete=False)
        self.assertEqual(validate_fields([], PluginConfigInput(), PluginSettings(), complete=True).values, {})

    async def test_local_executor_has_real_schema_and_execution(self) -> None:
        """无配置执行器真实处理 JSON，拒绝其他工具、额外参数及无效 JSON。"""
        executor = get_executor("local-json")
        definition = executor.definitions()[0]
        self.assertEqual(definition.name, "JsonFormat")
        self.assertIn("content", definition.parameters["required"])
        result = json.loads(await executor.debug(PluginSettings(), PluginDebugInput(tool_name=definition.name, input=definition.example_input)))
        self.assertTrue(result["ok"])
        failed = json.loads(await executor.debug(PluginSettings(), PluginDebugInput(input={"content": "not-json"})))
        self.assertEqual(failed["error"]["code"], "INVALID_JSON")
        for request in (PluginDebugInput(tool_name="BiCli", input={"content": "{}"}), PluginDebugInput(input={"content": "{}", "shell": "pwd"})):
            with self.assertRaises(ValueError):
                await executor.debug(PluginSettings(), request)

    async def test_managed_user_does_not_get_global_cli(self) -> None:
        """未绑定的用户配置阻止环境变量向所有 Agent 注入工具。"""
        with (
            patch.object(service, "load_runtime_plugins", AsyncMock(return_value=service.RuntimePlugins(managed_executors=["bi-cli"]))),
            patch("backend.core.bi_cli_tool.BI_CLI_ENABLED", True),
        ):
            tools = await build_all_tools([], [], RuntimeContext(user_id=7, agent_id=8))
        self.assertNotIn("BiCli", [tool.name for tool in tools])

    async def test_bound_plugin_gets_tool_and_skill_even_without_env_flag(self) -> None:
        """插件配置不依赖全局开关，同时注入统一技能入口。"""
        settings = PluginSettings(values={"base_url": "https://example.test"}, secrets={"token": "test"})
        with (
            patch.object(service, "load_runtime_plugins", AsyncMock(return_value=service.RuntimePlugins(entries=[service.RuntimePlugin(plugin_id="bi-metadata", settings=settings)], managed_executors=["bi-cli"]))),
            patch("backend.core.bi_cli_tool.BI_CLI_ENABLED", False),
        ):
            tools = await build_all_tools([], [], RuntimeContext(user_id=7, agent_id=8))
        self.assertTrue({"BiCli", "Skill", "SkillFile"}.issubset({tool.name for tool in tools}))

    async def test_duplicate_tool_names_fail_clearly(self) -> None:
        """MCP 与插件工具名称冲突时阻止构建，避免错误分发。"""
        settings = BiCliSettings(base_url="https://example.test", access_token="test")
        duplicate = build_bi_cli_tools(RuntimeContext(user_id=7), settings)
        with (
            patch.object(service, "load_runtime_plugins", AsyncMock(return_value=service.RuntimePlugins(entries=[service.RuntimePlugin(plugin_id="bi-metadata", settings=PluginSettings(values={"base_url": settings.base_url}, secrets={"token": settings.access_token}))], managed_executors=["bi-cli"]))),
            patch("backend.core.agent_factory.build_mcp_langchain_tools", AsyncMock(return_value=duplicate)),
        ):
            with self.assertRaisesRegex(ValueError, "BiCli"):
                await build_all_tools([], [], RuntimeContext(user_id=7, agent_id=8))

    async def test_each_child_gets_own_environment(self) -> None:
        """不同用户的 Token 只注入对应子进程，不污染共享环境。"""
        process = AsyncMock()
        process.returncode = 0
        process.communicate.return_value = (b'{"ok":true}', b"")
        previous = os.environ.get("BI_DOCKER_TOKEN")
        with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=process)) as spawn:
            for token in ("user-one", "user-two"):
                await _execute_bi_cli_process(["metadata"], "request", BiCliSettings("https://example.test", token))
        self.assertEqual([call.kwargs["env"]["BI_DOCKER_TOKEN"] for call in spawn.call_args_list], ["user-one", "user-two"])
        self.assertEqual(os.environ.get("BI_DOCKER_TOKEN"), previous)
        self.assertNotIn("shell", spawn.call_args.kwargs)

    def test_redaction_keeps_json_and_removes_escaped_secrets(self) -> None:
        """JSON 中转义后的 Token 仍应脱敏，防止上下游错误回显凭据。"""
        secret = 'token-"special"'
        result = service.redact_plugin_output(json.dumps({"data": [secret], "message": "https://example.test " + secret}), secret, "https://example.test")
        self.assertNotIn(secret, json.loads(result)["message"])
        self.assertEqual(json.loads(result)["data"], ["[已隐藏]"])

    async def test_plugin_routes_require_authentication(self) -> None:
        """插件接口不能匿名获取配置。"""
        app = FastAPI()
        app.include_router(router)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/plugins")
        self.assertEqual(response.status_code, 401)


@unittest.skipUnless(os.getenv("PLUGIN_DB_TEST") == "1", "设置 PLUGIN_DB_TEST=1 运行临时用户数据库集成测试")
class PluginDatabaseTests(unittest.IsolatedAsyncioTestCase):
    """连接项目数据库验证事务，全部业务记录使用临时用户并在结束后清理。"""

    async def test_lifecycle_and_isolation(self) -> None:
        """覆盖保存、版本冲突、用户隔离、真实固定 CLI 子进程、绑定和停用。"""
        users: list[int] = []
        headers: list[str] = []
        status = [200]

        async def upstream(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            """通过 reader 接收测试请求，writer 返回模拟 BI 响应，不访问业务服务。"""
            request = (await reader.readuntil(b"\r\n\r\n")).decode()
            headers.append(request)
            payload = json.dumps({"code": status[0], "data": {"list": [{"name": "fixture_event"}], "total": 1}, "message": "fixture"}).encode()
            writer.write(f"HTTP/1.1 {status[0]} Test\r\nContent-Type: application/json\r\nContent-Length: {len(payload)}\r\nConnection: close\r\n\r\n".encode() + payload)
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(upstream, "127.0.0.1", 0)
        address = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        try:
            for _ in range(2):
                users.append(await execute("INSERT INTO users (username,password,created_at) VALUES (%s,%s,UTC_TIMESTAMP())", ("plugin-test-" + uuid4().hex[:20], "test-disabled-login")))
            first, second = users
            data = PluginConfigInput(base_url=address, token="temporary-test-token")
            plugin = await service.save_plugin(first, "bi-metadata", data)
            self.assertNotIn("temporary-test-token", plugin.model_dump_json())
            row = await fetch_one("SELECT encrypted_token,secrets_json FROM plugin_configs WHERE user_id=%s", (first,))
            self.assertEqual(row["encrypted_token"], "")
            self.assertNotIn("temporary-test-token", row["secrets_json"])
            self.assertFalse((await service.get_plugin(second, "bi-metadata")).installed)
            with self.assertRaises(HTTPException) as conflict:
                await service.save_plugin(first, "bi-metadata", data)
            self.assertEqual(conflict.exception.status_code, 409)
            plugin = await service.save_plugin(first, "bi-metadata", PluginConfigInput(base_url=address, revision=plugin.revision))
            self.assertEqual(plugin.configured_secrets, ["token"])
            app = FastAPI()
            app.include_router(router)

            async def current_user() -> dict:
                """测试认证上下文固定到第一个临时用户。"""
                return {"user_id": first}

            app.dependency_overrides[get_current_user] = current_user
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/plugins/bi-metadata/test", json={"product_key": "fixture-product"})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json()["ok"])
                for args in (["--help"], ["metadata", "events", "list", ";echo"]):
                    response = await client.post("/api/plugins/bi-metadata/debug", json={"arguments": args})
                    self.assertEqual(response.status_code, 400)
            self.assertIn("token: temporary-test-token", headers[0].lower())
            plugin = await service.get_plugin(first, "bi-metadata")
            self.assertEqual(plugin.health_status, "healthy")
            arguments = ["metadata", "events", "list", "--product-key", "fixture-product"]
            repeated = await service.diagnose_plugin(first, "bi-metadata", arguments, probe=True)
            self.assertNotIn("配置已变化", repeated.message)

            async def change_config_during_query(*args: object) -> BiCliProcessResult:
                """args 为 CLI 执行参数；在返回旧检测结果前模拟用户保存了新配置。"""
                await service.save_plugin(first, "bi-metadata", PluginConfigInput(base_url=address, revision=plugin.revision))
                return BiCliProcessResult(exit_code=0, stdout='{"ok":true,"data":[]}')

            with patch("backend.core.bi_cli_tool._execute_bi_cli_process", change_config_during_query):
                stale = await service.diagnose_plugin(first, "bi-metadata", arguments, probe=True)
            self.assertIn("配置已变化", stale.message)
            plugin = await service.get_plugin(first, "bi-metadata")
            self.assertEqual(plugin.health_status, "untested")
            plugin = await service.toggle_plugin(first, "bi-metadata", True, plugin.revision)
            agent = await create_agent(first, {"name": "plugin fixture", "plugin_ids": ["bi-metadata"]})
            self.assertEqual((await get_agent(agent.id, first)).plugin_ids, ["bi-metadata"])
            context = RuntimeContext(user_id=first, agent_id=agent.id)
            self.assertEqual((await service.load_runtime_plugins(context)).plugin_ids, ["bi-metadata"])
            self.assertEqual((await service.load_runtime_plugins(RuntimeContext(user_id=second, agent_id=agent.id))).entries, [])
            with self.assertRaises(HTTPException):
                await service.bind_agent_plugins(agent.id, second, ["bi-metadata"])
            with self.assertRaises(HTTPException):
                await service.remove_plugin(first, "bi-metadata", plugin.revision)
            snapshot = await service.load_runtime_plugins(context)
            # 失败的上游检测不改变启用状态，错误信息不进入完整审计日志。
            status[0] = 401
            failed_probe = await service.diagnose_plugin(first, "bi-metadata", ["metadata", "events", "list", "--product-key", "fixture-product"], probe=True)
            self.assertFalse(failed_probe.ok)
            self.assertIn("UNAUTHENTICATED", failed_probe.message)
            self.assertTrue((await service.get_plugin(first, "bi-metadata")).enabled)
            plugin = await service.toggle_plugin(first, "bi-metadata", False, plugin.revision)
            self.assertEqual((await service.load_runtime_plugins(context)).entries, [])
            self.assertEqual(snapshot.entries[0].settings.secrets["token"], "temporary-test-token")
            await service.bind_agent_plugins(agent.id, first, [])
            plugin = await service.save_plugin(first, "bi-metadata", PluginConfigInput(base_url=address, clear_token=True, revision=plugin.revision))
            self.assertEqual(plugin.configured_secrets, [])
            self.assertEqual(plugin.health_status, "untested")
            activity = await service.list_activity(first, "bi-metadata")
            self.assertNotIn("temporary-test-token", json.dumps([entry.model_dump(mode="json") for entry in activity]))
            self.assertEqual(await service.list_activity(second, "bi-metadata"), [])
            await service.remove_plugin(first, "bi-metadata", plugin.revision)
            self.assertFalse((await service.get_plugin(first, "bi-metadata")).installed)

            # 无配置插件既不借用 BI 凭据，也不要求先保存一个空表单。
            local = await service.get_plugin(first, "json-tools")
            self.assertEqual(local.config_status, "not_required")
            local = await service.toggle_plugin(first, "json-tools", True, 0)
            local_agent = await create_agent(first, {"name": "local fixture", "plugin_ids": ["json-tools"]})
            local_context = RuntimeContext(user_id=first, agent_id=local_agent.id)
            tools = await build_all_tools([], [], local_context)
            self.assertIn("JsonFormat", [tool.name for tool in tools])
            self.assertNotIn("Skill", [tool.name for tool in tools])
            result = await next(tool for tool in tools if tool.name == "JsonFormat").ainvoke({"content": '{"b":2,"a":1}', "sort_keys": True})
            self.assertTrue(json.loads(result)["ok"])
            self.assertEqual((await service.list_activity(first, "json-tools"))[0].action, "call")
            with self.assertRaises(HTTPException):
                await service.import_environment(first, "json-tools", local.revision)
            with self.assertRaises(HTTPException):
                await service.diagnose_plugin(first, "json-tools", PluginProbeInput(), probe=True)

            # 历史 BI 行保留原密文，读取不中断，第一次保存才升级成通用 JSON 列。
            legacy_cipher = encrypt_plugin_token("legacy-token")
            await execute("INSERT INTO plugin_configs (user_id,plugin_id,base_url,encrypted_token,updated_at) VALUES (%s,%s,%s,%s,UTC_TIMESTAMP())", (second, "bi-metadata", address, legacy_cipher))
            old = await service.get_plugin(second, "bi-metadata")
            self.assertEqual(old.config_values["base_url"], address)
            old = await service.save_plugin(second, "bi-metadata", PluginConfigInput(values={"timeout_seconds": 15}, revision=old.revision))
            upgraded = await service._stored(second, "bi-metadata")
            self.assertEqual(upgraded.settings().secrets["token"], "legacy-token")
            self.assertEqual(old.config_values["timeout_seconds"], 15)

            # 多个任意命名的密钥分别保留和清除，不能假定字段名总是 token。
            custom = PluginManifest(id="test-config", name="测试配置", version="1", source="builtin", executor="local-json", tools=["JsonFormat"], description="测试", permissions=[], fields=[PluginField(key="access_key", label="访问密钥", kind="secret"), PluginField(key="sign_key", label="签名密钥", kind="secret")])
            with patch.dict(registry._MANIFESTS, {custom.id: custom}):
                saved = await service.save_plugin(first, custom.id, PluginConfigInput(secrets={"access_key": "first-secret", "sign_key": "second-secret"}))
                self.assertEqual(saved.configured_secrets, ["access_key", "sign_key"])
                saved = await service.save_plugin(first, custom.id, PluginConfigInput(secrets={"sign_key": ""}, clear_secrets=["access_key"], revision=saved.revision))
                self.assertEqual(saved.configured_secrets, ["sign_key"])
                self.assertEqual((await service._stored(first, custom.id)).settings().secrets["sign_key"], "second-secret")
                await service.remove_plugin(first, custom.id, saved.revision)
        finally:
            server.close()
            await server.wait_closed()
            for user_id in users:
                await execute("DELETE FROM agents WHERE user_id=%s", (user_id,))
                await execute("DELETE FROM plugin_configs WHERE user_id=%s", (user_id,))
                await execute("DELETE FROM plugin_activity WHERE user_id=%s", (user_id,))
                await execute("DELETE FROM users WHERE id=%s", (user_id,))
            await close_pool()


if __name__ == "__main__":
    unittest.main()
