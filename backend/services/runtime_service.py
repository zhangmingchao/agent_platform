"""本地 Python Runtime 的文件和代码执行服务。"""

import ast
import hashlib
import json
import mimetypes
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from redis.exceptions import RedisError

from ..config import (
    PYTHON_RUNTIME_MAX_OUTPUT_MB,
    PYTHON_RUNTIME_MAX_TIMEOUT_SECONDS,
    PYTHON_RUNTIME_MAX_UPLOAD_MB,
    PYTHON_RUNTIME_TIMEOUT_SECONDS,
    RUNTIME_DATA_DIR,
    RUNTIME_EXECUTION_RATE_LIMIT,
    RUNTIME_WORKER_QUEUE_WAIT_SECONDS,
    HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS,
    SKILLS_DIR,
)
from ..database import execute, fetch_all, fetch_one
from ..rate_limit import RateLimitRule, check_rate_limit
from ..runtime.models import RuntimeContext
from ..runtime.policy import validate_python_code
from ..runtime.sandbox_client import execute_in_sandbox
from ..runtime.queue import (
    cancel_runtime_task,
    enqueue_runtime_task,
    wait_runtime_result,
)


ALLOWED_UPLOAD_SUFFIXES = {
    ".csv", ".docx", ".json", ".md", ".pdf", ".txt", ".xls", ".xlsx",
}
MAX_RUNTIME_INPUT_FILES = 10
MAX_LOG_BYTES = 1024 * 1024
RUNTIME_EXECUTION_RULE = RateLimitRule(
    name="runtime-execution-user",
    limit=RUNTIME_EXECUTION_RATE_LIMIT,
    window_seconds=HIGH_RISK_RATE_LIMIT_WINDOW_SECONDS,
)


def _now() -> str:
    """返回适合写入 MySQL DATETIME 的 UTC 时间字符串。

    返回值结构：``YYYY-MM-DD HH:MM:SS`` 格式的字符串。
    """
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _safe_filename(filename: str) -> str:
    """移除路径信息并生成可安全落盘的文件名。

    返回值结构：不包含目录和空字节、最长 200 个字符的文件名字符串。
    """
    clean = Path(filename or "file").name.replace("\x00", "").strip()
    return clean[:200] or "file"


def _workspace_id(context: RuntimeContext) -> str:
    """生成安全的工作空间 ID；它只对应用户容器内的目录。"""
    raw = str(context.workspace_id or "").strip()
    if not raw:
        if context.session_id is not None:
            raw = f"session-{context.session_id}"
        elif context.workflow_run_id is not None:
            raw = f"workflow-run-{context.workflow_run_id}"
        else:
            raw = "default"
    safe = re.sub(r"[^a-zA-Z0-9_-]", "-", raw).strip("-_")[:100]
    if not safe:
        raise ValueError("workspace_id 不合法")
    return safe


def _sha256(path: Path) -> str:
    """计算文件 SHA-256，用于审计和结果复现。

    返回值结构：64 位小写十六进制摘要字符串。
    """
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rewrite_virtual_input_paths(code: str, input_paths_by_name: Dict[str, str]) -> str:
    """将模型常用的 /mnt/data 虚拟路径改写为本次执行的输入路径。

    这只改写完全匹配已上传文件名的字符串常量，不放宽子进程的
    文件访问规则。推荐代码仍应优先使用 INPUT_FILES[file_id]。

    返回值结构：改写完成后的完整 Python 源码字符串。
    """
    aliases = {}
    for file_name, actual_path in input_paths_by_name.items():
        aliases[f"/mnt/data/{file_name}"] = actual_path
        aliases[f"sandbox:/mnt/data/{file_name}"] = actual_path

    class VirtualPathTransformer(ast.NodeTransformer):
        """仅替换 AST 中已知虚拟文件路径字符串。"""

        def visit_Constant(self, node: ast.Constant) -> ast.AST:
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
    """保存用户上传的 Runtime 输入文件并写入数据库记录。

    返回值结构：``{"id": str, "name": str, "mimeType": str,
    "size": int, "kind": "runtime_file"}``。
    """
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
    """按用户和文件 ID 查询文件，避免跨用户读取。

    返回值结构：找到时返回包含文件元数据和 storage_path 的字典；未找到时返回 ``None``。
    """
    return await fetch_one(
        "SELECT id, user_id, session_id, execution_id, file_name, storage_path, "
        "mime_type, size_bytes, sha256, file_type, created_at "
        "FROM runtime_files WHERE id=%s AND user_id=%s",
        (file_id, user_id),
    )


async def get_runtime_files(file_ids: List[str], user_id: int) -> List[Dict]:
    """按传入顺序返回属于当前用户的 Runtime 文件。

    返回值结构：文件元数据字典列表，顺序与去重后的 file_ids 一致；空输入返回空列表。
    """
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
    """解析 Skill 内的 Python 脚本，并阻止路径越界。

    返回值结构：通过目录边界、扩展名和大小校验后的绝对 ``Path`` 对象。
    """
    skill_root = (Path(SKILLS_DIR) / str(skill_id)).resolve()
    script_path = (skill_root / relative_path).resolve()
    if skill_root != script_path and skill_root not in script_path.parents:
        raise ValueError("脚本路径超出 Skill 目录")
    if not script_path.is_file() or script_path.suffix.lower() != ".py":
        raise ValueError("Skill 脚本不存在或不是 .py 文件")
    if script_path.stat().st_size > 200_000:
        raise ValueError("Skill 脚本超过 200KB 限制")
    return script_path


def _read_limited(path: Path, limit: int = MAX_LOG_BYTES) -> str:
    """读取有限长度的日志，避免大输出占用过多内存。

    返回值结构：UTF-8 日志字符串；文件不存在时返回空字符串。
    """
    if not path.exists():
        return ""
    data = path.read_bytes()[:limit]
    return data.decode("utf-8", errors="replace")


async def _register_artifacts(
    context: RuntimeContext,
    execution_id: str,
    output_dir: Path,
) -> List[Dict]:
    """校验并登记 output 目录中由代码生成的文件。

    返回值结构：Artifact 字典列表，每项包含 fileId、name、mimeType、size 和 url。
    """
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


def _runtime_context_to_dict(context: RuntimeContext) -> Dict:
    """将不可变 RuntimeContext 转换成可写入 Redis 的普通字典。

    返回值结构：
    ``{"user_id": int, "workspace_id": str|None, "session_id": int|None, "workflow_run_id": int|None,
    "workflow_step_id": int|None, "node_id": str|None}``。
    """
    return {
        "user_id": context.user_id,
        "workspace_id": context.workspace_id,
        "session_id": context.session_id,
        "workflow_run_id": context.workflow_run_id,
        "workflow_step_id": context.workflow_step_id,
        "node_id": context.node_id,
    }


async def prepare_runtime_execution(
    context: RuntimeContext,
    code: str,
    input_file_ids: Optional[List[str]] = None,
    timeout_seconds: Optional[int] = None,
    *,
    source_type: str = "generated_code",
    skill_id: Optional[int] = None,
    arguments: Optional[Dict] = None,
) -> Dict:
    """校验代码和文件，并准备一条可由 Runtime Worker 消费的任务。

    本方法运行在 FastAPI 进程中，只负责执行前准备，不启动 Python 子进程。代码会
    保存到独立工作目录，输入文件会复制到 input 目录，数据库状态会记录为 queued。

    返回值结构：
    ``{"executionId": str, "userId": int, "timeoutSeconds": int, "context": dict}``。
    该字典不包含完整代码，只包含 Worker 定位工作目录和记录审计上下文所需的数据。
    """
    # Runtime 执行消耗较高且运行不可信代码，必须在准备文件前完成分布式限流。
    try:
        rate_limit = await check_rate_limit(RUNTIME_EXECUTION_RULE, str(context.user_id))
    except RedisError as exc:
        raise RuntimeError("Runtime 安全限流服务暂时不可用") from exc
    if not rate_limit.allowed:
        raise ValueError(
            f"Python Runtime 执行过于频繁，请在 {rate_limit.retry_after_seconds} 秒后重试"
        )

    # 第 1 步：入队前进行 AST 静态校验，拒绝危险导入和调用。
    validate_python_code(code)

    # 第 2 步：计算实际超时时间。最少为 1 秒，最大不超过系统配置上限。
    timeout = max(
        1,
        min(
            int(timeout_seconds or PYTHON_RUNTIME_TIMEOUT_SECONDS),
            PYTHON_RUNTIME_MAX_TIMEOUT_SECONDS,
        ),
    )

    # 第 3 步：根据 user_id 查询输入文件。文件不存在或属于其他用户时直接拒绝。
    files = await get_runtime_files(input_file_ids or [], context.user_id)

    # 第 4 步：为每次执行创建唯一 ID 和独立工作目录，供 Worker 后续使用。
    execution_id = str(uuid.uuid4())
    workspace_id = _workspace_id(context)
    user_root = Path(RUNTIME_DATA_DIR) / "users" / str(context.user_id)
    workspace = user_root / "workspaces" / workspace_id / "executions" / execution_id
    source_dir = workspace / "source"
    input_dir = workspace / "input"
    output_dir = workspace / "output"
    for directory in (source_dir, input_dir, output_dir):
        directory.mkdir(parents=True, exist_ok=False)

    # source/main.py 保存 Worker 将要交给子进程执行的 Python 源码。
    source_path = source_dir / "main.py"

    # 第 5 步：把用户文件复制到本次执行的 input 目录。
    # input_map 最终会在子进程内暴露为 INPUT_FILES，结构为：
    # {"文件ID": "本次工作目录内的文件路径"}。
    container_workspace = Path("/workspaces") / workspace_id / "executions" / execution_id
    input_map = {}
    input_paths_by_name = {}
    for file_info in files:
        target_name = f"{file_info['id'][:8]}_{_safe_filename(file_info['file_name'])}"
        target = input_dir / target_name
        shutil.copy2(file_info["storage_path"], target)
        container_target = container_workspace / "input" / target_name
        input_map[file_info["id"]] = str(container_target)
        input_paths_by_name[file_info["file_name"]] = str(container_target)

    # 第 6 步：兼容模型按通用沙箱习惯生成的 /mnt/data/文件名 写法。
    # 只替换与本次已上传文件名完全匹配的字符串，不会放宽读取权限。
    executable_code = _rewrite_virtual_input_paths(code, input_paths_by_name)
    source_path.write_text(executable_code, encoding="utf-8")

    # 第 7 步：生成父子进程之间的运行配置文件。child_runner.py 会读取它，
    # 并向被执行代码提供 INPUT_DIR、OUTPUT_DIR、INPUT_FILES 和 RUNTIME_ARGS。
    config_path = workspace / "runtime.json"
    config_path.write_text(
        json.dumps({
            "workspace": str(container_workspace),
            "sourcePath": str(container_workspace / "source" / "main.py"),
            "inputDir": str(container_workspace / "input"),
            "outputDir": str(container_workspace / "output"),
            "inputFiles": input_map,
            "arguments": arguments or {},
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    # 第 8 步：入队前创建 queued 记录。代码仅保存 SHA-256 摘要用于审计，
    # 不把完整源码写入 code_executions 表。
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    await execute(
        "INSERT INTO code_executions "
        "(id, user_id, workspace_id, session_id, workflow_run_id, workflow_step_id, node_id, "
        "source_type, skill_id, code_sha256, status, timeout_seconds, created_at) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            execution_id, context.user_id, workspace_id, context.session_id,
            context.workflow_run_id, context.workflow_step_id, context.node_id,
            source_type, skill_id, code_hash, "queued", timeout, _now(),
        ),
    )

    return {
        "executionId": execution_id,
        "userId": context.user_id,
        "workspaceId": workspace_id,
        "timeoutSeconds": timeout,
        "context": _runtime_context_to_dict(context),
    }


async def execute_runtime_task(task: Dict) -> Dict:
    """由独立 Runtime Worker 执行一条已经准备完成的任务。

    参数 task 的结构由 ``prepare_runtime_execution`` 产生。Worker 根据 executionId、
    userId 和 workspaceId 定位工作目录，再交给独立 Sandbox Service 执行。

    返回值结构：
    ``{"executionId": str, "status": str, "exitCode": int|None, "stdout": str,
    "stderr": str, "error": str, "result": object|None, "artifacts": list}``。
    status 可能为 completed、failed 或 timed_out。
    """
    execution_id = str(task["executionId"])
    user_id = int(task["userId"])
    workspace_id = str(task["workspaceId"])
    timeout = max(1, min(int(task["timeoutSeconds"]), PYTHON_RUNTIME_MAX_TIMEOUT_SECONDS))
    context = RuntimeContext(**task["context"])
    if context.user_id != user_id:
        raise ValueError("Runtime 任务用户上下文不一致")
    if _workspace_id(context) != workspace_id:
        raise ValueError("Runtime 任务工作空间上下文不一致")

    # 一个用户只有一个容器；workspace_id 只对应该容器内的独立工作目录。
    execution_root = (
        Path(RUNTIME_DATA_DIR) / "users" / str(user_id)
        / "workspaces" / workspace_id / "executions"
    ).resolve()
    workspace = (execution_root / execution_id).resolve()
    if execution_root not in workspace.parents or not workspace.is_dir():
        raise ValueError("Runtime 任务工作目录不存在或不合法")

    source_path = workspace / "source" / "main.py"
    output_dir = workspace / "output"
    config_path = workspace / "runtime.json"
    stdout_path = workspace / "stdout.log"
    stderr_path = workspace / "stderr.log"
    if not source_path.is_file() or not config_path.is_file() or not output_dir.is_dir():
        raise ValueError("Runtime 任务文件不完整")

    # Worker 再次校验落盘代码，避免排队期间代码文件被意外修改。
    validate_python_code(source_path.read_text(encoding="utf-8"))

    status = "failed"
    exit_code = None
    error_text = ""
    result_data = None
    artifacts = []
    await execute(
        "UPDATE code_executions SET status=%s, started_at=%s WHERE id=%s",
        ("running", _now(), execution_id),
    )

    try:
        # Worker 和 Docker 解耦：只有 Sandbox Service 可以访问 Docker Engine。
        sandbox_result = await execute_in_sandbox({
            "executionId": execution_id,
            "userId": user_id,
            "workspaceId": workspace_id,
            "timeoutSeconds": timeout,
            "configPath": f"/workspaces/{workspace_id}/executions/{execution_id}/runtime.json",
        })
        exit_code = sandbox_result.get("exitCode")
        stdout_path.write_text(str(sandbox_result.get("stdout") or ""), encoding="utf-8")
        stderr_path.write_text(str(sandbox_result.get("stderr") or ""), encoding="utf-8")
        if sandbox_result.get("status") == "timed_out":
            status = "timed_out"
            error_text = str(
                sandbox_result.get("error") or f"Python 执行超过 {timeout} 秒"
            )

        # 根据退出码解析执行结果。0 表示 Python 正常结束；
        # 非 0 表示代码异常、审计钩子拒绝或其他运行错误。
        if status != "timed_out":
            if exit_code == 0:
                status = "completed"
                # child_runner 会把脚本中的 result 变量写成 output/result.json。
                result_path = output_dir / "result.json"
                if result_path.exists():
                    result_data = json.loads(result_path.read_text(encoding="utf-8"))
                # output 中除 result.json 以外的文件都会登记为可下载 Artifact。
                artifacts = await _register_artifacts(context, execution_id, output_dir)
            else:
                status = "failed"
                error_text = (
                    str(sandbox_result.get("error") or "")
                    or _read_limited(stderr_path)
                    or f"Python 退出码：{exit_code}"
                )
    except Exception as exc:
        # 捕获沙箱服务不可用、结果 JSON 损坏或 Artifact 登记失败等调度异常。
        status = "failed"
        error_text = str(exc)

    # 有限读取 stdout/stderr，防止恶意或错误代码产生过大日志。
    stdout = _read_limited(stdout_path)
    stderr = _read_limited(stderr_path)

    # 无论成功、失败还是超时，都将最终状态和日志更新到 code_executions。
    await execute(
        "UPDATE code_executions SET status=%s, exit_code=%s, sandbox_container_id=%s, stdout_text=%s, "
        "stderr_text=%s, result_json=%s, error_text=%s, finished_at=%s WHERE id=%s",
        (
            status, exit_code,
            sandbox_result.get("containerId") if "sandbox_result" in locals() else None,
            stdout, stderr,
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
    """准备任务、提交到 Redis，并等待独立 Runtime Worker 返回结果。

    这是 ``ExecutePython`` 和 ``RunSkillScript`` 共同调用的 API 侧入口。它不再
    创建 Python 子进程，只负责准备任务、入队及通过 Redis 结果通道等待 Worker。

    返回值结构：
    ``{"executionId": str, "status": str, "exitCode": int|None, "stdout": str,
    "stderr": str, "error": str, "result": object|None, "artifacts": list}``。
    如果在允许的排队时间内没有 Worker 返回结果，status 为 failed，error 会说明
    Runtime Worker 未启动、繁忙或失联。
    """
    task = await prepare_runtime_execution(
        context=context,
        code=code,
        input_file_ids=input_file_ids,
        timeout_seconds=timeout_seconds,
        source_type=source_type,
        skill_id=skill_id,
        arguments=arguments,
    )
    execution_id = task["executionId"]
    await enqueue_runtime_task(task)

    # 等待时间由“最大排队时间 + 代码执行超时 + Worker 收尾缓冲”组成。
    wait_seconds = RUNTIME_WORKER_QUEUE_WAIT_SECONDS + task["timeoutSeconds"] + 10
    result = await wait_runtime_result(execution_id, wait_seconds)
    if result is not None:
        return result

    # 没有 Worker 或队列长期拥堵时给尚未执行的任务写取消标记，避免稍后突然执行。
    error_text = (
        f"等待 Runtime Worker 超过 {wait_seconds} 秒；"
        "请确认已启动 python -m backend.runtime_worker"
    )
    await cancel_runtime_task(execution_id, PYTHON_RUNTIME_MAX_TIMEOUT_SECONDS + 60)
    await execute(
        "UPDATE code_executions SET status=%s, error_text=%s, finished_at=%s "
        "WHERE id=%s AND status=%s",
        ("failed", error_text, _now(), execution_id, "queued"),
    )
    return {
        "executionId": execution_id,
        "status": "failed",
        "exitCode": None,
        "stdout": "",
        "stderr": "",
        "error": error_text,
        "result": None,
        "artifacts": [],
    }
