"""每用户一个私有容器的代码沙箱服务。

该服务是唯一允许访问 Docker Engine 的组件。workspace_id 仅映射为用户容器中的
目录，不会创建新的容器。
"""

import asyncio
import os
import re
import socket
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

import docker
from docker.errors import DockerException, ImageNotFound, NotFound
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


SERVICE_TOKEN = os.getenv("SANDBOX_SERVICE_TOKEN", "change-me-in-production")
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "agent-platform-python-sandbox:latest")
SANDBOX_DATA_ROOT = Path(os.getenv("SANDBOX_DATA_ROOT", "/runtime-data")).resolve()
SANDBOX_HOST_DATA_ROOT = os.getenv("SANDBOX_HOST_DATA_ROOT", "").strip()
SANDBOX_RUNTIME = os.getenv("SANDBOX_CONTAINER_RUNTIME", "").strip()
SANDBOX_MEMORY = os.getenv("SANDBOX_MEMORY", "512m")
SANDBOX_CPUS = float(os.getenv("SANDBOX_CPUS", "1"))
SANDBOX_PIDS_LIMIT = int(os.getenv("SANDBOX_PIDS_LIMIT", "128"))
SANDBOX_UID = int(os.getenv("SANDBOX_UID", "10001"))
SANDBOX_GID = int(os.getenv("SANDBOX_GID", "10001"))
IDLE_STOP_SECONDS = int(os.getenv("SANDBOX_IDLE_STOP_SECONDS", "1800"))
DELETE_AFTER_SECONDS = int(os.getenv("SANDBOX_DELETE_AFTER_SECONDS", "604800"))
CLEANUP_INTERVAL_SECONDS = int(os.getenv("SANDBOX_CLEANUP_INTERVAL_SECONDS", "60"))
MAX_CAPTURE_BYTES = int(os.getenv("SANDBOX_MAX_CAPTURE_BYTES", str(1024 * 1024)))

_SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
_docker = docker.from_env()
_user_locks: Dict[int, asyncio.Lock] = {}


class ExecutionRequest(BaseModel):
    executionId: str = Field(min_length=1, max_length=100)
    userId: int = Field(gt=0)
    workspaceId: str = Field(min_length=1, max_length=100)
    timeoutSeconds: int = Field(default=30, ge=1, le=30)
    configPath: str = Field(min_length=1, max_length=500)


async def require_internal_token(authorization: str = Header(default="")) -> None:
    if not SERVICE_TOKEN or authorization != f"Bearer {SERVICE_TOKEN}":
        raise HTTPException(status_code=401, detail="Sandbox Service 认证失败")


def _container_name(user_id: int) -> str:
    return f"agent-sandbox-user-{user_id}"


def _user_workspace_root(user_id: int) -> Path:
    root = (SANDBOX_DATA_ROOT / "users" / str(user_id) / "workspaces").resolve()
    expected = (SANDBOX_DATA_ROOT / "users" / str(user_id)).resolve()
    if expected not in root.parents:
        raise ValueError("用户工作目录不合法")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _host_data_root() -> Path:
    """取得 Docker daemon 可见的数据根目录，而不是 Manager 容器内路径。"""
    if SANDBOX_HOST_DATA_ROOT:
        return Path(SANDBOX_HOST_DATA_ROOT).resolve()
    try:
        current = _docker.containers.get(socket.gethostname())
        for mount in current.attrs.get("Mounts", []):
            if mount.get("Destination") == str(SANDBOX_DATA_ROOT):
                source = mount.get("Source")
                if source:
                    return Path(source).resolve()
    except DockerException:
        pass
    # Sandbox Manager 直接运行在宿主机时，两者就是同一路径。
    return SANDBOX_DATA_ROOT


def _host_workspace_root(user_id: int) -> Path:
    return _host_data_root() / "users" / str(user_id) / "workspaces"


def _activity_path(user_id: int) -> Path:
    return _user_workspace_root(user_id).parent / ".sandbox-last-active"


def _touch_activity(user_id: int) -> None:
    path = _activity_path(user_id)
    path.touch(exist_ok=True)
    os.utime(path, None)


def _validate_request_paths(request: ExecutionRequest) -> Path:
    if not _SAFE_ID.fullmatch(request.executionId) or not _SAFE_ID.fullmatch(request.workspaceId):
        raise ValueError("executionId 或 workspaceId 不合法")
    expected = f"/workspaces/{request.workspaceId}/executions/{request.executionId}/runtime.json"
    if request.configPath != expected:
        raise ValueError("configPath 与执行上下文不匹配")
    host_config = (
        _user_workspace_root(request.userId)
        / request.workspaceId / "executions" / request.executionId / "runtime.json"
    ).resolve()
    root = _user_workspace_root(request.userId)
    if root not in host_config.parents or not host_config.is_file():
        raise ValueError("执行配置不存在或超出用户目录")
    return host_config


def _prepare_permissions(host_config: Path) -> None:
    execution_root = host_config.parent
    for path in [execution_root, *execution_root.rglob("*")]:
        try:
            # 保留 API/Worker 创建文件时的 owner，只把 group 交给沙箱进程。
            # 这样宿主机后端和容器内 10001:10001 都能读取执行结果。
            os.chown(path, -1, SANDBOX_GID)
            path.chmod(0o770 if path.is_dir() else 0o660)
        except OSError as exc:
            raise RuntimeError(f"无法准备沙箱目录权限：{exc}") from exc


def _find_user_container(user_id: int):
    containers = _docker.containers.list(
        all=True,
        filters={"label": ["agent.platform.sandbox=true", f"agent.platform.user_id={user_id}"]},
    )
    return containers[0] if containers else None


def _ensure_user_container(user_id: int):
    container = _find_user_container(user_id)
    if container is not None:
        container.reload()
        if container.status != "running":
            container.start()
        return container

    _user_workspace_root(user_id)
    workspace_root = _host_workspace_root(user_id)
    kwargs = {
        "image": SANDBOX_IMAGE,
        "name": _container_name(user_id),
        "command": ["sleep", "infinity"],
        "detach": True,
        "network_disabled": True,
        "read_only": True,
        "user": f"{SANDBOX_UID}:{SANDBOX_GID}",
        "mem_limit": SANDBOX_MEMORY,
        "memswap_limit": SANDBOX_MEMORY,
        "nano_cpus": int(SANDBOX_CPUS * 1_000_000_000),
        "pids_limit": SANDBOX_PIDS_LIMIT,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "tmpfs": {"/tmp": "rw,noexec,nosuid,nodev,size=128m"},
        "volumes": {str(workspace_root): {"bind": "/workspaces", "mode": "rw"}},
        "environment": {
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "MPLBACKEND": "Agg",
        },
        "labels": {
            "agent.platform.sandbox": "true",
            "agent.platform.user_id": str(user_id),
        },
    }
    if SANDBOX_RUNTIME:
        kwargs["runtime"] = SANDBOX_RUNTIME
    try:
        return _docker.containers.run(**kwargs)
    except ImageNotFound as exc:
        raise RuntimeError(f"沙箱镜像不存在：{SANDBOX_IMAGE}") from exc


def _execute_sync(request: ExecutionRequest) -> dict:
    host_config = _validate_request_paths(request)
    _prepare_permissions(host_config)
    container = _ensure_user_container(request.userId)
    _touch_activity(request.userId)

    result = container.exec_run(
        [
            "timeout", "--signal=KILL", f"{request.timeoutSeconds}s",
            "python", "-I", "/opt/sandbox/child_runner.py", request.configPath,
        ],
        demux=True,
        workdir=str(Path(request.configPath).parent),
        user=f"{SANDBOX_UID}:{SANDBOX_GID}",
    )
    stdout_raw, stderr_raw = result.output or (b"", b"")
    stdout = (stdout_raw or b"")[:MAX_CAPTURE_BYTES].decode("utf-8", errors="replace")
    stderr = (stderr_raw or b"")[:MAX_CAPTURE_BYTES].decode("utf-8", errors="replace")
    exit_code = int(result.exit_code)
    timed_out = exit_code == 124
    return {
        "executionId": request.executionId,
        "containerId": container.id,
        "status": "timed_out" if timed_out else ("completed" if exit_code == 0 else "failed"),
        "exitCode": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "error": f"Python 执行超过 {request.timeoutSeconds} 秒" if timed_out else "",
    }


def _cleanup_sync() -> None:
    now = time.time()
    containers = _docker.containers.list(all=True, filters={"label": "agent.platform.sandbox=true"})
    for container in containers:
        user_id_raw = container.labels.get("agent.platform.user_id", "")
        if not user_id_raw.isdigit():
            continue
        activity = _activity_path(int(user_id_raw))
        last_active = activity.stat().st_mtime if activity.exists() else now
        idle_seconds = now - last_active
        container.reload()
        if idle_seconds >= DELETE_AFTER_SECONDS:
            container.remove(force=True)
        elif idle_seconds >= IDLE_STOP_SECONDS and container.status == "running":
            container.stop(timeout=10)


async def _cleanup_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(_cleanup_sync)
        except (DockerException, OSError):
            pass
        await asyncio.sleep(max(10, CLEANUP_INTERVAL_SECONDS))


@asynccontextmanager
async def lifespan(_: FastAPI):
    cleanup_task = asyncio.create_task(_cleanup_loop())
    try:
        yield
    finally:
        cleanup_task.cancel()
        await asyncio.gather(cleanup_task, return_exceptions=True)


app = FastAPI(title="Agent Platform Sandbox Service", lifespan=lifespan)


@app.get("/health")
async def health(_: None = Depends(require_internal_token)):
    try:
        version = await asyncio.to_thread(lambda: _docker.version().get("Version"))
        return {"status": "ok", "dockerVersion": version, "image": SANDBOX_IMAGE}
    except DockerException as exc:
        raise HTTPException(status_code=503, detail=f"Docker Engine 不可用：{exc}") from exc


@app.post("/v1/executions")
async def execute_code(
    request: ExecutionRequest,
    _: None = Depends(require_internal_token),
):
    lock = _user_locks.setdefault(request.userId, asyncio.Lock())
    async with lock:
        try:
            return await asyncio.to_thread(_execute_sync, request)
        except (DockerException, NotFound, OSError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
