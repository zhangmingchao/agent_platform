"""可分发插件协议、工具桥接与进程生命周期的行为回归。"""

import io
import asyncio
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
import httpx

from backend.auth import get_current_user
from backend.core.plugin_tools import build_plugin_tools
from backend.models.plugin import PluginSettings, PluginView
from backend.plugins.examples import export_builtin
from backend.plugins.packages import ProcessManifest, ProcessProbe, ProcessResult, check_package, public_tool_name, validate_dependencies
from backend.routers.plugins import router
from backend.runtime.models import RuntimeContext
from backend.services.plugin_service import RuntimePlugin
from sandbox_service.process_runner import run_process
from backend.plugin_worker import run_with_cancellation
from backend.services.plugin_package_service import PluginExecution, SandboxPluginResult
from backend.plugins.storage import package_root


def rewrite_package(content: bytes, changes: dict[str, bytes]) -> bytes:
    """在测试 content 包上替换 changes 文件，用于构造真实的错误安装输入。"""
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(content)) as archive, zipfile.ZipFile(output, "w") as target:
        for name in archive.namelist():
            target.writestr(name, changes.pop(name, archive.read(name)))
        for name, value in changes.items():
            target.writestr(name, value)
    return output.getvalue()


class PackageContractTests(unittest.IsolatedAsyncioTestCase):
    """不连接外部服务的包格式、嵌套 Schema、响应契约和进程资源测试。"""

    def test_exported_builtins_are_standard_deterministic_packages(self) -> None:
        """内置导出包保留 ID，安装/导出摘要稳定，校验时不读取用户配置。"""
        for plugin_id in ("json-tools", "bi-metadata"):
            checked = check_package(export_builtin(plugin_id))
            self.assertEqual(checked.manifest.id, plugin_id)
            self.assertEqual(checked.manifest.source, "builtin")
            self.assertEqual(export_builtin(plugin_id), export_builtin(plugin_id))
            self.assertEqual(checked.manifest.executor, "python-process")
            self.assertEqual(checked.manifest.capabilities.environment_import, False)
            self.assertIn("tool_definitions", PluginView(manifest=checked.manifest).model_dump()["manifest"])

    def test_rejects_unsafe_archive_and_dependencies(self) -> None:
        """上传包拒绝路径越界、缺少入口、远程 Schema 引用和非固定依赖。"""
        content = export_builtin("json-tools")
        for name in ("../escape.py", "/escape.py", "executor\\escape.py", "a:escape.py", "executor//main.py"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                check_package(rewrite_package(content, {name: b"pass"}))
        manifest = check_package(content).manifest.model_dump()
        manifest["entrypoint"] = "missing.py"
        with self.assertRaises(ValueError):
            check_package(rewrite_package(content, {"manifest.json": json.dumps(manifest).encode()}))
        manifest["entrypoint"] = "executor/main.py"
        manifest["tool_definitions"][0]["parameters"] = {"type": "object", "$ref": "https://example.test/schema"}
        with self.assertRaises(ValueError):
            check_package(rewrite_package(content, {"manifest.json": json.dumps(manifest).encode()}))
        for dependency in ("httpx>=0.1", "-e ./code", "https://example.test/code.whl", "--index-url https://example.test"):
            with self.subTest(dependency=dependency), self.assertRaises(ValueError):
                validate_dependencies(dependency)

    def test_probe_preserves_json_types_and_rejects_undeclared_inputs(self) -> None:
        """检测数字/布尔值不能变为字符串；未声明字段和检测密钥在安装时拒绝。"""
        probe = ProcessProbe(tool_name="Check", arguments_template={"page": "{{page}}", "active": "{{active}}", "nested": ["constant"]})
        request = probe.request(PluginSettings(values={"page": 0, "active": False}))
        self.assertEqual(request.input, {"page": 0, "active": False, "nested": ["constant"]})
        self.assertIs(type(request.input["page"]), int)
        self.assertIs(type(request.input["active"]), bool)
        manifest = check_package(export_builtin("bi-metadata")).manifest.model_dump()
        manifest["probe"]["arguments_template"] = {"arguments": ["{{unknown}}"]}
        with self.assertRaises(ValueError):
            ProcessManifest.model_validate(manifest)
        manifest["probe"]["arguments_template"] = {"arguments": ["{{product_key}}"]}
        manifest["test_fields"][0]["kind"] = "secret"
        with self.assertRaises(ValueError):
            ProcessManifest.model_validate(manifest)

    async def test_tool_bridge_preserves_schema_identity_and_secret_scope(self) -> None:
        """工具名称有命名空间，参数数组不变，执行闭包只注入当前用户配置。"""
        manifest = check_package(export_builtin("bi-metadata")).manifest
        settings = PluginSettings(values={"base_url": "https://example.test"}, secrets={"token": "test-only"})
        entry = RuntimePlugin(plugin_id=manifest.id, settings=settings, manifest=manifest)
        context = RuntimeContext(user_id=7)
        with patch("backend.services.plugin_package_service.execute_process_plugin", AsyncMock(return_value='{"ok":true,"data":{},"error":null}')) as execute, patch("backend.core.plugin_tools.record_plugin_call", AsyncMock()):
            tool = build_plugin_tools(context, [entry])[0]
            await tool.ainvoke({"arguments": ["metadata", "events", "list", "--product-key", "fixture"]})
        self.assertEqual(tool.name, public_tool_name(manifest.id, "BiCli"))
        self.assertEqual(tool.args_schema["properties"]["arguments"]["type"], "array")
        self.assertEqual(execute.await_args.args[0].user_id, 7)
        self.assertEqual(execute.await_args.args[-1], {"token": "test-only"})
        self.assertTrue(tool.metadata["plugin_process"])

    async def test_upload_route_keeps_complete_process_manifest(self) -> None:
        """接口响应必须保留子类工具契约，否则前端无法加载上传插件。"""
        manifest = check_package(export_builtin("json-tools")).manifest
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: {"user_id": 7}
        with patch("backend.routers.plugins.service.get_plugin", AsyncMock(return_value=PluginView(manifest=manifest, package_status="ready"))):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
                response = await client.get("/api/plugins/" + manifest.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn("tool_definitions", response.json()["manifest"])

    def test_result_contract_and_process_timeout(self) -> None:
        """错误结果必须有原因；监督器在超时和输出超限后终止进程。"""
        import sys
        with self.assertRaises(ValueError):
            ProcessResult(ok=False)
        with self.assertRaises(ValueError):
            ProcessResult(ok=True, data=float("nan"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            timed = run_process([sys.executable, "-c", "import time;time.sleep(20)"], root, 1)
            self.assertEqual(timed.status, "timed_out")
            overflow = run_process([sys.executable, "-c", "print('x'*1100000)"], root, 5)
            self.assertEqual(overflow.status, "output_limit")
            self.assertLessEqual(len(overflow.stdout), 1024 * 1024)

    def test_shared_workspace_cannot_redirect_host_paths(self) -> None:
        """同用户代码能写共享目录，但不能通过链接诱导平台读取其他用户/宿主机路径。"""
        with tempfile.TemporaryDirectory() as directory, patch("backend.plugins.storage.RUNTIME_DATA_DIR", directory):
            parent = Path(directory) / "users/7/workspaces"
            parent.mkdir(parents=True)
            (parent / "plugins").symlink_to(Path(directory), target_is_directory=True)
            with self.assertRaises(ValueError):
                package_root(7, "json-test", "1.0.0")

    async def test_worker_retries_cancel_after_notification_failure(self) -> None:
        """接口首次取消通知失败后，Worker 必须根据数据库标记重新通知监督器。"""
        manifest = check_package(export_builtin("json-tools")).manifest
        stopped = asyncio.Event()
        cancel_count = 0

        async def sandbox(action: str, *_args: object) -> SandboxPluginResult:
            """模拟 action 对应的服务状态，第一次取消失败，第二次使执行返回。"""
            nonlocal cancel_count
            if action == "run":
                await stopped.wait()
                return SandboxPluginResult(status="cancelled")
            cancel_count += 1
            if cancel_count == 1:
                raise RuntimeError("暂时不可用")
            stopped.set()
            return SandboxPluginResult(status="cancel_requested")

        snapshot = PluginExecution(manifest=manifest, tool_name="JsonFormat")
        with patch("backend.plugin_worker.call_sandbox", sandbox), patch("backend.plugin_worker.fetch_one", AsyncMock(return_value={"cancel_requested": 1})):
            result = await asyncio.wait_for(run_with_cancellation(7, manifest.id, manifest.version, "a" * 32, snapshot), timeout=3)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(cancel_count, 2)

    async def test_worker_cancels_manager_after_http_failure(self) -> None:
        """请求连接失败时 Manager 可能仍在执行，Worker 必须主动送达取消。"""
        manifest = check_package(export_builtin("json-tools")).manifest
        snapshot = PluginExecution(manifest=manifest, tool_name="JsonFormat")
        sandbox = AsyncMock(side_effect=[RuntimeError("连接已中断"), SandboxPluginResult(status="cancel_requested")])
        with patch("backend.plugin_worker.call_sandbox", sandbox), self.assertRaises(RuntimeError):
            await run_with_cancellation(7, manifest.id, manifest.version, "a" * 32, snapshot)
        self.assertEqual([call.args[0] for call in sandbox.await_args_list], ["run", "cancel"])


if __name__ == "__main__":
    unittest.main()
