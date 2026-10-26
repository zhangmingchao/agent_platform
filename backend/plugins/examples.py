"""打包平台内置插件源码；安装与导出使用同一份标准 ZIP，不执行插件业务代码。"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from .packages import check_package
from .registry import builtin_package_root, get_manifest


def export_builtin(plugin_id: str) -> bytes:
    """将 plugin_id 的平台源码打包，保留稳定 ID/版本，不读取用户配置或凭据。"""
    manifest = get_manifest(plugin_id)
    root = builtin_package_root(plugin_id)
    files: dict[str, bytes] = {"manifest.json": manifest.model_dump_json(indent=2).encode()}
    for name in ("requirements.lock", manifest.entrypoint, *manifest.skill_files):
        files[name] = (root / name).read_bytes()
    if plugin_id == "bi-metadata":
        # BI CLI 仅作为包内库复制，API/Worker 不导入或执行其业务客户端。
        cli_root = Path(__file__).resolve().parents[1] / "bi_cli"
        for path in cli_root.rglob("*.py"):
            if path.name != "__main__.py":
                files["executor/bi_cli/" + path.relative_to(cli_root).as_posix()] = path.read_bytes()
        # 目录与客户端是插件代码资产，明确打包 Python/JSON，不携带平台配置和缓存。
        for path in (root / "executor" / "solar_api").rglob("*"):
            if path.is_file() and path.suffix in (".py", ".json"):
                files[path.relative_to(root).as_posix()] = path.read_bytes()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            # 固定 ZIP 元信息，连续导出摘要一致，安装幂等和失败重试使用相同内容。
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    content = output.getvalue()
    check_package(content)
    return content
