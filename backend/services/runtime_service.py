"""本地 Python Runtime 的文件和代码执行服务。"""

import asyncio
import ast
import hashlib
import json
import mimetypes
import os
import shutil
import signal
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..config import (
    PYTHON_RUNTIME_MAX_OUTPUT_MB,
    PYTHON_RUNTIME_MAX_TIMEOUT_SECONDS,
    PYTHON_RUNTIME_MAX_UPLOAD_MB,
    PYTHON_RUNTIME_MEMORY_MB,
    PYTHON_RUNTIME_TIMEOUT_SECONDS,
    RUNTIME_DATA_DIR,
    SKILLS_DIR,
)
from ..database import execute, fetch_all, fetch_one
from ..runtime.models import RuntimeContext
from ..runtime.policy import validate_python_code


ALLOWED_UPLOAD_SUFFIXES = {
    ".csv", ".docx", ".json", ".md", ".pdf", ".txt", ".xls", ".xlsx",
}
MAX_RUNTIME_INPUT_FILES = 10
MAX_LOG_BYTES = 1024 * 1024


def _now() -> str:
    """返回适合写入 MySQL DATETIME 的 UTC 时间字符串。"""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _safe_filename(filename: str) -> str:
    """移除路径信息并生成可安全落盘的文件名。"""
    clean = Path(filename or "file").name.replace("\x00", "").strip()
    return clean[:200] or "file"


def _sha256(path: Path) -> str:
    """计算文件 SHA-256，用于审计和结果复现。"""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rewrite_virtual_input_paths(code: str, input_paths_by_name: Dict[str, str]) -> str:
    """将模型常用的 /mnt/data 虚拟路径改写为本次执行的输入路径。

    这只改写完全匹配已上传文件名的字符串常量，不放宽子进程的
    文件访问规则。推荐代码仍应优先使用 INPUT_FILES[file_id]。
    """
    aliases = {}
    for file_name, actual_path in input_paths_by_name.items():
        aliases[f"/mnt/data/{file_name}"] = actual_path
        aliases[f"sandbox:/mnt/data/{file_name}"] = actual_path

    class VirtualPathTransformer(ast.NodeTransformer):
        """仅替换 AST 中已知虚拟文件路径字符串。"""

        def visit_Constant(self, node: ast.Constant):
            """将匹配的字符串常量替换为 Runtime 输入文件路径。"""
            if isinstance(node.value, str) and node.value in aliases:
                return ast.copy_location(ast.Constant(value=aliases[node.value]), node)
            return node

    tree = VirtualPathTransformer().visit(ast.parse(code, mode="exec"))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


async def save_runtime_file(
    user_id: int,
    session_id: Optional[int],
    filename: str,
    content_type: Optional[str],
    content: bytes,
) -> Dict:
    """保存用户上传的 Runtime 输入文件并写入数据库记录。"""
    max_bytes = PYTHON_RUNTIME_MAX_UPLOAD_MB * 1024 * 1024
    if not content or len(content) > max_bytes:
        raise ValueError(f"文件不能为空且不能超过 {PYTHON_RUNTIME_MAX_UPLOAD_MB}MB")

    safe_name = _safe_filename(filename)
    if Path(safe_name).suffix.lower() not in ALLOWED_UPLOAD_SUFFIXES:
        raise ValueError("仅支持 CSV、Excel、Word、PDF、JSON、Markdown 和文本文件")

    file_id = str(uuid.uuid4())
    target_dir = Path(RUNTIME_DATA_DIR) / "files" / str(user_id) / file_id
    target_dir.mkdir(parents=True, exist_ok=False)
    target_path = target_dir / safe_name
    target_path.write_bytes(content)

    mime_type = content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    await execute(
        "INSERT INTO runtime_files "
        "(id, user_id, session_id, execution_id, file_name, storage_path, mime_type, "
        "size_bytes, sha256, file_type, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            file_id, user_id, session_id, None, safe_name, str(target_path),
            mime_type, len(content), _sha256(target_path), "input", _now(),
        ),
    )
    return {
        "id": file_id,
        "name": safe_name,
        "mimeType": mime_type,
        "size": len(content),
        "kind": "runtime_file",
    }


async def get_runtime_file(file_id: str, user_id: int) -> Optional[Dict]:
    """按用户和文件 ID 查询文件，避免跨用户读取。"""
    return await fetch_one(
        "SELECT id, user_id, session_id, execution_id, file_name, storage_path, "
        "mime_type, size_bytes, sha256, file_type, created_at "
        "FROM runtime_files WHERE id=%s AND user_id=%s",
        (file_id, user_id),
    )


async def get_runtime_files(file_ids: List[str], user_id: int) -> List[Dict]:
    """按传入顺序返回属于当前用户的 Runtime 文件。"""
    clean_ids = list(dict.fromkeys(str(item) for item in file_ids if item))
    if not clean_ids:
        return []
    if len(clean_ids) > MAX_RUNTIME_INPUT_FILES:
        raise ValueError(f"单次最多使用 {MAX_RUNTIME_INPUT_FILES} 个文件")
    placeholders = ",".join(["%s"] * len(clean_ids))
    rows = await fetch_all(
        "SELECT id, file_name, storage_path, mime_type, size_bytes, file_type "
        f"FROM runtime_files WHERE user_id=%s AND id IN ({placeholders})",
        (user_id, *clean_ids),
    )
    by_id = {row["id"]: row for row in rows}
    missing = [file_id for file_id in clean_ids if file_id not in by_id]
    if missing:
        raise ValueError("部分文件不存在或无权访问")
    return [by_id[file_id] for file_id in clean_ids]


def resolve_skill_script(skill_id: int, relative_path: str) -> Path:
    """解析 Skill 内的 Python 脚本，并阻止路径越界。"""
    skill_root = (Path(SKILLS_DIR) / str(skill_id)).resolve()
    script_path = (skill_root / relative_path).resolve()
    if skill_root != script_path and skill_root not in script_path.parents:
        raise ValueError("脚本路径超出 Skill 目录")
    if not script_path.is_file() or script_path.suffix.lower() != ".py":
        raise ValueError("Skill 脚本不存在或不是 .py 文件")
    if script_path.stat().st_size > 200_000:
        raise ValueError("Skill 脚本超过 200KB 限制")
    return script_path


def _limit_child_resources(timeout_seconds: int) -> None:
    """在 Unix 子进程启动后设置 CPU、内存、文件和进程数量限制。"""
    try:
        import resource

        memory_bytes = PYTHON_RUNTIME_MEMORY_MB * 1024 * 1024
        output_bytes = PYTHON_RUNTIME_MAX_OUTPUT_MB * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_CPU, (timeout_seconds, timeout_seconds + 1))
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (output_bytes, output_bytes))
        resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
        if hasattr(resource, "RLIMIT_NPROC"):
            resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
    except (ImportError, OSError, ValueError):
        # 不同操作系统对 resource 的支持不同，父进程的超时控制仍然生效。
        pass


def _read_limited(path: Path, limit: int = MAX_LOG_BYTES) -> str:
    """读取有限长度的日志，避免大输出占用过多内存。"""
    if not path.exists():
        return ""
    data = path.read_bytes()[:limit]
    return data.decode("utf-8", errors="replace")


async def _register_artifacts(
    context: RuntimeContext,
    execution_id: str,
    output_dir: Path,
) -> List[Dict]:
    """校验并登记 output 目录中由代码生成的文件。"""
    artifacts = []
    max_total = PYTHON_RUNTIME_MAX_OUTPUT_MB * 1024 * 1024
    total_size = 0
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == "result.json":
            continue
        total_size += path.stat().st_size
        if total_size > max_total:
            raise ValueError(f"生成文件总大小超过 {PYTHON_RUNTIME_MAX_OUTPUT_MB}MB")
        artifact_id = str(uuid.uuid4())
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        await execute(
            "INSERT INTO runtime_files "
            "(id, user_id, session_id, execution_id, file_name, storage_path, mime_type, "
            "size_bytes, sha256, file_type, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                artifact_id, context.user_id, context.session_id, execution_id,
                path.name, str(path), mime_type, path.stat().st_size,
                _sha256(path), "artifact", _now(),
            ),
        )
        artifacts.append({
            "fileId": artifact_id,
            "name": path.name,
            "mimeType": mime_type,
            "size": path.stat().st_size,
            "url": f"/api/runtime/files/{artifact_id}",
        })
    return artifacts


async def execute_python_code(
    context: RuntimeContext,
    code: str,
    input_file_ids: Optional[List[str]] = None,
    timeout_seconds: Optional[int] = None,
    *,
    source_type: str = "generated_code",
    skill_id: Optional[int] = None,
    arguments: Optional[Dict] = None,
) -> Dict:
    """在受限本地子进程中执行 Python，并返回结果、日志和 Artifact。"""
    validate_python_code(code)
    timeout = max(
        1,
        min(
            int(timeout_seconds or PYTHON_RUNTIME_TIMEOUT_SECONDS),
            PYTHON_RUNTIME_MAX_TIMEOUT_SECONDS,
        ),
    )
    files = await get_runtime_files(input_file_ids or [], context.user_id)
    execution_id = str(uuid.uuid4())
    workspace = Path(RUNTIME_DATA_DIR) / "executions" / str(context.user_id) / execution_id
    source_dir = workspace / "source"
    input_dir = workspace / "input"
    output_dir = workspace / "output"
    for directory in (source_dir, input_dir, output_dir):
        directory.mkdir(parents=True, exist_ok=False)

    source_path = source_dir / "main.py"
    source_path.write_text(code, encoding="utf-8")
    input_map = {}
    input_paths_by_name = {}
    for file_info in files:
        target_name = f"{file_info['id'][:8]}_{_safe_filename(file_info['file_name'])}"
        target = input_dir / target_name
        shutil.copy2(file_info["storage_path"], target)
        input_map[file_info["id"]] = str(target)
        input_paths_by_name[file_info["file_name"]] = str(target)

    # 兼容从通用代码沙箱习惯中生成的 /mnt/data/文件名 写法。
    executable_code = _rewrite_virtual_input_paths(code, input_paths_by_name)
    source_path.write_text(executable_code, encoding="utf-8")

    config_path = workspace / "runtime.json"
    config_path.write_text(
        json.dumps({
            "workspace": str(workspace),
            "sourcePath": str(source_path),
            "inputDir": str(input_dir),
            "outputDir": str(output_dir),
            "inputFiles": input_map,
            "arguments": arguments or {},
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    await execute(
        "INSERT INTO code_executions "
        "(id, user_id, session_id, workflow_run_id, workflow_step_id, node_id, "
        "source_type, skill_id, code_sha256, status, timeout_seconds, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            execution_id, context.user_id, context.session_id,
            context.workflow_run_id, context.workflow_step_id, context.node_id,
            source_type, skill_id, code_hash, "running", timeout, _now(),
        ),
    )

    stdout_path = workspace / "stdout.log"
    stderr_path = workspace / "stderr.log"
    status = "failed"
    exit_code = None
    error_text = ""
    result_data = None
    artifacts = []
    started_at = _now()
    await execute(
        "UPDATE code_executions SET started_at=%s WHERE id=%s",
        (started_at, execution_id),
    )

    try:
        env = {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "MPLBACKEND": "Agg",
        }
        child_runner = Path(__file__).resolve().parents[1] / "runtime" / "child_runner.py"
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-I",
                str(child_runner),
                str(config_path),
                cwd=str(workspace),
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True,
                preexec_fn=lambda: _limit_child_resources(timeout),
            )
            try:
                exit_code = await asyncio.wait_for(process.wait(), timeout=timeout + 2)
            except asyncio.TimeoutError:
                status = "timed_out"
                error_text = f"Python 执行超过 {timeout} 秒"
                os.killpg(process.pid, signal.SIGKILL)
                await process.wait()

        if status != "timed_out":
            if exit_code == 0:
                status = "completed"
                result_path = output_dir / "result.json"
                if result_path.exists():
                    result_data = json.loads(result_path.read_text(encoding="utf-8"))
                artifacts = await _register_artifacts(context, execution_id, output_dir)
            else:
                status = "failed"
                error_text = _read_limited(stderr_path) or f"Python 退出码：{exit_code}"
    except Exception as exc:
        status = "failed"
        error_text = str(exc)

    stdout = _read_limited(stdout_path)
    stderr = _read_limited(stderr_path)
    await execute(
        "UPDATE code_executions SET status=%s, exit_code=%s, stdout_text=%s, "
        "stderr_text=%s, result_json=%s, error_text=%s, finished_at=%s WHERE id=%s",
        (
            status, exit_code, stdout, stderr,
            json.dumps(result_data, ensure_ascii=False, default=str) if result_data is not None else None,
            error_text[:5000] if error_text else None, _now(), execution_id,
        ),
    )
    return {
        "executionId": execution_id,
        "status": status,
        "exitCode": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "error": error_text,
        "result": result_data,
        "artifacts": artifacts,
    }
