"""读取固定目录内的插件声明，不从用户输入导入 Python 模块。"""

from pathlib import Path

from ..models.plugin import PluginManifest, PluginSkill


_PLUGIN_ROOT = Path(__file__).resolve().parent
_BI_SKILL_ROOT = _PLUGIN_ROOT.parents[1] / "pre-skill" / "bi-metadata"
_MANIFESTS = {
    "bi-metadata": PluginManifest.model_validate_json(
        (_PLUGIN_ROOT / "bi_metadata" / "manifest.json").read_text(encoding="utf-8")
    ),
    "json-tools": PluginManifest.model_validate_json(
        (_PLUGIN_ROOT / "json_tools" / "manifest.json").read_text(encoding="utf-8")
    ),
}
_SKILL_ROOTS = {"bi-metadata": _BI_SKILL_ROOT}


def list_manifests() -> list[PluginManifest]:
    """返回经过启动时校验的内置插件目录。"""
    return list(_MANIFESTS.values())


def get_manifest(plugin_id: str) -> PluginManifest:
    """按 plugin_id 获取受信任声明，不存在时抛出 ValueError。"""
    if plugin_id not in _MANIFESTS:
        raise ValueError("插件不存在")
    return _MANIFESTS[plugin_id]


def read_plugin_skill(plugin_id: str, path: str = "SKILL.md") -> PluginSkill:
    """读取 plugin_id 声明的 path 文件，仅允许清单中的固定路径。"""
    manifest = get_manifest(plugin_id)
    if not manifest.skill_name or path not in manifest.skill_files or plugin_id not in _SKILL_ROOTS:
        raise ValueError("插件中不存在该技能文件")
    return PluginSkill(name=manifest.skill_name, path=path,
                       content=(_SKILL_ROOTS[plugin_id] / path).read_text(encoding="utf-8"))
