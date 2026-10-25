"""共享用户容器里的插件控制；不创建第二个容器，不导入上传代码。"""

from __future__ import annotations

import json
import os
from pathlib import Path

from docker.models.containers import Container
from pydantic import BaseModel, Field


class PluginContainerRequest(BaseModel):
    """内部请求；身份与版本决定路径，execution_id 区分任务，snapshot 为执行契约及配置。"""

    user_id: int = Field(gt=0)
    plugin_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,59}$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?$")
    execution_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,100}$")
    snapshot: dict | None = Field(default=None, repr=False)


class PluginContainerResult(BaseModel):
    """容器操作终态；status 为成功/失败/取消，stdout 为业务结果，container_id 验证复用。"""

    status: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    container_id: str = ""


def version_root(workspace_root: Path, request: PluginContainerRequest) -> Path:
    """根据 workspace_root 和 request 身份定位插件版本，解析后必须仍在用户目录内。"""
    return private_path(workspace_root, "plugins", request.plugin_id, request.version)


def private_path(workspace_root: Path, *parts: str) -> Path:
    """校验 workspace_root 下由平台提供的 parts；共享挂载里的链接不能跨用户或指向 Manager 文件。"""
    target = workspace_root
    for part in parts:
        target = target / part
        if target.is_symlink():
            raise ValueError("插件目录不允许符号链接")
    if workspace_root.resolve() not in target.resolve().parents:
        raise ValueError("插件路径超出用户目录")
    return target


def prepare_permissions(root: Path, gid: int) -> None:
    """让容器 gid 可访问 root 下的平台文件；拒绝链接，不递归用户生成的依赖目录。"""
    for path in [root, root / "package", *(root / "package").rglob("*")]:
        if path.is_symlink():
            raise ValueError("插件代码不允许符号链接")
        os.chown(path, -1, gid)
        path.chmod(0o770 if path.is_dir() else 0o660)


def execute_plugin(container: Container, workspace_root: Path, request: PluginContainerRequest, action: str, uid: int, gid: int) -> PluginContainerResult:
    """在 container 执行 action；workspace_root 对应用户挂载，uid/gid 为现有容器用户。"""
    root = version_root(workspace_root, request)
    if not (root / "package/manifest.json").is_file():
        raise ValueError("插件包文件不存在")
    if action == "install":
        # 宿主创建目录时可能使用严格 umask，补齐版本父目录的容器访问权限。
        for parent in (workspace_root, root.parent.parent, root.parent):
            os.chown(parent, -1, gid)
            parent.chmod(0o770)
        prepare_permissions(root, gid)
    relative_root = f"/workspaces/plugins/{request.plugin_id}/{request.version}"
    # 控制文件不包含密钥；它与业务输出按执行标识隔离。
    task_id = f"install-{request.plugin_id}-{request.version}" if action == "install" else request.execution_id
    task_root = private_path(workspace_root, "plugins", ".executions", task_id)
    task_root.mkdir(parents=True, exist_ok=True)
    os.chown(task_root.parent, -1, gid)
    task_root.parent.chmod(0o770)
    os.chown(task_root, -1, gid)
    task_root.chmod(0o770)
    for child in task_root.rglob("*"):
        if child.is_symlink():
            raise ValueError("执行目录包含符号链接")
        os.chown(child, -1, gid)
        child.chmod(0o770 if child.is_dir() else 0o660)
    config = {"root": relative_root, "workspace": f"/workspaces/plugins/.executions/{task_id}", "action": action}
    environment = {"PLUGIN_VALUES": "{}", "PLUGIN_SECRETS": "{}"}
    if action == "run":
        if not (root / ".ready").is_file() or request.snapshot is None:
            raise ValueError("插件依赖尚未安装或执行快照不存在")
        snapshot = request.snapshot
        manifest = snapshot["manifest"]
        if manifest["id"] != request.plugin_id or manifest["version"] != request.version:
            raise ValueError("插件版本与快照不一致")
        entrypoint = manifest["entrypoint"]
        target = (root / "package" / entrypoint).resolve()
        if (root / "package").resolve() not in target.parents or not target.is_file():
            raise ValueError("插件入口不存在或越界")
        config.update({"entrypoint": entrypoint, "tool_name": snapshot["tool_name"], "arguments": snapshot["arguments"], "execution_id": request.execution_id, "timeout_seconds": min(120, max(1, int(manifest["timeout_seconds"])))})
        environment = {"PLUGIN_VALUES": json.dumps(snapshot["values"], ensure_ascii=False), "PLUGIN_SECRETS": json.dumps(snapshot["secrets"], ensure_ascii=False),
                       "PLUGIN_INPUT_FILES": json.dumps(snapshot.get("input_files", {}), ensure_ascii=False),
                       "PLUGIN_OUTPUT_DIR": config["workspace"] + "/output"}
    control = task_root / "control.json"
    control.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    os.chown(control, -1, gid)
    control.chmod(0o660)
    try:
        result = container.exec_run(["timeout", "--signal=KILL", "310" if action == "install" else "130", "python", "-I", "/opt/sandbox/process_runner.py", config["workspace"] + "/control.json"], demux=True, user=f"{uid}:{gid}", environment=environment)
        stdout, _ = result.output or (b"", b"")
        if result.exit_code != 0:
            return PluginContainerResult(status="failed", exit_code=result.exit_code, error="插件监督进程失败", container_id=container.id)
        parsed = PluginContainerResult.model_validate_json(stdout or b"{}")
        parsed.container_id = container.id
        return parsed
    finally:
        # 即使监督器失败或返回无效 JSON，也清理可能包含业务数据/凭据回显的临时文件。
        for filename in ("stdout.log", "stderr.log", "input.json", "control.json"):
            (task_root / filename).unlink(missing_ok=True)


def cancel_plugin(workspace_root: Path, request: PluginContainerRequest) -> PluginContainerResult:
    """为 request 执行写取消标记；监督器检查后会终止进程组并等待清理。"""
    task_root = private_path(workspace_root, "plugins", ".executions", request.execution_id)
    task_root.mkdir(parents=True, exist_ok=True)
    (task_root / "cancel").touch()
    return PluginContainerResult(status="cancel_requested")
