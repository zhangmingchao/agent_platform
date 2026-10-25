"""插件管理 HTTP 边界，所有配置与调试操作均使用当前登录用户。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from jsonschema import ValidationError as SchemaValidationError

from ..auth import get_current_user
from ..models.plugin import (
    PluginActivity, PluginConfigInput, PluginDebugInput, PluginOperationResult,
    PluginProbeInput, PluginSkill, PluginToggleInput, PluginToolDefinition, PluginView,
)
from ..security import SecretDecryptionError, SecurityConfigurationError
from ..services import plugin_service as service
from ..plugins.storage import InstalledPackage, list_packages

router = APIRouter(prefix="/api/plugins", tags=["Plugins"])


@router.post("/packages/upload")
async def upload_package(file: UploadFile = File(...), user: dict = Depends(get_current_user)) -> PluginView:
    """校验 file 上传包并准备安装；user 确定所有者，响应不包含配置或凭据。"""
    from ..services.plugin_package_service import submit_package
    try:
        content = await file.read(20 * 1024 * 1024 + 1)
        package = await submit_package(user["user_id"], content)
        return await service.get_plugin(user["user_id"], package.plugin_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/{plugin_id}/versions")
async def package_versions(plugin_id: str, user: dict = Depends(get_current_user)) -> list[InstalledPackage]:
    """读取 user 的 plugin_id 私有版本列表，不返回运行配置。"""
    from ..plugins.storage import list_packages
    return await list_packages(user["user_id"], plugin_id)


@router.post("/{plugin_id}/install", response_model=PluginView)
async def install_builtin_package(plugin_id: str, user: dict = Depends(get_current_user)) -> PluginView:
    """为 user 安装平台提供的 plugin_id 包；来源为内置但安装/运行与上传包完全相同。"""
    from ..services.plugin_package_service import install_builtin
    try:
        await install_builtin(user["user_id"], plugin_id)
        return await service.get_plugin(user["user_id"], plugin_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/{plugin_id}/versions/{version}/activate", response_model=PluginOperationResult)
async def activate_package(plugin_id: str, version: str, user: dict = Depends(get_current_user)) -> PluginOperationResult:
    """将 user 的 plugin_id 切换到已安装的 version。"""
    from ..services.plugin_package_service import activate_version
    try:
        return await activate_version(user["user_id"], plugin_id, version)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/{plugin_id}/export")
async def export_package(plugin_id: str, version: Optional[str] = None, user: dict = Depends(get_current_user)) -> Response:
    """导出 user 的 plugin_id/version 原始包或内置示例包，始终不包含用户配置和密钥。"""
    from ..plugins.storage import installed_package, private_workspace_path
    from ..plugins.examples import export_builtin
    try:
        packages = await list_packages(user["user_id"], plugin_id)
        if not packages and version is None:
            content = export_builtin(plugin_id)
        else:
            package = await installed_package(user["user_id"], plugin_id, version)
            content = private_workspace_path(user["user_id"], "plugins", plugin_id, package.version, "package.zip").read_bytes()
        return Response(content, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{plugin_id}.zip"'})
    except (ValueError, OSError) as exc:
        raise HTTPException(404, "插件安装包不存在") from exc


@router.delete("/{plugin_id}/package", response_model=PluginOperationResult)
async def uninstall_package(plugin_id: str, user: dict = Depends(get_current_user)) -> PluginOperationResult:
    """卸载 user 的 plugin_id 包，运行或绑定中的插件不能卸载。"""
    from ..services.plugin_package_service import uninstall_package as uninstall
    return await uninstall(user["user_id"], plugin_id)


@router.post("/executions/{execution_id}/cancel", response_model=PluginOperationResult)
async def cancel_package_execution(execution_id: str, user: dict = Depends(get_current_user)) -> PluginOperationResult:
    """请求取消 user 的 execution_id，禁止跨用户操作。"""
    from ..services.plugin_package_service import cancel_execution
    return await cancel_execution(user["user_id"], execution_id)


@router.get("", response_model=list[PluginView])
async def list_plugins(user: dict = Depends(get_current_user)) -> list[PluginView]:
    """列出 user 当前用户的插件目录和配置。"""
    return await service.list_plugins(user["user_id"])


@router.get("/{plugin_id}", response_model=PluginView)
async def get_plugin(plugin_id: str, user: dict = Depends(get_current_user)) -> PluginView:
    """读取 plugin_id 的公开详情；user 为认证上下文。"""
    return await service.get_plugin(user["user_id"], plugin_id)


@router.put("/{plugin_id}/config", response_model=PluginView)
async def save_config(plugin_id: str, data: PluginConfigInput, user: dict = Depends(get_current_user)) -> PluginView:
    """保存 plugin_id 的 data 配置；凭据加密后存储，user 隔离所属用户。"""
    try:
        return await service.save_plugin(user["user_id"], plugin_id, data)
    except (ValueError, SecurityConfigurationError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.put("/{plugin_id}/enabled", response_model=PluginView)
async def toggle_plugin(plugin_id: str, data: PluginToggleInput, user: dict = Depends(get_current_user)) -> PluginView:
    """按 data 目标状态及版本启停 plugin_id；user 为所属用户。"""
    try:
        return await service.toggle_plugin(user["user_id"], plugin_id, data.enabled, data.revision)
    except (ValueError, SecretDecryptionError, SecurityConfigurationError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.delete("/{plugin_id}", response_model=PluginOperationResult)
async def remove_plugin(plugin_id: str, revision: int = Query(ge=1), user: dict = Depends(get_current_user)) -> PluginOperationResult:
    """按 revision 移除 plugin_id 配置；user 为所属用户，有绑定时拒绝。"""
    return await service.remove_plugin(user["user_id"], plugin_id, revision)


@router.post("/{plugin_id}/test", response_model=PluginOperationResult)
async def test_plugin(plugin_id: str, data: PluginProbeInput, user: dict = Depends(get_current_user)) -> PluginOperationResult:
    """按 plugin_id 声明校验 data 检测参数，user 为配置所属用户。"""
    return await _diagnose(plugin_id, user["user_id"], data, True)


@router.post("/{plugin_id}/debug", response_model=PluginOperationResult)
async def debug_plugin(plugin_id: str, data: PluginDebugInput, user: dict = Depends(get_current_user)) -> PluginOperationResult:
    """用 data 参数调试 plugin_id 声明的工具；user 为配置所属用户。"""
    return await _diagnose(plugin_id, user["user_id"], data, False)


async def _diagnose(plugin_id: str, user_id: int, data: PluginDebugInput | PluginProbeInput, probe: bool) -> PluginOperationResult:
    """统一诊断错误；plugin_id/user_id 标识配置，data 是插件参数，probe 控制健康状态更新。"""
    try:
        return await service.diagnose_plugin(user_id, plugin_id, data, probe)
    except SchemaValidationError as exc:
        raise HTTPException(400, "工具参数无效，请按工具 Schema 填写") from exc
    except (ValueError, SecretDecryptionError, SecurityConfigurationError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/{plugin_id}/activity", response_model=list[PluginActivity])
async def activity(plugin_id: str, before_id: Optional[int] = Query(default=None, ge=1), user: dict = Depends(get_current_user)) -> list[PluginActivity]:
    """返回 plugin_id 操作记录；before_id 为分页游标，user 隔离数据。"""
    return await service.list_activity(user["user_id"], plugin_id, before_id)


@router.get("/{plugin_id}/skill", response_model=PluginSkill)
async def skill_file(plugin_id: str, path: str = "SKILL.md", user: dict = Depends(get_current_user)) -> PluginSkill:
    """读取 plugin_id 声明内的 path 技能文件；user 要求登录。"""
    try:
        await service.require_installed(user["user_id"], plugin_id)
        manifest = (await service.get_plugin(user["user_id"], plugin_id)).manifest
        from ..core.tools import build_skill_tools
        tools = build_skill_tools([], [plugin_id], {plugin_id: manifest}, user["user_id"])
        if path not in manifest.skill_files:
            raise ValueError("插件 Skill 文件不存在")
        return PluginSkill(name=manifest.skill_name or "", path=path, content=tools[1].invoke({"skill_name": manifest.skill_name, "path": path}))
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{plugin_id}/tools", response_model=None)
async def tool_schema(plugin_id: str, user: dict = Depends(get_current_user)) -> list[PluginToolDefinition]:
    """返回 plugin_id 执行器声明的工具定义实体；user 要求登录。"""
    plugin = await service.get_plugin(user["user_id"], plugin_id)
    from ..plugins.packages import ProcessManifest
    return ProcessManifest.model_validate(plugin.manifest.model_dump()).tool_definitions
