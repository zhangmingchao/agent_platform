"""通用插件管理：声明驱动的配置、密钥、诊断、用户隔离及运行快照。"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from time import monotonic
from typing import Any, AsyncIterator, Optional

import aiomysql
from fastapi import HTTPException
from pydantic import BaseModel, Field, SerializeAsAny, model_validator

from ..database import fetch_all, fetch_one, get_conn, release_conn
from ..models.plugin import (
    PluginActivity, PluginAgentSummary, PluginConfigInput, PluginDebugInput, PluginManifest,
    PluginOperationResult, PluginProbeInput, PluginSettings, PluginView,
)
from ..plugins.configuration import settings_complete, validate_fields
from ..plugins.registry import get_manifest, list_manifests
from ..plugins.packages import ProcessManifest
from ..plugins.storage import installed_package, list_packages
from ..runtime.models import RuntimeContext
from ..security import decrypt_plugin_token, encrypt_plugin_token

log = logging.getLogger(__name__)


class StoredPlugin(BaseModel):
    """数据库配置实体。

    user_id/plugin_id 标识所有者和插件；values 为普通配置，encrypted_secrets 为字段密文。
    enabled/revision 为启用状态和并发版本；health_status/health_message 为检测状态和摘要。
    tested_at/updated_at 为 UTC 检测及配置时间；只读取通用 JSON 配置列，不恢复历史 BI 字段。
    """

    user_id: int
    plugin_id: str
    values: dict[str, Any] = Field(default_factory=dict)
    encrypted_secrets: dict[str, str] = Field(default_factory=dict, repr=False)
    enabled: bool
    revision: int
    health_status: str
    health_message: str
    tested_at: Optional[datetime] = None
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def load_storage(cls, data: Any) -> Any:
        """将 data 数据库行映射为通用配置，动态字段仅在持久化边界使用映射。"""
        if not isinstance(data, dict) or "values_json" not in data:
            return data
        result = dict(data)
        for column, field in (("values_json", "values"), ("secrets_json", "encrypted_secrets")):
            value = data.get(column)
            result[field] = json.loads(value) if isinstance(value, str) else (value or {})
        return result

    def presence_settings(self) -> PluginSettings:
        """返回不解密的完整性快照，占位标记表示已有密钥，仅供公开视图和保存校验。"""
        return PluginSettings(values=self.values, secrets={key: "x" for key, value in self.encrypted_secrets.items() if value})

    def settings(self, manifest: PluginManifest | None = None) -> PluginSettings:
        """按插件声明解密和校验执行快照，禁止向日志或接口返回该实体的密钥。"""
        manifest = manifest or get_manifest(self.plugin_id)
        previous = PluginSettings(values=self.values, secrets={key: decrypt_plugin_token(value) for key, value in self.encrypted_secrets.items()})
        settings = validate_fields(manifest.fields, PluginConfigInput(), previous, complete=True)
        return settings


class RuntimePlugin(BaseModel):
    """一个运行插件；plugin_id 为受信任标识，settings 为独立配置快照，禁止 repr 回显。"""

    plugin_id: str
    settings: PluginSettings = Field(repr=False)
    manifest: SerializeAsAny[PluginManifest] | None = None


class RuntimePlugins(BaseModel):
    """Agent 插件快照；entries 仅包含已安装、启用且绑定的容器进程插件。"""

    entries: list[RuntimePlugin] = Field(default_factory=list)

    @property
    def plugin_ids(self) -> list[str]:
        """返回运行插件标识，供统一 Skill 入口合并可选的插件技能。"""
        return [entry.plugin_id for entry in self.entries]


async def _manifest(user_id: int, plugin_id: str) -> ProcessManifest:
    """按 user_id/plugin_id 读取用户激活版本，尚未安装的内置包返回目录声明。"""
    packages = await list_packages(user_id, plugin_id)
    if packages:
        return (next((package for package in packages if package.active), packages[0])).manifest
    try:
        return get_manifest(plugin_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


async def require_installed(user_id: int, plugin_id: str) -> None:
    """确认 user_id 的 plugin_id 已完成容器依赖安装，配置记录不能代替安装状态。"""
    try:
        package = await installed_package(user_id, plugin_id)
    except ValueError as exc:
        raise HTTPException(409, "请先将插件安装到用户 Runtime 容器") from exc
    if package.status != "ready":
        raise HTTPException(409, "请等待插件安装完成")


@asynccontextmanager
async def _transaction() -> AsyncIterator[aiomysql.Cursor]:
    """提供成功提交、异常回滚的字典游标，保证配置与审计原子更新。"""
    conn = await get_conn()
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            yield cursor
        await conn.commit()
    except BaseException:
        await conn.rollback()
        raise
    finally:
        await release_conn(conn)


async def _stored(user_id: int, plugin_id: str) -> Optional[StoredPlugin]:
    """读取 user_id 的 plugin_id 配置，不存在时返回 None。"""
    await _manifest(user_id, plugin_id)
    row = await fetch_one("SELECT * FROM plugin_configs WHERE user_id=%s AND plugin_id=%s", (user_id, plugin_id))
    return StoredPlugin.model_validate(row) if row else None


async def _audit(
    cursor: aiomysql.Cursor, user_id: int, plugin_id: str, action: str,
    status: str = "success", message: str = "", duration_ms: int = 0,
    agent_id: Optional[int] = None, trace_run_id: Optional[int] = None,
) -> None:
    """用 cursor 记录 user_id/plugin_id 的 action；其余参数为状态、安全摘要、耗时及 Agent/Trace 关联。"""
    await cursor.execute(
        "INSERT INTO plugin_activity (user_id,plugin_id,action,status,message,duration_ms,agent_id,trace_run_id,created_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP())",
        (user_id, plugin_id, action, status, message[:500], duration_ms, agent_id, trace_run_id),
    )


async def _persist(
    cursor: aiomysql.Cursor, user_id: int, plugin_id: str, settings: PluginSettings,
    encrypted_secrets: dict[str, str], existing: Optional[StoredPlugin], enabled: bool,
) -> None:
    """通过 cursor 保存用户插件；settings 仅写普通配置，encrypted_secrets 仅写密文，existing/enabled 控制更新与状态。"""
    values_json = json.dumps(settings.values, ensure_ascii=False)
    secrets_json = json.dumps(encrypted_secrets)
    if existing:
        # 历史专用列只写空值，不再读取或恢复历史配置。
        await cursor.execute(
            "UPDATE plugin_configs SET values_json=%s,secrets_json=%s,base_url='',encrypted_token='',"
            "revision=revision+1,health_status='untested',health_message='',tested_at=NULL,updated_at=UTC_TIMESTAMP() "
            "WHERE user_id=%s AND plugin_id=%s", (values_json, secrets_json, user_id, plugin_id),
        )
    else:
        await cursor.execute(
            "INSERT INTO plugin_configs (user_id,plugin_id,encrypted_token,values_json,secrets_json,enabled,updated_at) "
            "VALUES (%s,%s,'',%s,%s,%s,UTC_TIMESTAMP())", (user_id, plugin_id, values_json, secrets_json, enabled),
        )


async def get_plugin(user_id: int, plugin_id: str) -> PluginView:
    """返回 user_id 的 plugin_id 公开视图，仅暴露已配置密钥名称，不解密凭据。"""
    manifest = await _manifest(user_id, plugin_id)
    stored = await _stored(user_id, plugin_id)
    settings = stored.presence_settings() if stored else PluginSettings()
    normalized = validate_fields(manifest.fields, PluginConfigInput(), settings, complete=False)
    status = "not_required" if not manifest.fields else ("ready" if settings_complete(manifest.fields, normalized) else "incomplete")
    view = PluginView(manifest=manifest, config_values=normalized.values, config_status=status if stored or not manifest.fields else "unconfigured")
    if stored:
        view.installed = True
        view.enabled = stored.enabled
        view.configured_secrets = sorted(key for key, value in stored.encrypted_secrets.items() if value)
        view.revision = stored.revision
        view.health_status = stored.health_status
        view.health_message = stored.health_message
        view.tested_at = stored.tested_at
        view.updated_at = stored.updated_at
        rows = await fetch_all(
            "SELECT a.id,a.name FROM agents a JOIN agent_plugins p ON a.id=p.agent_id "
            "WHERE p.user_id=%s AND a.user_id=%s AND p.plugin_id=%s ORDER BY a.id", (user_id, user_id, plugin_id),
        )
        view.agents = [PluginAgentSummary.model_validate(row) for row in rows]
    packages = await list_packages(user_id, plugin_id)
    if packages:
        current = next((package for package in packages if package.active), packages[0])
        pending = next((package for package in packages if package.version != current.version and package.status in ("queued", "installing")), None)
        view.installed = True
        view.package_status = current.status
        view.pending_version = pending.version if pending else None
        view.package_error = current.error_message
    else:
        view.installed = False
        view.package_status = "not_installed"
    if view.package_status != "ready":
        view.enabled = False
    return view


async def list_plugins(user_id: int) -> list[PluginView]:
    """返回 user_id 的完整插件目录，各插件依据自己的声明计算配置状态。"""
    identifiers = [manifest.id for manifest in list_manifests()]
    identifiers.extend(sorted({package.plugin_id for package in await list_packages(user_id)} - set(identifiers)))
    return [await get_plugin(user_id, plugin_id) for plugin_id in identifiers]


async def save_plugin(user_id: int, plugin_id: str, data: PluginConfigInput, action: str = "configure") -> PluginView:
    """保存 user_id/plugin_id 的 data 通用配置；action 为本次审计操作名称。"""
    manifest = await _manifest(user_id, plugin_id)
    await require_installed(user_id, plugin_id)
    async with _transaction() as cursor:
        await cursor.execute("SELECT id FROM users WHERE id=%s FOR UPDATE", (user_id,))
        if not await cursor.fetchone():
            raise HTTPException(404, "用户不存在")
        await require_installed(user_id, plugin_id)
        manifest = await _manifest(user_id, plugin_id)
        await cursor.execute("SELECT * FROM plugin_configs WHERE user_id=%s AND plugin_id=%s FOR UPDATE", (user_id, plugin_id))
        row = await cursor.fetchone()
        existing = StoredPlugin.model_validate(row) if row else None
        if (existing.revision if existing else 0) != data.revision:
            raise HTTPException(409, "配置已被修改，请刷新后再保存")
        previous = existing.presence_settings() if existing else PluginSettings()
        settings = validate_fields(manifest.fields, data, previous, complete=bool(existing and existing.enabled))
        encrypted = dict(existing.encrypted_secrets) if existing else {}
        for key in data.clear_secrets:
            encrypted.pop(key, None)
        for key, secret in data.secrets.items():
            if secret:
                encrypted[key] = encrypt_plugin_token(secret)
        await _persist(cursor, user_id, plugin_id, settings, encrypted, existing, bool(existing and existing.enabled))
        await _audit(cursor, user_id, plugin_id, action, message="插件配置已保存")
    return await get_plugin(user_id, plugin_id)


async def toggle_plugin(user_id: int, plugin_id: str, enabled: bool, revision: int) -> PluginView:
    """按 revision 为 user_id 启停 plugin_id；无配置项插件允许以版本 0 直接首次启用。"""
    manifest = await _manifest(user_id, plugin_id)
    await require_installed(user_id, plugin_id)
    async with _transaction() as cursor:
        await cursor.execute("SELECT id FROM users WHERE id=%s FOR UPDATE", (user_id,))
        if not await cursor.fetchone():
            raise HTTPException(404, "用户不存在")
        await require_installed(user_id, plugin_id)
        manifest = await _manifest(user_id, plugin_id)
        await cursor.execute("SELECT * FROM plugin_configs WHERE user_id=%s AND plugin_id=%s FOR UPDATE", (user_id, plugin_id))
        row = await cursor.fetchone()
        stored = StoredPlugin.model_validate(row) if row else None
        if (stored.revision if stored else 0) != revision:
            raise HTTPException(409, "配置已被修改，请刷新后再操作")
        if stored:
            if enabled:
                stored.settings(manifest)
            await cursor.execute(
                "UPDATE plugin_configs SET enabled=%s,revision=revision+1,updated_at=UTC_TIMESTAMP() WHERE user_id=%s AND plugin_id=%s",
                (enabled, user_id, plugin_id),
            )
        else:
            settings = validate_fields(manifest.fields, PluginConfigInput(), PluginSettings(), complete=True)
            await _persist(cursor, user_id, plugin_id, settings, {}, None, enabled)
        await _audit(cursor, user_id, plugin_id, "enable" if enabled else "disable")
    return await get_plugin(user_id, plugin_id)


async def remove_plugin(user_id: int, plugin_id: str, revision: int) -> PluginOperationResult:
    """按 revision 删除 user_id 的 plugin_id 配置；有绑定则拒绝。"""
    await _manifest(user_id, plugin_id)
    async with _transaction() as cursor:
        await cursor.execute("SELECT revision FROM plugin_configs WHERE user_id=%s AND plugin_id=%s FOR UPDATE", (user_id, plugin_id))
        row = await cursor.fetchone()
        if not row or row["revision"] != revision:
            raise HTTPException(409, "配置不存在或已变化，请刷新后重试")
        await cursor.execute("SELECT agent_id FROM agent_plugins WHERE user_id=%s AND plugin_id=%s LIMIT 1", (user_id, plugin_id))
        if await cursor.fetchone():
            raise HTTPException(409, "请先解除所有 Agent 绑定")
        await cursor.execute("DELETE FROM plugin_configs WHERE user_id=%s AND plugin_id=%s", (user_id, plugin_id))
        await _audit(cursor, user_id, plugin_id, "remove")
    return PluginOperationResult(ok=True, message="插件已移除")


def redact_plugin_output(output: str, token: str = "", base_url: str = "", *, secrets: Optional[list[str]] = None) -> str:
    """递归脱敏 output；token/base_url 兼容旧入口，secrets 支持任意插件的多个敏感值。"""
    hidden = sorted({value for value in [token, base_url, *(secrets or [])] if value}, key=len, reverse=True)

    def clean(value: object) -> object:
        """递归处理 value 的 JSON 文本节点和键，避免凭据被服务错误回显。"""
        if isinstance(value, str):
            for secret in hidden:
                value = value.replace(secret, "[已隐藏]")
            return value
        if isinstance(value, dict):
            return {str(clean(key)): clean(item) for key, item in value.items()}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value
    return json.dumps(clean(json.loads(output)), ensure_ascii=False)


def redacted_result(output: str, manifest: PluginManifest, settings: PluginSettings) -> str:
    """按 manifest 字段类型脱敏 output；settings 提供本次敏感值及服务地址。"""
    hidden = list(settings.secrets.values()) + [str(settings.values.get(field.key) or "") for field in manifest.fields if field.format == "url"]
    return redact_plugin_output(output, secrets=hidden)


async def diagnose_plugin(
    user_id: int, plugin_id: str, request: PluginDebugInput | PluginProbeInput, probe: bool = False,
) -> PluginOperationResult:
    """按 user_id/plugin_id 配置执行 request；probe 使用声明模板，所有业务执行进入容器队列。"""
    await require_installed(user_id, plugin_id)
    manifest = await _manifest(user_id, plugin_id)
    if not (manifest.capabilities.connection_test if probe else manifest.capabilities.debug):
        raise HTTPException(400, "此插件不支持连接检测" if probe else "此插件不支持工具调试")
    stored = await _stored(user_id, plugin_id)
    settings = stored.settings(manifest) if stored else validate_fields(manifest.fields, PluginConfigInput(), PluginSettings(), complete=True)
    if probe:
        if not isinstance(request, PluginProbeInput) or manifest.probe is None:
            raise ValueError("连接检测参数无效")
        parameters = validate_fields(manifest.test_fields, PluginConfigInput(values=request.parameters), PluginSettings(), complete=True)
        data = manifest.probe.request(parameters)
    else:
        if not isinstance(request, PluginDebugInput):
            raise ValueError("工具调试参数无效")
        data = request
    from ..core.plugin_tools import build_plugin_tools
    from ..core.tool_execution_pipeline import wrap_tools_with_execution_pipeline
    from ..plugins.packages import public_tool_name
    context = RuntimeContext(user_id=user_id)
    tools = wrap_tools_with_execution_pipeline(build_plugin_tools(context, [RuntimePlugin(plugin_id=plugin_id, settings=settings, manifest=manifest)]), context)
    raw_name = data.tool_name or (manifest.tools[0] if len(manifest.tools) == 1 else "")
    tool = next((item for item in tools if item.name == public_tool_name(plugin_id, raw_name)), None)
    if tool is None:
        raise ValueError("插件工具不存在")
    started = monotonic()
    output = str(await tool.ainvoke(data.input))
    output = redacted_result(output, manifest, settings)
    result = json.loads(output)
    ok = result.get("ok") is True
    duration_ms = int((monotonic() - started) * 1000)
    code = str((result.get("error") or {}).get("code") or "EXECUTION_ERROR")
    message = ("连接正常（只读查询成功）" if probe else "执行成功") if ok else f"执行失败：{code}"
    async with _transaction() as cursor:
        if probe and stored:
            await cursor.execute("SELECT revision FROM plugin_configs WHERE user_id=%s AND plugin_id=%s FOR UPDATE", (user_id, plugin_id))
            current = await cursor.fetchone()
            if current and current["revision"] == stored.revision:
                await cursor.execute(
                    "UPDATE plugin_configs SET health_status=%s,health_message=%s,tested_at=UTC_TIMESTAMP() WHERE user_id=%s AND plugin_id=%s",
                    ("healthy" if ok else "error", message, user_id, plugin_id),
                )
            else:
                message += "；配置已变化，请重新测试"
        await _audit(cursor, user_id, plugin_id, "test" if probe else "debug", "success" if ok else "error", message, duration_ms)
    return PluginOperationResult(ok=ok, message=message, duration_ms=duration_ms, result=output)


async def list_activity(user_id: int, plugin_id: str, before_id: Optional[int] = None) -> list[PluginActivity]:
    """按 before_id 游标读取 user_id 的 plugin_id 最近 30 条记录。"""
    await _manifest(user_id, plugin_id)
    rows = await fetch_all(
        "SELECT * FROM plugin_activity WHERE user_id=%s AND plugin_id=%s AND (%s IS NULL OR id<%s) ORDER BY id DESC LIMIT 30",
        (user_id, plugin_id, before_id, before_id),
    )
    return [PluginActivity.model_validate(row) for row in rows]


async def bind_agent_plugins(agent_id: int, user_id: int, plugin_ids: list[str]) -> None:
    """为 user_id 的 agent_id 原子替换 plugin_ids 绑定；锁定配置防止与移除竞争。"""
    async with _transaction() as cursor:
        await cursor.execute("SELECT id FROM users WHERE id=%s FOR UPDATE", (user_id,))
        await cursor.fetchone()
        await cursor.execute("SELECT id FROM agents WHERE id=%s AND user_id=%s FOR UPDATE", (agent_id, user_id))
        if not await cursor.fetchone():
            raise HTTPException(404, "Agent 不存在")
        for plugin_id in sorted(set(plugin_ids)):
            manifest = await _manifest(user_id, plugin_id)
            await require_installed(user_id, plugin_id)
            await cursor.execute("SELECT * FROM plugin_configs WHERE user_id=%s AND plugin_id=%s FOR UPDATE", (user_id, plugin_id))
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(400, "请先启用插件")
            stored = StoredPlugin.model_validate(row)
            if not stored.enabled:
                await cursor.execute("SELECT agent_id FROM agent_plugins WHERE agent_id=%s AND user_id=%s AND plugin_id=%s", (agent_id, user_id, plugin_id))
                if not await cursor.fetchone():
                    raise HTTPException(400, "新绑定的插件必须已启用")
            else:
                stored.settings(manifest)
        await cursor.execute("SELECT plugin_id FROM agent_plugins WHERE agent_id=%s AND user_id=%s", (agent_id, user_id))
        previous = {row["plugin_id"] for row in await cursor.fetchall()}
        await cursor.execute("DELETE FROM agent_plugins WHERE agent_id=%s AND user_id=%s", (agent_id, user_id))
        for plugin_id in previous - set(plugin_ids):
            await _audit(cursor, user_id, plugin_id, "unbind", message="Agent 绑定已解除", agent_id=agent_id)
        for plugin_id in sorted(set(plugin_ids)):
            await cursor.execute("INSERT INTO agent_plugins (agent_id,user_id,plugin_id) VALUES (%s,%s,%s)", (agent_id, user_id, plugin_id))
            if plugin_id not in previous:
                await _audit(cursor, user_id, plugin_id, "bind", message="Agent 绑定已保存", agent_id=agent_id)


async def load_runtime_plugins(context: Optional[RuntimeContext]) -> RuntimePlugins:
    """按 context 所属用户及 Agent 读取 ready、启用且绑定的安装版本快照，不加载全局环境工具。"""
    if context is None or context.agent_id is None:
        return RuntimePlugins()
    rows = await fetch_all(
        "SELECT c.* FROM plugin_configs c JOIN agent_plugins p ON c.user_id=p.user_id AND c.plugin_id=p.plugin_id "
        "JOIN agents a ON a.id=p.agent_id WHERE c.user_id=%s AND a.user_id=%s AND p.agent_id=%s AND c.enabled=1",
        (context.user_id, context.user_id, context.agent_id),
    )
    entries: list[RuntimePlugin] = []
    for row in rows:
        stored = StoredPlugin.model_validate(row)
        packages = await list_packages(context.user_id, stored.plugin_id)
        current = next((package for package in packages if package.active and package.status == "ready"), None)
        if current:
            manifest = current.manifest
            entries.append(RuntimePlugin(plugin_id=stored.plugin_id, settings=stored.settings(manifest), manifest=manifest))
    return RuntimePlugins(entries=entries)


async def record_plugin_call(context: RuntimeContext, output: str, duration_ms: int = 0, plugin_id: str = "bi-metadata") -> None:
    """记录 context 的 plugin_id 调用；output 只读取状态，duration_ms 为耗时，审计失败不重试业务调用。"""
    try:
        ok = json.loads(output).get("ok") is True
        async with _transaction() as cursor:
            await _audit(cursor, context.user_id, plugin_id, "call", "success" if ok else "error",
                         "工具执行成功" if ok else "工具执行失败", duration_ms, context.agent_id,
                         context.trace_ctx.run_id if context.trace_ctx else None)
    except Exception:
        log.warning("插件调用记录写入失败", exc_info=False)
