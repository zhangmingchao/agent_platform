"""插件安装和执行服务；数据库保存任务，Worker 领取后调用共享用户容器。"""

from __future__ import annotations

import asyncio
import json
import shutil
from time import monotonic
from uuid import uuid4

import httpx
from fastapi import HTTPException
from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field

from ..config import SANDBOX_SERVICE_TOKEN, SANDBOX_SERVICE_URL
from ..database import execute, fetch_one
from ..models.plugin import PluginConfigInput, PluginOperationResult
from ..plugins.configuration import validate_fields
from ..plugins.packages import ProcessManifest, ProcessResult, check_package
from ..plugins.storage import InstalledPackage, installed_package, list_packages, package_root
from ..runtime.models import RuntimeContext
from ..security import encrypt_plugin_token


class PluginExecution(BaseModel):
    """执行快照；manifest 固定版本，tool_name 为原始名称，arguments 为业务参数。

    values 为普通配置，secrets 为仅执行时解密的凭据；身份和路径由平台单独确定。
    """

    manifest: ProcessManifest = Field(description="本次调用固定的插件版本声明")
    tool_name: str = Field(description="包内原始工具名称")
    arguments: dict[str, object] = Field(default_factory=dict, description="通过工具输入 Schema 校验的业务参数")
    values: dict[str, object] = Field(default_factory=dict, description="本次普通配置快照")
    secrets: dict[str, str] = Field(default_factory=dict, repr=False, description="本次解密凭据，仅内部执行传递")
    input_files: dict[str, str] = Field(default_factory=dict, description="授权文件 ID 到容器输入路径的映射")
    session_id: int | None = Field(default=None, description="生成文件关联的会话，调试时为空")


class SandboxPluginResult(BaseModel):
    """共享容器操作结果；status/exit_code/error 表示执行状态，stdout/stderr 为有限日志。"""

    status: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    container_id: str = ""


async def submit_package(user_id: int, content: bytes) -> InstalledPackage:
    """为 user_id 校验并暂存 content 安装包，队列由数据库持久化，返回安装状态实体。"""
    from . import plugin_service as service
    from ..plugins.registry import list_manifests
    from ..plugins.examples import export_builtin

    checked = check_package(content)
    manifest = checked.manifest
    if manifest.id in {item.id for item in list_manifests()}:
        if content != export_builtin(manifest.id):
            raise HTTPException(409, "内置插件标识只接受平台提供的原始包，修改代码请使用新的插件标识")
    else:
        # 插件来源由平台决定，上传声明不能伪装成平台内置代码。
        manifest = manifest.model_copy(update={"source": "upload"})
    async with service._transaction() as cursor:
        await cursor.execute("SELECT id FROM users WHERE id=%s FOR UPDATE", (user_id,))
        if not await cursor.fetchone():
            raise HTTPException(404, "用户不存在")
        await cursor.execute("SELECT * FROM plugin_packages WHERE user_id=%s AND plugin_id=%s", (user_id, manifest.id))
        previous = [InstalledPackage.model_validate(row) for row in await cursor.fetchall()]
        for package in previous:
            if package.version == manifest.version:
                if package.digest != checked.digest:
                    raise HTTPException(409, "同版本已有不同内容，请增加插件版本")
                if package.status == "failed":
                    (package_root(user_id, manifest.id, manifest.version) / ".ready").unlink(missing_ok=True)
                    await cursor.execute("UPDATE plugin_packages SET status='queued',error_message='',updated_at=UTC_TIMESTAMP() WHERE user_id=%s AND plugin_id=%s AND version=%s", (user_id, manifest.id, manifest.version))
                return package.model_copy(update={"status": "queued" if package.status == "failed" else package.status})
            if package.status in ("queued", "installing"):
                raise HTTPException(409, "该插件已有正在准备的版本")
        directory = package_root(user_id, manifest.id, manifest.version)
        # 用户行锁保护同用户安装；未提交事务留下的临时目录可安全重建。
        if directory.exists():
            shutil.rmtree(directory)
        check_package(content, directory / "package")
        (directory / "package.zip").write_bytes(content)
        await cursor.execute(
            "INSERT INTO plugin_packages (user_id,plugin_id,version,digest,manifest_json,status,active,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,'queued',0,UTC_TIMESTAMP(),UTC_TIMESTAMP())",
            (user_id, manifest.id, manifest.version, checked.digest, manifest.model_dump_json()),
        )
        await service._audit(cursor, user_id, manifest.id, "upload", message="插件包已校验，等待准备依赖")
    return await installed_package(user_id, manifest.id, manifest.version)


async def install_builtin(user_id: int, plugin_id: str) -> InstalledPackage:
    """将平台提供的 plugin_id 标准包安装到 user_id 的 Runtime 容器，复用上传包队列和重试。"""
    from ..plugins.examples import export_builtin
    return await submit_package(user_id, export_builtin(plugin_id))


async def activate_version(user_id: int, plugin_id: str, version: str) -> PluginOperationResult:
    """为 user_id/plugin_id 切换已准备好的 version；校验现有配置兼容，运行任务继续旧版本。"""
    from . import plugin_service as service
    async with service._transaction() as cursor:
        await cursor.execute("SELECT id FROM users WHERE id=%s FOR UPDATE", (user_id,))
        await cursor.fetchone()
        package = await installed_package(user_id, plugin_id, version)
        if package.status != "ready":
            raise HTTPException(409, "插件版本尚未准备完成")
        await cursor.execute("SELECT * FROM plugin_configs WHERE user_id=%s AND plugin_id=%s FOR UPDATE", (user_id, plugin_id))
        row = await cursor.fetchone()
        if row:
            stored = service.StoredPlugin.model_validate(row)
            if (set(stored.values) | set(stored.encrypted_secrets)) - {field.key for field in package.manifest.fields}:
                raise HTTPException(409, "新版本删除了已保存配置字段，请先停用并清理对应配置")
            try:
                validate_fields(package.manifest.fields, PluginConfigInput(), stored.presence_settings(), complete=stored.enabled)
            except ValueError as exc:
                raise HTTPException(409, "新版本与当前配置不兼容：" + str(exc)) from exc
        await cursor.execute("UPDATE plugin_packages SET active=0 WHERE user_id=%s AND plugin_id=%s", (user_id, plugin_id))
        await cursor.execute("UPDATE plugin_packages SET active=1,updated_at=UTC_TIMESTAMP() WHERE user_id=%s AND plugin_id=%s AND version=%s", (user_id, plugin_id, version))
        # 配置版本同步递增，避免旧页面覆盖新版本配置。
        await cursor.execute("UPDATE plugin_configs SET revision=revision+1,health_status='untested' WHERE user_id=%s AND plugin_id=%s", (user_id, plugin_id))
        await service._audit(cursor, user_id, plugin_id, "activate", message=f"已切换到版本 {version}")
    return PluginOperationResult(ok=True, message="插件版本已切换")


async def uninstall_package(user_id: int, plugin_id: str) -> PluginOperationResult:
    """卸载 user_id 的 plugin_id 包；拒绝存在 Agent 绑定、安装或运行任务的插件。"""
    from . import plugin_service as service
    async with service._transaction() as cursor:
        await cursor.execute("SELECT id FROM users WHERE id=%s FOR UPDATE", (user_id,))
        await cursor.fetchone()
        packages = await list_packages(user_id, plugin_id)
        if not packages:
            raise HTTPException(404, "插件包不存在")
        await cursor.execute("SELECT agent_id FROM agent_plugins WHERE user_id=%s AND plugin_id=%s LIMIT 1", (user_id, plugin_id))
        if await cursor.fetchone():
            raise HTTPException(409, "请先解除 Agent 绑定")
        await cursor.execute("SELECT id FROM plugin_executions WHERE user_id=%s AND plugin_id=%s AND status IN ('queued','running') LIMIT 1", (user_id, plugin_id))
        if await cursor.fetchone() or any(package.status in ("queued", "installing") for package in packages):
            raise HTTPException(409, "插件仍有正在安装或执行的任务")
        await cursor.execute("DELETE FROM plugin_configs WHERE user_id=%s AND plugin_id=%s", (user_id, plugin_id))
        await cursor.execute("DELETE FROM plugin_packages WHERE user_id=%s AND plugin_id=%s", (user_id, plugin_id))
        await service._audit(cursor, user_id, plugin_id, "uninstall", message="插件已卸载")
        # 文件删除仍在用户锁内，防止卸载提交后立即重装同版本目录被误删。
        for package in packages:
            await asyncio.to_thread(shutil.rmtree, package_root(user_id, plugin_id, package.version), True)
    return PluginOperationResult(ok=True, message="插件包及配置已卸载")


async def call_sandbox(action: str, user_id: int, plugin_id: str, version: str, execution_id: str, snapshot: PluginExecution | None = None) -> SandboxPluginResult:
    """通过 action 调用共享容器；身份参数由数据库任务提供，snapshot 仅通过内部认证 HTTP 传递。"""
    payload = {"user_id": user_id, "plugin_id": plugin_id, "version": version, "execution_id": execution_id}
    if snapshot is not None:
        payload["snapshot"] = snapshot.model_dump()
    async with httpx.AsyncClient(timeout=330 if action == "install" else 5 if action == "cancel" else 150) as client:
        response = await client.post(f"{SANDBOX_SERVICE_URL}/v1/plugins/{action}", json=payload, headers={"Authorization": f"Bearer {SANDBOX_SERVICE_TOKEN}"})
        if response.status_code >= 400:
            # 错误文本可能含凭据，仅向上层返回静态错误。
            raise RuntimeError(f"共享容器服务拒绝插件操作（HTTP {response.status_code}）")
        return SandboxPluginResult.model_validate(response.json())


async def execute_process_plugin(context: RuntimeContext, manifest: ProcessManifest, tool_name: str, arguments: dict[str, object], values: dict[str, object], secrets: dict[str, str]) -> str:
    """使用 context 身份执行 manifest 的 tool_name；arguments 是业务输入，values/secrets 是配置快照。"""
    from . import plugin_service as service
    tool = next((item for item in manifest.tool_definitions if item.name == tool_name), None)
    if tool is None:
        raise ValueError("插件工具不存在")
    Draft202012Validator(tool.parameters).validate(arguments)
    if len(json.dumps(arguments, ensure_ascii=False, allow_nan=False).encode()) > 200_000:
        raise ValueError("插件参数超过 200KB")
    execution_id = uuid4().hex
    from ..plugins.files import prepare_files
    input_files = await prepare_files(context, execution_id, arguments.get(manifest.file_input_parameter, []) if manifest.file_input_parameter else [])
    snapshot = PluginExecution(manifest=manifest, tool_name=tool_name, arguments=arguments, values=values, secrets=secrets, input_files=input_files.references, session_id=context.session_id)
    async with service._transaction() as cursor:
        await cursor.execute("SELECT id FROM users WHERE id=%s FOR UPDATE", (context.user_id,))
        await cursor.fetchone()
        package = await installed_package(context.user_id, manifest.id, manifest.version)
        if package.status != "ready":
            raise HTTPException(409, "插件尚未准备完成")
        await cursor.execute("INSERT INTO plugin_executions (id,user_id,plugin_id,version,encrypted_request,status,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,'queued',UTC_TIMESTAMP(),UTC_TIMESTAMP())", (execution_id, context.user_id, manifest.id, manifest.version, encrypt_plugin_token(snapshot.model_dump_json())))
    deadline = monotonic() + manifest.timeout_seconds + 90
    try:
        while monotonic() < deadline:
            row = await fetch_one("SELECT status,result_json FROM plugin_executions WHERE id=%s AND user_id=%s", (execution_id, context.user_id))
            if row and row["status"] not in ("queued", "running"):
                return row["result_json"] or ProcessResult(ok=False, error={"code": "EXECUTION_FAILED", "message": "执行失败"}).model_dump_json()
            await asyncio.sleep(0.3)
    except asyncio.CancelledError:
        await cancel_execution(context.user_id, execution_id)
        raise
    await cancel_execution(context.user_id, execution_id)
    return ProcessResult(ok=False, error={"code": "QUEUE_TIMEOUT", "message": "插件执行等待超时，请检查插件 Worker"}).model_dump_json()


async def cancel_execution(user_id: int, execution_id: str) -> PluginOperationResult:
    """为 user_id 的 execution_id 写取消标记，并要求容器执行器终止运行中的任务。"""
    row = await fetch_one("SELECT * FROM plugin_executions WHERE id=%s AND user_id=%s", (execution_id, user_id))
    if not row:
        raise HTTPException(404, "插件执行不存在")
    await execute("UPDATE plugin_executions SET cancel_requested=1,updated_at=UTC_TIMESTAMP() WHERE id=%s AND user_id=%s", (execution_id, user_id))
    if row["status"] == "running":
        try:
            await call_sandbox("cancel", user_id, row["plugin_id"], row["version"], execution_id)
        except (httpx.HTTPError, RuntimeError):
            pass  # Worker 运行期间轮询持久化标记并重发取消；监督器硬超时负责最终清理。
    return PluginOperationResult(ok=True, message="已请求取消执行")
