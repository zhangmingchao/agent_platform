"""容器内插件进程监督器；安装/运行使用独立进程组，超时、取消和输出超限均清理子进程。"""

from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ManagedResult:
    """受管理进程结果；状态、退出码、有限 stdout/stderr 和错误供 Sandbox HTTP 返回。"""

    status: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str = ""


def run_process(command: list[str], workspace: Path, timeout: int, stdin: bytes | None = None, cancel_file: Path | None = None) -> ManagedResult:
    """在 workspace 执行 command；timeout 限制秒数，stdin 是业务 JSON，cancel_file 是平台取消标记。"""
    stdout_path, stderr_path = workspace / "stdout.log", workspace / "stderr.log"
    limit = 1024 * 1024
    deadline = time.monotonic() + timeout
    status = "completed"
    input_path = workspace / "input.json"
    input_path.write_bytes(stdin or b"")
    # 文件输入不会因为插件不读 stdin 而让监督器堵在管道写入阶段。
    with input_path.open("rb") as inp, stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        process = subprocess.Popen(command, stdin=inp, stdout=out, stderr=err, start_new_session=True)
        try:
            while process.poll() is None:
                if cancel_file is not None and cancel_file.exists():
                    status = "cancelled"
                    break
                if time.monotonic() >= deadline:
                    status = "timed_out"
                    break
                if stdout_path.stat().st_size > limit or stderr_path.stat().st_size > limit:
                    status = "output_limit"
                    break
                time.sleep(0.05)
        finally:
            # 即使主进程成功退出，也清理留在同一进程组里的后台子进程。
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    if status == "completed" and (stdout_path.stat().st_size > limit or stderr_path.stat().st_size > limit):
        status = "output_limit"
    if status == "completed" and process.returncode != 0:
        status = "failed"
    errors = {"cancelled": "插件执行已取消", "timed_out": "插件执行超时", "output_limit": "插件输出超过 1MB", "failed": "插件进程退出异常"}
    with stdout_path.open("rb") as source:
        output = source.read(limit).decode("utf-8", errors="replace")
    with stderr_path.open("rb") as source:
        diagnostic = source.read(limit).decode("utf-8", errors="replace")
    return ManagedResult(status, process.returncode, output, diagnostic, errors.get(status, ""))


def main() -> int:
    """读取非敏感控制文件；凭据仅来自本次 Docker Exec 环境，结果以 JSON 输出。"""
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    root = Path(config["root"])
    workspace = Path(config["workspace"])
    workspace.mkdir(parents=True, exist_ok=True)
    if config["action"] == "install":
        venv = root / ".venv"
        # 安装失败重试从干净依赖目录开始，不继承半安装状态。
        (root / ".ready").unlink(missing_ok=True)
        if venv.is_symlink():
            venv.unlink()
        elif venv.exists():
            shutil.rmtree(venv)
        # copies 避免虚拟环境链接依赖运行器外部路径；--no-deps 要求 lock 列出全部依赖。
        result = run_process([sys.executable, "-m", "venv", "--copies", str(venv)], workspace, 30)
        if result.status == "completed":
            result = run_process([str(venv / "bin/python"), "-m", "pip", "install", "--disable-pip-version-check", "--no-cache-dir", "--only-binary=:all:", "--no-deps", "-r", str(root / "package/requirements.lock")], workspace, 260)
        if result.status == "completed":
            result = run_process([str(venv / "bin/python"), "-m", "pip", "check"], workspace, 10)
        if result.status == "completed":
            (root / ".ready").write_text("1", encoding="utf-8")
        # 安装日志不作为业务 stdout 返回。
        result.stdout = ""
    else:
        command = [str(root / ".venv/bin/python"), "-I", str(root / "package" / config["entrypoint"])]
        payload = json.dumps({"protocol_version": 1, "execution_id": config["execution_id"], "tool_name": config["tool_name"], "arguments": config["arguments"]}, ensure_ascii=False).encode()
        os.chdir(root / "package")
        result = run_process(command, workspace, config["timeout_seconds"], payload, workspace / "cancel")
    # stderr 可能包含 Token；容器服务不持久化或回传它。错误细节由插件结构化返回。
    result.stderr = ""
    print(json.dumps(asdict(result), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
