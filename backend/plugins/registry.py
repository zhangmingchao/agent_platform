"""内置插件包目录；来源为平台内置，运行方式统一为用户容器中的 Python 进程。"""

from pathlib import Path

from .packages import ProcessManifest

_PLUGIN_ROOT = Path(__file__).resolve().parent
_PACKAGE_ROOTS = {"bi-metadata": _PLUGIN_ROOT / "bi_metadata", "json-tools": _PLUGIN_ROOT / "json_tools"}
_MANIFESTS = {plugin_id: ProcessManifest.model_validate_json((root / "manifest.json").read_text(encoding="utf-8"))
              for plugin_id, root in _PACKAGE_ROOTS.items()}


def list_manifests() -> list[ProcessManifest]:
    """返回平台提供的安装包声明，目录可见不代表已为当前用户安装。"""
    return list(_MANIFESTS.values())


def get_manifest(plugin_id: str) -> ProcessManifest:
    """按 plugin_id 读取内置包声明，未知标识拒绝使用。"""
    if plugin_id not in _MANIFESTS:
        raise ValueError("插件不存在")
    return _MANIFESTS[plugin_id]


def builtin_package_root(plugin_id: str) -> Path:
    """按 plugin_id 定位受信任的平台包源码目录，不接受任意宿主路径。"""
    get_manifest(plugin_id)
    return _PACKAGE_ROOTS[plugin_id]
