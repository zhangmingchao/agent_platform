"""插件管理 HTTP 边界，所有配置与调试操作均使用当前登录用户。"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import get_current_user
from ..models.plugin import (
    PluginActivity, PluginConfigInput, PluginDebugInput, PluginOperationResult,
    PluginProbeInput, PluginSkill, PluginToggleInput, PluginToolDefinition, PluginView,
)
from ..plugins.registry import read_plugin_skill
from ..plugins.executors import get_executor
from ..security import SecretDecryptionError, SecurityConfigurationError
from ..services import plugin_service as service

router = APIRouter(prefix="/api/plugins", tags=["Plugins"])


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


@router.post("/{plugin_id}/import-environment", response_model=PluginView)
async def import_environment(plugin_id: str, revision: int = Query(ge=0), user: dict = Depends(get_current_user)) -> PluginView:
    """显式导入服务器环境；plugin_id 为插件，revision 为期望版本，user 为目标用户。"""
    try:
        return await service.import_environment(user["user_id"], plugin_id, revision)
    except (ValueError, SecurityConfigurationError) as exc:
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
    except (ValueError, SecretDecryptionError, SecurityConfigurationError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/{plugin_id}/activity", response_model=list[PluginActivity])
async def activity(plugin_id: str, before_id: Optional[int] = Query(default=None, ge=1), user: dict = Depends(get_current_user)) -> list[PluginActivity]:
    """返回 plugin_id 操作记录；before_id 为分页游标，user 隔离数据。"""
    return await service.list_activity(user["user_id"], plugin_id, before_id)


@router.get("/{plugin_id}/skill", response_model=PluginSkill)
async def skill_file(plugin_id: str, path: str = "SKILL.md", user: dict = Depends(get_current_user)) -> PluginSkill:
    """读取 plugin_id 声明内的 path 技能文件；user 要求登录。"""
    await service.get_plugin(user["user_id"], plugin_id)
    try:
        return read_plugin_skill(plugin_id, path)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/{plugin_id}/tools", response_model=list[PluginToolDefinition])
async def tool_schema(plugin_id: str, user: dict = Depends(get_current_user)) -> list[PluginToolDefinition]:
    """返回 plugin_id 执行器声明的工具定义实体；user 要求登录。"""
    plugin = await service.get_plugin(user["user_id"], plugin_id)
    return get_executor(plugin.manifest.executor).definitions()
