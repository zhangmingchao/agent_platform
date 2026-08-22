"""Skill 业务操作。"""
import json
import os
import logging
import shutil
import zipfile
from io import BytesIO
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import List, Dict, Optional, Tuple

from ..config import SKILLS_DIR
from ..database import execute, fetch_all, fetch_one

log = logging.getLogger("agent-platform")

MAX_SKILL_ARCHIVE_FILES = 200
MAX_SKILL_ARCHIVE_SIZE = 20 * 1024 * 1024  # 解压后 20 MiB
MAX_EDITABLE_SKILL_FILE_SIZE = 1024 * 1024  # 1 MiB


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


async def list_skills(user_id: int) -> List[Dict]:
    return await fetch_all(
        "SELECT id, name, description, created_at FROM skills WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,)
    )


async def get_skill(skill_id: int, user_id: int) -> Optional[Dict]:
    skill = await fetch_one(
        "SELECT * FROM skills WHERE id=%s AND user_id=%s",
        (skill_id, user_id)
    )
    if skill:
        # 文件系统是 Skill 指令的主数据源；数据库 content 仅用于兼容旧记录。
        skill["content"] = read_skill_entrypoint(skill_id, skill.get("content", ""))
    return skill


async def create_skill(user_id: int, name: str, description: str, content: str) -> Dict:
    now = _now()
    skill_id = await execute(
        "INSERT INTO skills (user_id, name, description, content, created_at) VALUES (%s, %s, %s, %s, %s)",
        (user_id, name, description, content, now)
    )
    try:
        # 手动创建的 Skill 也遵循 ZIP Skill 的目录结构。
        skill_dir = Path(SKILLS_DIR) / str(skill_id)
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
    except Exception:
        await execute("DELETE FROM skills WHERE id=%s AND user_id=%s", (skill_id, user_id))
        raise

    return {
        "id": skill_id,
        "name": name,
        "description": description,
        "content": content,
        "created_at": now,
    }


async def update_skill_metadata(
    skill_id: int,
    user_id: int,
    name: str,
    description: str,
) -> Optional[Dict]:
    """更新显示元数据，不修改 Skill 包文件。"""
    existing = await fetch_one(
        "SELECT id FROM skills WHERE id=%s AND user_id=%s",
        (skill_id, user_id),
    )
    if not existing:
        return None
    await execute(
        "UPDATE skills SET name=%s, description=%s WHERE id=%s AND user_id=%s",
        (name, description, skill_id, user_id),
    )
    return await get_skill(skill_id, user_id)


def _decode_zip_filename(filename: str) -> str:
    """修复 ZIP 工具在未设置 UTF-8 标志时按 CP437 解码的 UTF-8 文件名。"""
    try:
        return filename.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return filename


def _is_ignored_archive_path(path: PurePosixPath) -> bool:
    """忽略不属于 Skill 的 macOS 元数据文件和 IDE 文件。"""
    return (
        "__MACOSX" in path.parts
        or ".idea" in path.parts
        or path.name == ".DS_Store"
        or path.name.startswith("._")
    )


def _safe_archive_members(
    archive: zipfile.ZipFile,
) -> Tuple[List[Tuple[zipfile.ZipInfo, PurePosixPath]], int]:
    """在解压前验证并规范化压缩包成员。"""
    members = []
    for member in archive.infolist():
        if member.is_dir():
            continue

        original_path = PurePosixPath(member.filename)
        if original_path.is_absolute() or ".." in original_path.parts:
            raise ValueError("压缩包包含不安全的文件路径")

        normalized_path = PurePosixPath(_decode_zip_filename(member.filename))
        if normalized_path.is_absolute() or ".." in normalized_path.parts:
            raise ValueError("压缩包包含不安全的文件路径")
        if _is_ignored_archive_path(normalized_path):
            continue
        members.append((member, normalized_path))

    if not members:
        raise ValueError("压缩包中没有有效的 Skill 文件")
    if len(members) > MAX_SKILL_ARCHIVE_FILES:
        raise ValueError(f"压缩包文件过多，最多支持 {MAX_SKILL_ARCHIVE_FILES} 个")

    total_size = sum(member.file_size for member, _ in members)

    if total_size > MAX_SKILL_ARCHIVE_SIZE:
        raise ValueError("解压后文件大小超过 20MB 限制")

    # Finder 经常会将选中的文件夹本身一并压缩。如果所有有效文件都共享同一个外层目录，
    # 则移除该外层目录，使 <skill_id>/ 直接包含 SKILL.md。
    first_parts = {path.parts[0] for _, path in members if len(path.parts) > 1}
    if len(first_parts) == 1 and all(len(path.parts) > 1 for _, path in members):
        members = [
            (member, PurePosixPath(*path.parts[1:]))
            for member, path in members
        ]
    return members, total_size


def read_skill_archive(archive_content: bytes) -> Tuple[str, str, str]:
    """从 ZIP 压缩包中读取 SKILL.md 元数据和内容，无需写入磁盘。"""
    try:
        with zipfile.ZipFile(BytesIO(archive_content)) as archive:
            members, _ = _safe_archive_members(archive)
            skill_entry = next(
                ((member, path) for member, path in members if path.name.lower() == "skill.md"),
                None,
            )
            if not skill_entry:
                raise ValueError("压缩包中必须包含 SKILL.md")
            skill_file, skill_path = skill_entry
            try:
                content = archive.read(skill_file).decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError("SKILL.md 必须是 UTF-8 编码") from exc
    except zipfile.BadZipFile as exc:
        raise ValueError("无效的 ZIP 压缩包") from exc

    name, description = parse_skill_metadata(content, skill_path.parent.name or "Skill")
    return name, description, content


def extract_skill_archive(skill_id: int, archive_content: bytes) -> str:
    """将已验证的 Skill 压缩包安全地解压到 data/skills/<skill_id>/ 目录。"""
    target_dir = Path(SKILLS_DIR) / str(skill_id)
    try:
        with zipfile.ZipFile(BytesIO(archive_content)) as archive:
            members, _ = _safe_archive_members(archive)
            if target_dir.exists():
                shutil.rmtree(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)

            for member, relative_path in members:
                destination = target_dir / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, open(destination, "wb") as output:
                    shutil.copyfileobj(source, output)
    except Exception:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        raise
    return str(target_dir)


def parse_skill_metadata(content: str, default_name: str) -> Tuple[str, str]:
    """从 SKILL.md 文档中提取可选的标题和描述。"""
    name = default_name
    description = ""
    for line in content.split("\n")[:5]:
        line = line.strip()
        if line.startswith("# "):
            name = line[2:].strip() or name
        elif line.startswith("description:"):
            description = line.split(":", 1)[1].strip()
    return name, description


def _resolve_skill_file(skill_id: int, relative_path: str) -> Path:
    """解析用户提供的路径，并确保其严格限制在单个 Skill 文件夹内。"""
    skill_dir = (Path(SKILLS_DIR) / str(skill_id)).resolve()
    candidate = (skill_dir / relative_path).resolve()
    if skill_dir != candidate and skill_dir not in candidate.parents:
        raise ValueError("不允访问 Skill 目录之外的文件")
    return candidate


def find_skill_entrypoint(skill_id: int) -> Optional[Path]:
    """定位 SKILL.md 文件，优先使用规范化的 <skill_id>/SKILL.md 布局。"""
    skill_dir = Path(SKILLS_DIR) / str(skill_id)
    direct_entrypoint = skill_dir / "SKILL.md"
    if direct_entrypoint.is_file():
        return direct_entrypoint
    if not skill_dir.is_dir():
        return None

    # 兼容在外层目录规范化之前解压的压缩包。
    candidates = [
        path for path in skill_dir.rglob("*")
        if path.is_file()
        and path.name.lower() == "skill.md"
        and not _is_ignored_archive_path(PurePosixPath(*path.relative_to(skill_dir).parts))
    ]
    return min(candidates, key=lambda path: len(path.parts)) if candidates else None


def read_skill_entrypoint(skill_id: int, legacy_content: str = "") -> str:
    """从磁盘读取可执行的 Skill 指令，旧记录则回退使用数据库内容。"""
    entrypoint = find_skill_entrypoint(skill_id)
    if not entrypoint:
        log.warning("[Skill] id=%s 缺少 SKILL.md，使用数据库兼容内容", skill_id)
        return legacy_content
    if entrypoint.stat().st_size > MAX_EDITABLE_SKILL_FILE_SIZE:
        raise ValueError("SKILL.md 超过 1MB 限制")
    try:
        return entrypoint.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("SKILL.md 必须是 UTF-8 编码") from exc


def list_skill_files(skill_id: int) -> List[Dict]:
    """返回 Skill ZIP 包中解压出的文件，使用相对路径。"""
    skill_dir = Path(SKILLS_DIR) / str(skill_id)
    if not skill_dir.is_dir():
        return []
    return [
        {"path": str(path.relative_to(skill_dir)), "size": path.stat().st_size}
        for path in sorted(skill_dir.rglob("*"))
        if path.is_file()
    ]


def read_skill_file(skill_id: int, relative_path: str) -> str:
    path = _resolve_skill_file(skill_id, relative_path)
    if not path.is_file():
        raise ValueError("文件不存在")
    if path.stat().st_size > MAX_EDITABLE_SKILL_FILE_SIZE:
        raise ValueError("文件超过 1MB，不支持在页面中编辑")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("仅支持编辑 UTF-8 文本文件") from exc


def read_skill_action_manifest(skill_id: int) -> Dict:
    """从 Skill 包中读取可选的 skill.json 动作清单。"""
    skill_dir = Path(SKILLS_DIR) / str(skill_id)
    manifest_path = skill_dir / "skill.json"
    if not manifest_path.is_file():
        return {}
    if manifest_path.stat().st_size > MAX_EDITABLE_SKILL_FILE_SIZE:
        raise ValueError("skill.json 超过 1MB 限制")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("skill.json 必须是 UTF-8 编码") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"skill.json 不是合法 JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("skill.json 顶层必须是 JSON 对象")
    return data


async def update_skill_file(skill_id: int, user_id: int, relative_path: str, content: str) -> None:
    """保存 Skill 包中的文本文件。"""
    path = _resolve_skill_file(skill_id, relative_path)
    if not path.is_file():
        raise ValueError("文件不存在")
    if len(content.encode("utf-8")) > MAX_EDITABLE_SKILL_FILE_SIZE:
        raise ValueError("文件超过 1MB，不支持保存")
    path.write_text(content, encoding="utf-8")

    # 为旧代码/数据迁移保留兼容快照。运行时优先读取磁盘。
    if path.name.lower() == "skill.md":
        await execute(
            "UPDATE skills SET content=%s WHERE id=%s AND user_id=%s",
            (content, skill_id, user_id),
        )


async def delete_skill(skill_id: int, user_id: int) -> bool:
    result = await execute(
        "DELETE FROM skills WHERE id=%s AND user_id=%s",
        (skill_id, user_id)
    )
    if result > 0:
        skill_dir = Path(SKILLS_DIR) / str(skill_id)
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
    return result > 0


async def get_agent_skills(agent_id: int) -> List[Dict]:
    skills = await fetch_all(
        "SELECT s.* FROM skills s "
        "JOIN agent_skills ao ON s.id=ao.skill_id "
        "WHERE ao.agent_id=%s",
        (agent_id,)
    )
    for skill in skills:
        skill["content"] = read_skill_entrypoint(skill["id"], skill.get("content", ""))
    return skills
