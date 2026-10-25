"""用户私有包目录和版本读取；路径不由模型或上传声明指定。"""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from ..config import RUNTIME_DATA_DIR
from ..database import fetch_all
from .packages import ProcessManifest


class InstalledPackage(BaseModel):
    """版本存储实体；身份、摘要、声明、安装状态、激活标记和错误用于安装及执行。"""

    user_id: int = Field(description="安装包所属平台用户")
    plugin_id: str = Field(description="插件稳定标识")
    version: str = Field(description="本记录固定代码版本")
    digest: str = Field(description="原始上传 ZIP 的 SHA-256 摘要")
    manifest_json: str | dict[str, object] = Field(description="数据库保存的版本声明，不包含用户配置")
    status: str = Field(description="依赖准备状态 queued/installing/ready/failed")
    active: bool = Field(description="是否为后续请求使用的激活版本")
    error_message: str = Field(default="", description="静态安装错误说明")

    @property
    def manifest(self) -> ProcessManifest:
        """返回经过完整协议校验的声明实体。"""
        if isinstance(self.manifest_json, str):
            return ProcessManifest.model_validate_json(self.manifest_json)
        return ProcessManifest.model_validate(self.manifest_json)


def package_root(user_id: int, plugin_id: str, version: str) -> Path:
    """由认证 user_id、plugin_id、version 定位私有版本目录，拒绝路径越界。"""
    if user_id <= 0 or not re.fullmatch(r"[a-z][a-z0-9-]{0,59}", plugin_id) or not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?", version):
        raise ValueError("插件存储身份无效")
    return private_workspace_path(user_id, "plugins", plugin_id, version)


def private_workspace_path(user_id: int, *parts: str) -> Path:
    """由 user_id 和平台生成的 parts 定位私有文件；拒绝共享挂载里的符号链接和越界路径。"""
    root = Path(RUNTIME_DATA_DIR) / "users" / str(user_id) / "workspaces"
    target = root
    for part in parts:
        if not part or part in (".", "..") or "/" in part or "\\" in part:
            raise ValueError("插件工作路径无效")
        target = target / part
        if target.is_symlink():
            raise ValueError("插件工作目录不允许符号链接")
    if root.resolve() not in target.resolve().parents:
        raise ValueError("插件路径超出用户工作目录")
    return target


async def list_packages(user_id: int, plugin_id: str | None = None) -> list[InstalledPackage]:
    """读取 user_id 的私有版本；plugin_id 为空时返回该用户的全部插件版本。"""
    rows = await fetch_all(
        "SELECT * FROM plugin_packages WHERE user_id=%s AND (%s IS NULL OR plugin_id=%s) ORDER BY created_at DESC",
        (user_id, plugin_id, plugin_id),
    )
    return [InstalledPackage.model_validate(row) for row in rows]


async def installed_package(user_id: int, plugin_id: str, version: str | None = None) -> InstalledPackage:
    """读取 user_id 的 plugin_id；version 指定快照版本，否则读取激活版本或最新安装状态。"""
    packages = await list_packages(user_id, plugin_id)
    for package in packages:
        if (version is not None and package.version == version) or (version is None and package.active):
            return package
    if packages and version is None:
        return packages[0]
    raise ValueError("插件包不存在")
