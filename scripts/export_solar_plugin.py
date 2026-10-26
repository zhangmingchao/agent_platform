"""导出 BI/Rule 进程插件与独立 Skill 文档包；不包含服务配置、Token 或参考工程源码。"""
from __future__ import annotations

import argparse
import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from backend.plugins.examples import export_builtin
from backend.plugins.packages import check_package, public_tool_name


@dataclass(frozen=True)
class ExportResult:
    """导出结果；plugin_path/skill_path 为交付文件，version 为代码版本，files 是插件文件数量。"""
    plugin_path: Path
    skill_path: Path
    version: str
    files: int


def export(output_dir: Path, standalone_source: Path | None = None) -> ExportResult:
    """导出到 output_dir；standalone_source 可选同步独立 Skill 源目录，使用实际带命名空间的工具名。"""
    content = export_builtin('bi-metadata')
    checked = check_package(content)
    output_dir.mkdir(parents=True, exist_ok=True)
    plugin_path = output_dir / f'solarengine-bi-rule-{checked.manifest.version}.zip'
    plugin_path.write_bytes(content)
    skills = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(content)) as source, zipfile.ZipFile(skills, 'w', compression=zipfile.ZIP_DEFLATED) as target:
        for name in checked.manifest.skill_files:
            text = source.read(name).decode()
            text = re.sub(r'\{\{tool:(\w+)\}\}', lambda match: public_tool_name(checked.manifest.id, match[1]), text)
            data = text.encode()
            entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            target.writestr(entry, data)
            if standalone_source is not None:
                file = standalone_source / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(data)
    skill_path = output_dir / f'solarengine-bi-rule-skill-{checked.manifest.version}.zip'
    skill_path.write_bytes(skills.getvalue())
    return ExportResult(plugin_path, skill_path, checked.manifest.version, checked.files)


def main() -> None:
    """解析 --output 导出目录、--standalone-source 可选 Skill 源目录，输出非敏感交付位置。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('dist/plugins'))
    parser.add_argument('--standalone-source', type=Path)
    args = parser.parse_args()
    result = export(args.output, args.standalone_source)
    print(f'plugin={result.plugin_path}\nskill={result.skill_path}\nversion={result.version}, files={result.files}')


if __name__ == '__main__':
    main()
