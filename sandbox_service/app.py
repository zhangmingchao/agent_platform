"""每用户一个私有容器的代码沙箱服务。

该服务是唯一允许访问 Docker Engine 的组件。workspace_id 仅映射为用户容器中的
目录，不会创建新的容器。

架构定位：
    FastAPI (:20000)  →  Redis 队列  →  Runtime Worker  →  Sandbox Service (:20002)  →  Docker 容器
    准备任务            中转任务         取任务+调Sandbox      管容器+exec_run          执行代码

本服务的职责边界：
    1. 接收 Worker 的 HTTP 请求（Bearer Token 认证）
    2. 校验路径安全（防止路径越界）
    3. 准备文件权限（让容器内 10001 用户可读写）
    4. 管理用户容器（按 user_id 隔离，每用户一个）
    5. 在容器内 exec_run 执行 child_runner.py
    6. 后台清理空闲容器（30 分钟停止，7 天删除）
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

# ── 配置项（全部通过环境变量注入，生产部署时必须覆盖默认值）──────────────────

SERVICE_TOKEN = os.getenv("SANDBOX_SERVICE_TOKEN", "change-me-in-production")
# 沙箱镜像名，由 sandbox.Dockerfile 构建，预装 pandas/numpy/openpyxl 等
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "agent-platform-python-sandbox:latest")
# Sandbox Service 容器内的数据根目录（与 Worker 共享的 volume 挂载点）
SANDBOX_DATA_ROOT = Path(os.getenv("SANDBOX_DATA_ROOT", "/runtime-data")).resolve()
# Docker daemon 可见的数据根目录；当 Sandbox 运行在容器内时与上面的路径不同
SANDBOX_HOST_DATA_ROOT = os.getenv("SANDBOX_HOST_DATA_ROOT", "").strip()
# 可选容器运行时，Linux 生产环境可设为 runsc（gVisor）增强隔离
SANDBOX_RUNTIME = os.getenv("SANDBOX_CONTAINER_RUNTIME", "").strip()
# 容器资源限制
SANDBOX_MEMORY = os.getenv("SANDBOX_MEMORY", "512m")           # 内存上限
SANDBOX_CPUS = float(os.getenv("SANDBOX_CPUS", "1"))          # CPU 核数
SANDBOX_PIDS_LIMIT = int(os.getenv("SANDBOX_PIDS_LIMIT", "128"))  # 最大进程数
# 容器内运行用户（非 root，UID:GID = 10001:10001）
SANDBOX_UID = int(os.getenv("SANDBOX_UID", "10001"))
SANDBOX_GID = int(os.getenv("SANDBOX_GID", "10001"))
# 容器生命周期管理
IDLE_STOP_SECONDS = int(os.getenv("SANDBOX_IDLE_STOP_SECONDS", "1800"))      # 空闲 30 分钟停止
DELETE_AFTER_SECONDS = int(os.getenv("SANDBOX_DELETE_AFTER_SECONDS", "604800"))  # 7 天删除
CLEANUP_INTERVAL_SECONDS = int(os.getenv("SANDBOX_CLEANUP_INTERVAL_SECONDS", "60"))  # 每 60 秒检查
# stdout/stderr 最大捕获字节数（1MB），防止恶意代码产生过大日志
MAX_CAPTURE_BYTES = int(os.getenv("SANDBOX_MAX_CAPTURE_BYTES", str(1024 * 1024)))

# 安全的正则：executionId 和 workspaceId 只允许字母/数字/下划线/连字符
_SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
# Docker 客户端单例，通过 DOCKER_HOST 环境变量连接 Docker daemon
_docker = docker.from_env()
# 每用户一把异步锁，保证同一用户的代码执行是串行的（避免容器 exec_run 竞争）
_user_locks: Dict[int, asyncio.Lock] = {}


class ExecutionRequest(BaseModel):
    """Worker 提交给 Sandbox Service 的执行请求结构。

    这些字段由 prepare_runtime_execution() 在 FastAPI 进程中生成，
    经 Redis 队列传给 Worker，再由 Worker 通过 HTTP POST 传到这里。
    """
    executionId: str = Field(min_length=1, max_length=100)   # UUID，唯一标识一次执行
    userId: int = Field(gt=0)                                # 用户 ID，用于容器隔离
    workspaceId: str = Field(min_length=1, max_length=100)    # 工作空间 ID，映射容器内目录
    timeoutSeconds: int = Field(default=30, ge=1, le=30)     # 执行超时（秒），硬限制 30s
    configPath: str = Field(min_length=1, max_length=500)     # runtime.json 在容器内的路径


async def require_internal_token(authorization: str = Header(default="")) -> None:
    """FastAPI 依赖项：校验 Bearer Token，拒绝未授权调用。

    只有知道 SERVICE_TOKEN 的 Worker 才能调用本服务，
    防止外部直接通过 :20002 端口执行任意代码。
    """
    if not SERVICE_TOKEN or authorization != f"Bearer {SERVICE_TOKEN}":
        raise HTTPException(status_code=401, detail="Sandbox Service 认证失败")


def _container_name(user_id: int) -> str:
    """生成用户容器的名称，格式：agent-sandbox-user-{user_id}。"""
    return f"agent-sandbox-user-{user_id}"


def _user_workspace_root(user_id: int) -> Path:
    """返回 Sandbox Service 容器内该用户的工作空间根目录。

    路径结构：/runtime-data/users/{user_id}/workspaces/
    同时做目录遍历防护：确保 root 是 expected 的子目录。
    """
    root = (SANDBOX_DATA_ROOT / "users" / str(user_id) / "workspaces").resolve()
    expected = (SANDBOX_DATA_ROOT / "users" / str(user_id)).resolve()
    if expected not in root.parents:
        raise ValueError("用户工作目录不合法")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _host_data_root() -> Path:
    """取得 Docker daemon 可见的数据根目录，而不是 Manager 容器内路径。

    为什么要区分：
    - 当 Sandbox Service 运行在容器内时，它看到的 /runtime-data 是容器内路径
    - 但 Docker daemon 创建子容器时，volume 挂载需要用宿主机路径
    - 所以需要通过 inspect 自己的 Mounts 反查宿主机路径

    三种情况：
    1. 显式配置了 SANDBOX_HOST_DATA_ROOT → 直接用
    2. Sandbox 运行在容器内 → 查自身容器的 Mounts 反推宿主机路径
    3. Sandbox 直接运行在宿主机 → 两个路径相同
    """
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
    """返回宿主机上该用户的工作空间路径（用于 Docker volume 挂载）。"""
    return _host_data_root() / "users" / str(user_id) / "workspaces"


def _activity_path(user_id: int) -> Path:
    """返回记录用户最后活跃时间的文件路径（用于空闲容器清理）。"""
    return _user_workspace_root(user_id).parent / ".sandbox-last-active"


def _touch_activity(user_id: int) -> None:
    """更新用户最后活跃时间戳（touch 文件的 mtime）。"""
    path = _activity_path(user_id)
    path.touch(exist_ok=True)
    os.utime(path, None)


def _validate_request_paths(request: ExecutionRequest) -> Path:
    """校验请求中的所有路径参数，防止路径遍历攻击。

    三层校验：
    1. executionId 和 workspaceId 必须匹配安全正则（只允许字母/数字/下划线/连字符）
    2. configPath 必须符合预期格式 /workspaces/{wid}/executions/{eid}/runtime.json
    3. 解析后的宿主机路径必须在用户工作空间目录内，且文件实际存在
    """
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
    """调整执行目录的文件权限，让容器内 10001:10001 用户可读写。

    宿主机上的文件由 API/Worker 进程创建（owner 通常是 root 或运行用户），
    容器内以 10001:10001 运行，需要 group 权限才能读写。
    - 目录：770（rwxrwx---）→ owner 和 group 可读写执行
    - 文件：660（rw-rw----）→ owner 和 group 可读写
    """
    execution_root = host_config.parent
    for path in [execution_root, *execution_root.rglob("*")]:
        try:
            # chown -1 表示不改变 owner，只把 group 改为 10001
            os.chown(path, -1, SANDBOX_GID)
            path.chmod(0o770 if path.is_dir() else 0o660)
        except OSError as exc:
            raise RuntimeError(f"无法准备沙箱目录权限：{exc}") from exc


def _find_user_container(user_id: int):
    """通过 Docker label 查找该用户已有的沙箱容器。

    用 label 过滤而不是用容器名，更可靠（容器名可能被手动改）。
    """
    containers = _docker.containers.list(
        all=True,
        filters={"label": ["agent.platform.sandbox=true", f"agent.platform.user_id={user_id}"]},
    )
    return containers[0] if containers else None


def _ensure_user_container(user_id: int):
    """确保该用户有一个运行中的沙箱容器（不存在就创建）。

    容器策略：
    - 每用户一个容器，复用（不每次执行都新建/销毁）
    - 已存在但已停止 → start() 启动
    - 不存在 → docker run 创建

    安全约束：
    - network_disabled: 无网络（防止数据外传/反向 Shell）
    - read_only: 根文件系统只读（只有 /workspaces 和 /tmp 可写）
    - cap_drop ALL + no-new-privileges: 丢弃所有 Linux capabilities
    - mem_limit/pids_limit: 防止资源耗尽
    - 非 root 用户 10001:10001
    """
    container = _find_user_container(user_id)
    if container is not None:
        container.reload()  # 刷新容器状态（可能被其他进程停止/启动）
        if container.status != "running":
            container.start()
        return container

    # 确保用户工作目录存在
    _user_workspace_root(user_id)
    # 用宿主机路径做 volume 挂载（Docker daemon 看到的是宿主机路径）
    workspace_root = _host_workspace_root(user_id)
    kwargs = {
        "image": SANDBOX_IMAGE,
        "name": _container_name(user_id),
        "command": ["sleep", "infinity"],       # 容器启动后睡眠，等 exec_run 来调用
        "detach": True,                        # 后台运行
        "network_disabled": True,              # ★ 无网络
        "read_only": True,                     # ★ 根文件系统只读
        "user": f"{SANDBOX_UID}:{SANDBOX_GID}",  # ★ 非 root
        "mem_limit": SANDBOX_MEMORY,           # 内存上限 512MB
        "memswap_limit": SANDBOX_MEMORY,       # swap 也限制（等于禁用 swap）
        "nano_cpus": int(SANDBOX_CPUS * 1_000_000_000),  # CPU 1 核
        "pids_limit": SANDBOX_PIDS_LIMIT,     # 最大进程数 128
        "cap_drop": ["ALL"],                   # ★ 丢弃所有 capabilities
        "security_opt": ["no-new-privileges:true"],  # ★ 禁止提权
        "tmpfs": {"/tmp": "rw,noexec,nosuid,nodev,size=128m"},  # /tmp 限制 128MB
        "volumes": {str(workspace_root): {"bind": "/workspaces", "mode": "rw"}},  # 挂载用户数据
        "environment": {
            "PYTHONIOENCODING": "utf-8",       # 强制 UTF-8 输出
            "PYTHONDONTWRITEBYTECODE": "1",    # 不生成 .pyc
            "MPLBACKEND": "Agg",               # matplotlib 无界面模式
        },
        "labels": {
            "agent.platform.sandbox": "true",  # 标记为沙箱容器
            "agent.platform.user_id": str(user_id),  # 标记所属用户
        },
    }
    if SANDBOX_RUNTIME:
        kwargs["runtime"] = SANDBOX_RUNTIME    # 可选 gVisor (runsc)
    try:
        return _docker.containers.run(**kwargs)
    except ImageNotFound as exc:
        raise RuntimeError(f"沙箱镜像不存在：{SANDBOX_IMAGE}") from exc


def _execute_sync(request: ExecutionRequest) -> dict:
    """在用户容器内同步执行 Python 代码（阻塞函数，需通过 asyncio.to_thread 调用）。

    执行流程：
    1. 校验路径安全
    2. 准备文件权限
    3. 找到/创建用户容器
    4. 更新活跃时间
    5. container.exec_run 执行 child_runner.py
    6. 收集 stdout/stderr 并截断到 1MB

    返回值结构：
    {
        "executionId": "uuid",
        "containerId": "docker-container-id",
        "status": "completed | failed | timed_out",
        "exitCode": 0,
        "stdout": "标准输出",
        "stderr": "标准错误",
        "error": "失败或超时原因"
    }
    """
    host_config = _validate_request_paths(request)  # 路径校验
    _prepare_permissions(host_config)               # 权限准备
    container = _ensure_user_container(request.userId)  # 获取容器
    _touch_activity(request.userId)                  # 更新活跃时间

    # 在容器内执行：timeout 超时杀进程 → python -I 隔离环境 → child_runner.py 执行器
    result = container.exec_run(
        [
            "timeout", "--signal=KILL", f"{request.timeoutSeconds}s",  # 超时后 SIGKILL
            "python", "-I",                                           # -I 忽略 PYTHON 相关环境变量
            "/opt/sandbox/child_runner.py",                           # 容器内的代码执行器
            request.configPath,                                       # runtime.json 配置文件路径
        ],
        demux=True,                                                   # stdout 和 stderr 分开返回
        workdir=str(Path(request.configPath).parent),                 # 切换到执行目录
        user=f"{SANDBOX_UID}:{SANDBOX_GID}",                          # 以 10001 用户执行
    )
    # demux=True 时 output 是 (stdout_bytes, stderr_bytes) 元组
    stdout_raw, stderr_raw = result.output or (b"", b"")
    # 截断到 MAX_CAPTURE_BYTES 防止过大输出
    stdout = (stdout_raw or b"")[:MAX_CAPTURE_BYTES].decode("utf-8", errors="replace")
    stderr = (stderr_raw or b"")[:MAX_CAPTURE_BYTES].decode("utf-8", errors="replace")
    exit_code = int(result.exit_code)
    # timeout 命令超时返回 124
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
    """同步清理空闲容器（阻塞函数，需通过 asyncio.to_thread 调用）。

    清理策略：
    - 遍历所有带 agent.platform.sandbox=true 标签的容器
    - 空闲超过 30 分钟 → 停止容器（释放内存，保留文件）
    - 空闲超过 7 天 → 强制删除容器（防止堆积）
    - 空闲时间通过 .sandbox-last-active 文件的 mtime 判断
    """
    now = time.time()
    containers = _docker.containers.list(all=True, filters={"label": "agent.platform.sandbox=true"})
    for container in containers:
        user_id_raw = container.labels.get("agent.platform.user_id", "")
        if not user_id_raw.isdigit():
            continue
        activity = _activity_path(int(user_id_raw))
        last_active = activity.stat().st_mtime if activity.exists() else now
        idle_seconds = now - last_active
        container.reload()  # 刷新状态
        if idle_seconds >= DELETE_AFTER_SECONDS:
            container.remove(force=True)       # 7 天 → 删除
        elif idle_seconds >= IDLE_STOP_SECONDS and container.status == "running":
            container.stop(timeout=10)          # 30 分钟 → 停止


async def _cleanup_loop() -> None:
    """后台清理循环：每 CLEANUP_INTERVAL_SECONDS 秒执行一次 _cleanup_sync。

    用 asyncio.to_thread 把同步的 Docker 操作丢到线程里，
    不阻塞事件循环。
    """
    while True:
        try:
            await asyncio.to_thread(_cleanup_sync)
        except (DockerException, OSError):
            pass  # 清理失败不影响服务运行，下一轮重试
        await asyncio.sleep(max(10, CLEANUP_INTERVAL_SECONDS))


@asynccontextmanager
async def lifespan(_: FastAPI):
    """FastAPI 生命周期：启动时创建清理协程，关闭时取消。"""
    cleanup_task = asyncio.create_task(_cleanup_loop())
    try:
        yield
    finally:
        cleanup_task.cancel()
        await asyncio.gather(cleanup_task, return_exceptions=True)


app = FastAPI(title="Agent Platform Sandbox Service", lifespan=lifespan)


@app.get("/health")
async def health(_: None = Depends(require_internal_token)):
    """健康检查接口：验证 Docker Engine 是否可用。"""
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
    """执行代码的 HTTP 接口（Worker 调用）。

    流程：
    1. require_internal_token 认证
    2. 获取该用户的 asyncio.Lock（保证同一用户串行执行）
    3. asyncio.to_thread 把同步的 _execute_sync 丢到线程里（不阻塞事件循环）
    4. 返回执行结果 JSON

    为什么用用户级锁：
    同一用户只有一个容器，多个请求并发 exec_run 同一个容器会竞争资源，
    用锁保证同一用户的代码执行是串行的。
    """
    lock = _user_locks.setdefault(request.userId, asyncio.Lock())
    async with lock:
        try:
            return await asyncio.to_thread(_execute_sync, request)
        except (DockerException, NotFound, OSError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
