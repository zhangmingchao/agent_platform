"""显式开启的数据库/Docker 插件集成测试，所有测试身份和容器在结束后清理。"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel

from backend.config import RUNTIME_DATA_DIR
from backend.core.agent_factory import build_all_tools
from backend.database import close_pool, execute, fetch_one, init_db
from backend.models.plugin import PluginConfigInput, PluginDebugInput, PluginProbeInput
from backend.plugins.examples import export_builtin
from backend.plugins.packages import check_package
from backend.plugins.storage import InstalledPackage, installed_package, package_root
from backend.runtime.models import RuntimeContext
from backend.services import plugin_service
from backend.services.agent_service import create_agent
from backend.services.plugin_package_service import (
    activate_version, execute_process_plugin, install_builtin, submit_package, uninstall_package,
)
from backend.services.runtime_service import execute_runtime_task, prepare_runtime_execution, save_runtime_file
from backend.test.test_plugin_packages import rewrite_package


class FixtureContainer(BaseModel):
    """测试容器实体；id 验证实际复用，network_mode 验证联网策略。"""

    id: str
    network_mode: str


def docker_command(*arguments: str) -> str:
    """通过 Docker CLI 执行测试 arguments，避免后端引入仅 Manager 使用的 SDK 依赖。"""
    return subprocess.run(["docker", *arguments], check=True, capture_output=True, text=True).stdout.strip()


def fixture_container(user_id: int) -> FixtureContainer:
    """读取 user_id 测试容器，返回固定实体而不是原始 inspect 字典。"""
    inspected = json.loads(docker_command("inspect", f"agent-sandbox-user-{user_id}"))[0]
    return FixtureContainer(id=inspected["Id"], network_mode=inspected["HostConfig"]["NetworkMode"])


@unittest.skipUnless(os.getenv("PLUGIN_DOCKER_TEST") == "1", "显式设置 PLUGIN_DOCKER_TEST=1 并启动插件 Worker/Sandbox Service")
class PluginDockerTests(unittest.IsolatedAsyncioTestCase):
    """测试真实持久化队列、共享容器和进程协议；user_ids 为本测试创建的临时用户。"""

    async def asyncSetUp(self) -> None:
        """建立数据库及 Docker 连接，记录临时用户以便失败时也能清理。"""
        await init_db()
        self.user_ids: list[int] = []
        self.user_id = await self.new_user()

    async def new_user(self) -> int:
        """创建不能登录的临时用户实体记录，返回其平台 ID。"""
        user_id = await execute("INSERT INTO users (username,password,created_at) VALUES (%s,%s,UTC_TIMESTAMP())", ("plugin-docker-" + uuid4().hex[:12], "disabled-test-account"))
        self.user_ids.append(user_id)
        return user_id

    async def asyncTearDown(self) -> None:
        """只移除本测试的用户、容器和目录，避免影响已有 Runtime 数据。"""
        for user_id in self.user_ids:
            for container_id in docker_command("ps", "-aq", "--filter", f"label=agent.platform.user_id={user_id}").splitlines():
                docker_command("rm", "-f", container_id)
            await execute("DELETE FROM agents WHERE user_id=%s", (user_id,))
            await execute("DELETE FROM users WHERE id=%s", (user_id,))
            shutil.rmtree(Path(RUNTIME_DATA_DIR) / "users" / str(user_id), ignore_errors=True)
            shutil.rmtree(Path(RUNTIME_DATA_DIR) / "files" / str(user_id), ignore_errors=True)
        await close_pool()

    async def wait_package(self, plugin_id: str, version: str | None = None) -> InstalledPackage:
        """等 self.user_id 的 plugin_id/version 完成依赖准备，避免把 queued 当作安装成功。"""
        for _ in range(660):
            package = await installed_package(self.user_id, plugin_id, version)
            if package.status not in ("queued", "installing"):
                return package
            await asyncio.sleep(0.5)
        self.fail("依赖准备超时，请检查插件 Worker")

    async def test_shared_container_complete_lifecycle(self) -> None:
        """覆盖旧容器迁移、Agent 调用、网络、升级回滚、失败重试、文件、取消和卸载。"""
        user_id = self.user_id
        context = RuntimeContext(user_id=user_id)
        content = export_builtin("json-tools")
        manifest = check_package(content).manifest.model_dump()
        workspace = Path(RUNTIME_DATA_DIR) / "users" / str(user_id) / "workspaces"
        workspace.mkdir(parents=True)
        (workspace / "migration-proof.txt").write_text("preserved", encoding="utf-8")
        # 使用无 revision 的旧配置容器，验证升级仅替换容器，挂载文件保留。
        legacy_id = docker_command(
            "run", "-d", "--name", f"agent-sandbox-user-{user_id}", "--network", "none", "--user", "10001:10001",
            "-v", f"{workspace}:/workspaces", "--label", "agent.platform.sandbox=true", "--label", f"agent.platform.user_id={user_id}",
            os.getenv("PLUGIN_DOCKER_IMAGE", "agent-platform-python-sandbox:latest"), "sleep", "infinity",
        )
        initial = await plugin_service.get_plugin(user_id, "json-tools")
        self.assertEqual(initial.package_status, "not_installed")
        with self.assertRaises(HTTPException):
            await plugin_service.toggle_plugin(user_id, "json-tools", True, 0)
        package = await install_builtin(user_id, "json-tools")
        package = await self.wait_package(package.plugin_id)
        self.assertEqual(package.status, "ready", package.error_message)
        container = fixture_container(user_id)
        self.assertNotEqual(container.id, legacy_id)
        self.assertNotEqual(container.network_mode, "none")
        self.assertEqual((workspace / "migration-proof.txt").read_text(), "preserved")

        await plugin_service.toggle_plugin(user_id, package.plugin_id, True, 0)
        agent = await create_agent(user_id, {"name": "plugin-fixture", "system_prompt": "test", "plugin_ids": [package.plugin_id]})
        tools = await build_all_tools([], [], RuntimeContext(user_id=user_id, agent_id=agent.id))
        tool = next(item for item in tools if item.name.startswith("plugin__"))
        result = json.loads(await tool.ainvoke({"content": '{"z":1,"a":2}', "sort_keys": True}))
        self.assertTrue(result["ok"], result)
        self.assertEqual(json.loads(result["data"]["formatted"]), {"a": 2, "z": 1})
        debug = await plugin_service.diagnose_plugin(user_id, "json-tools", PluginDebugInput(tool_name="JsonFormat", input={"content": "{}", "indent": 0}))
        self.assertTrue(debug.ok, debug.result)
        self.assertEqual(json.loads(debug.result)["data"]["formatted"], "{}")
        task = await prepare_runtime_execution(context, code='import socket\nresult = {"address": socket.gethostbyname("example.com")}')
        runtime_result = await execute_runtime_task(task)
        self.assertEqual(runtime_result["status"], "completed", runtime_result)
        stored = await fetch_one("SELECT sandbox_container_id FROM code_executions WHERE id=%s", (task["executionId"],))
        self.assertEqual(stored["sandbox_container_id"], container.id)
        self.assertEqual(len(docker_command("ps", "-aq", "--filter", f"label=agent.platform.user_id={user_id}").splitlines()), 1)

        # 修改示例时使用独立标识；保留内置来源无法绕过平台原始包身份检查。
        with self.assertRaises(HTTPException):
            await submit_package(user_id, rewrite_package(content, {"executor/main.py": b"print('changed')"}))
        manifest.update(id="uploaded-json", source="builtin")
        upload = rewrite_package(content, {"manifest.json": json.dumps(manifest).encode()})
        package = await submit_package(user_id, upload)
        package = await self.wait_package(package.plugin_id)
        self.assertEqual(package.manifest.source, "upload")
        manifest["version"] = "1.0.1"
        newer = rewrite_package(content, {"manifest.json": json.dumps(manifest).encode()})
        await submit_package(user_id, newer)
        self.assertEqual((await self.wait_package(package.plugin_id, "1.0.1")).status, "ready")
        self.assertEqual((await installed_package(user_id, package.plugin_id)).version, "1.0.0")
        await activate_version(user_id, package.plugin_id, "1.0.1")
        self.assertEqual((await installed_package(user_id, package.plugin_id)).version, "1.0.1")
        await activate_version(user_id, package.plugin_id, "1.0.0")
        with self.assertRaises(HTTPException) as conflict:
            await submit_package(user_id, rewrite_package(upload, {"executor/main.py": b"print('changed')"}))
        self.assertEqual(conflict.exception.status_code, 409)
        other_user = await self.new_user()
        with self.assertRaises(HTTPException) as invisible:
            await plugin_service.get_plugin(other_user, package.plugin_id)
        self.assertEqual(invisible.exception.status_code, 404)

        manifest.update(id="broken-dep", version="1.0.0")
        broken = rewrite_package(content, {"manifest.json": json.dumps(manifest).encode(), "requirements.lock": b"package-does-not-exist-agent-platform==1.0.0"})
        await submit_package(user_id, broken)
        self.assertEqual((await self.wait_package("broken-dep")).status, "failed")
        await submit_package(user_id, broken)
        self.assertEqual((await self.wait_package("broken-dep")).status, "failed")
        self.assertEqual((await installed_package(user_id, package.plugin_id)).version, "1.0.0")

        # 同一标准参数协议支持平台文件 ID，生成文件只由平台登记。
        manifest.update(id="file-test", file_input_parameter="file_ids", tools=["CopyFile"], tool_definitions=[{
            "name": "CopyFile", "description": "复制文件", "risk_level": "medium",
            "parameters": {"type": "object", "properties": {"file_ids": {"type": "array", "items": {"type": "string"}}}, "required": ["file_ids"], "additionalProperties": False},
            "output_schema": {"type": "object"},
        }])
        source = b'import os,json,sys\nfrom pathlib import Path\nr=json.load(sys.stdin)\nf=json.loads(os.environ["PLUGIN_INPUT_FILES"])\np=Path(os.environ["PLUGIN_OUTPUT_DIR"])/"copied.txt"\np.write_text(Path(next(iter(f.values()))).read_text())\nprint(json.dumps({"ok":True,"data":{"copied":True},"error":None}))'
        await submit_package(user_id, rewrite_package(content, {"manifest.json": json.dumps(manifest).encode(), "executor/main.py": source}))
        file_plugin = await self.wait_package("file-test")
        input_file = await save_runtime_file(user_id, None, "input.txt", "text/plain", b"fixture contents")
        output = json.loads(await execute_process_plugin(context, file_plugin.manifest, "CopyFile", {"file_ids": [input_file["id"]]}, {}, {}))
        self.assertTrue(output["ok"], output)
        self.assertEqual(len(output["artifacts"]), 1)
        artifact = await fetch_one("SELECT storage_path FROM runtime_files WHERE id=%s", (output["artifacts"][0]["file_id"],))
        self.assertEqual(Path(artifact["storage_path"]).read_text(), "fixture contents")
        await uninstall_package(user_id, "file-test")
        self.assertFalse(package_root(user_id, "file-test", "1.0.0").exists())

        manifest = check_package(content).manifest.model_dump()
        manifest["id"] = "slow-test"
        await submit_package(user_id, rewrite_package(content, {"manifest.json": json.dumps(manifest).encode(), "executor/main.py": b"import time;time.sleep(60)"}))
        slow = await self.wait_package("slow-test")
        pending = asyncio.create_task(execute_process_plugin(context, slow.manifest, "JsonFormat", {"content": "{}"}, {}, {}))
        execution_id = ""
        try:
            for _ in range(100):
                row = await fetch_one("SELECT id,status FROM plugin_executions WHERE user_id=%s AND plugin_id='slow-test' ORDER BY created_at DESC LIMIT 1", (user_id,))
                if row and row["status"] == "running":
                    execution_id = row["id"]
                    break
                await asyncio.sleep(0.1)
            self.assertTrue(execution_id)
            await asyncio.sleep(0.3)
        finally:
            pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)
        for _ in range(100):
            row = await fetch_one("SELECT status,encrypted_request FROM plugin_executions WHERE id=%s", (execution_id,))
            if row and row["status"] == "cancelled":
                break
            await asyncio.sleep(0.1)
        self.assertEqual(row["status"], "cancelled")
        self.assertEqual(row["encrypted_request"], "")

        # 真实安装 BI 依赖，通过 Docker 网络访问本机模拟业务服务。
        async def upstream(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            """检查 reader 收到本次 Token，再通过 writer 返回固定模拟元数据。"""
            header = await reader.readuntil(b"\r\n\r\n")
            self.assertIn(b"token: fixture-token", header.lower())
            body = b'{"code":200,"data":{"list":[{"name":"login"}],"total":1},"message":"ok"}'
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(upstream, "0.0.0.0", 0)
        try:
            bi = await install_builtin(user_id, "bi-metadata")
            bi = await self.wait_package(bi.plugin_id)
            self.assertEqual(bi.status, "ready", bi.error_message)
            address = f'http://{os.getenv("PLUGIN_DOCKER_HOST", "host.docker.internal")}:{server.sockets[0].getsockname()[1]}'
            await plugin_service.save_plugin(user_id, bi.plugin_id, PluginConfigInput(values={"base_url": address}, secrets={"token": "fixture-token"}, revision=0))
            probe = await plugin_service.diagnose_plugin(user_id, "bi-metadata", PluginProbeInput(parameters={"product_key": "fixture"}), probe=True)
            self.assertTrue(probe.ok, probe.result)
            self.assertEqual((await plugin_service.get_plugin(user_id, "bi-metadata")).health_status, "healthy")
            debug = await plugin_service.diagnose_plugin(user_id, "bi-metadata", PluginDebugInput(tool_name="BiCli", input={"arguments": ["metadata", "events", "list", "--product-key", "fixture"]}))
            output = debug.result
            self.assertTrue(json.loads(output)["ok"], output)
            self.assertNotIn("fixture-token", output)
            saved = await plugin_service.get_plugin(user_id, "bi-metadata")
            await plugin_service.toggle_plugin(user_id, "bi-metadata", True, saved.revision)
            await plugin_service.bind_agent_plugins(agent.id, user_id, ["json-tools", "bi-metadata"])
            tools = await build_all_tools([], [], RuntimeContext(user_id=user_id, agent_id=agent.id))
            skill = next(tool for tool in tools if tool.name == "Skill")
            self.assertIn("plugin__bi_metadata__BiCli", await skill.ainvoke({"command": "bi-metadata"}))
            result = await next(tool for tool in tools if tool.name == "plugin__bi_metadata__BiCli").ainvoke({"arguments": ["metadata", "events", "list", "--product-key", "fixture"]})
            self.assertTrue(json.loads(result)["ok"], result)
        finally:
            server.close()
            await server.wait_closed()
        self.assertEqual(fixture_container(user_id).id, container.id)
        self.assertFalse(list((workspace / "plugins/.executions").glob("*/stderr.log")))
        await plugin_service.bind_agent_plugins(agent.id, user_id, [])
        await uninstall_package(user_id, "json-tools")
        removed = await plugin_service.get_plugin(user_id, "json-tools")
        self.assertEqual(removed.package_status, "not_installed")
        self.assertFalse(removed.enabled)
        await install_builtin(user_id, "json-tools")
        self.assertEqual((await self.wait_package("json-tools")).status, "ready")


if __name__ == "__main__":
    unittest.main()
