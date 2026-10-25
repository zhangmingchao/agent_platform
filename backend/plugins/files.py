"""插件文件协议与 Runtime 文件存储衔接，只使用平台授权的文件 ID。"""

from __future__ import annotations

import hashlib
import mimetypes
import shutil
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from ..config import RUNTIME_DATA_DIR, PYTHON_RUNTIME_MAX_OUTPUT_MB
from ..database import execute
from ..runtime.models import RuntimeContext
from .packages import PluginArtifact
from .storage import private_workspace_path


class PreparedPluginFiles(BaseModel):
    """已授权的输入文件；references 保存文件 ID 到容器内副本路径的映射。"""

    references: dict[str, str] = Field(default_factory=dict, description="容器内只引用当前用户授权的文件副本")


def execution_directory(user_id: int, execution_id: str) -> Path:
    """由平台 user_id 与 execution_id 生成插件执行文件目录。"""
    if user_id <= 0 or len(execution_id) != 32 or any(character not in "0123456789abcdef" for character in execution_id):
        raise ValueError("插件执行身份无效")
    return private_workspace_path(user_id, "plugins", ".executions", execution_id)


async def prepare_files(context: RuntimeContext, execution_id: str, file_ids: list[str]) -> PreparedPluginFiles:
    """按 context 用户授权 file_ids，复制到 execution_id 输入目录，返回容器内文件引用映射。"""
    from ..services.runtime_service import get_runtime_files
    rows = await get_runtime_files(file_ids, context.user_id)
    workspace = execution_directory(context.user_id, execution_id)
    input_dir, output_dir = workspace / "input", workspace / "output"
    if input_dir.is_symlink() or output_dir.is_symlink():
        raise ValueError("插件输入输出目录不允许符号链接")
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    references: dict[str, str] = {}
    for row in rows:
        filename = row["id"] + "_" + Path(row["file_name"]).name
        source = Path(row["storage_path"])
        # 既有生成文件位于共享目录；读取前也拒绝链接，避免同用户代码诱导平台读取宿主文件。
        if Path(RUNTIME_DATA_DIR).resolve() not in source.resolve().parents or source.is_symlink() or any(parent.is_symlink() for parent in source.parents):
            raise ValueError("插件输入文件路径无效")
        shutil.copy2(source, input_dir / filename)
        references[row["id"]] = f"/workspaces/plugins/.executions/{execution_id}/input/{filename}"
    return PreparedPluginFiles(references=references)


async def register_artifacts(context: RuntimeContext, execution_id: str) -> list[PluginArtifact]:
    """登记 context 用户在 execution_id 下生成的普通文件，拒绝链接及超过输出总量的文件。"""
    output_dir = execution_directory(context.user_id, execution_id) / "output"
    if output_dir.is_symlink():
        raise ValueError("插件输出目录不允许符号链接")
    files: list[Path] = []
    size_total = 0
    for path in sorted(output_dir.rglob("*")):
        if path.is_symlink():
            raise ValueError("插件输出不能包含符号链接")
        if not path.is_file():
            continue
        size_total += path.stat().st_size
        if size_total > PYTHON_RUNTIME_MAX_OUTPUT_MB * 1024 * 1024 or len(files) >= 100:
            raise ValueError("插件生成文件超过大小或数量限制")
        files.append(path)
    artifacts: list[PluginArtifact] = []
    for path in files:
        artifact_id = str(uuid4())
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        await execute(
            "INSERT INTO runtime_files (id,user_id,session_id,execution_id,file_name,storage_path,mime_type,size_bytes,sha256,file_type,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'artifact',UTC_TIMESTAMP())",
            (artifact_id, context.user_id, context.session_id, execution_id, path.name, str(path), mimetypes.guess_type(path.name)[0] or "application/octet-stream", path.stat().st_size, digest.hexdigest()),
        )
        artifacts.append(PluginArtifact(file_id=artifact_id, name=path.name, size=path.stat().st_size, url=f"/api/runtime/files/{artifact_id}"))
    return artifacts
