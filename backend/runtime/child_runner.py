"""受限 Python 子进程入口。

该文件由 Runtime Service 使用独立 Python 进程启动，不应作为 HTTP 服务运行。
"""

import json
import mimetypes
import os
import sys
from pathlib import Path


def _is_relative_to(path: Path, root: Path) -> bool:
    """判断解析后的路径是否位于指定根目录。"""
    return path == root or root in path.parents


def _install_audit_hook(workspace: Path, output_dir: Path) -> None:
    """安装审计钩子，限制文件写入、网络和子进程操作。"""
    readable_roots = {
        workspace.resolve(),
        Path(sys.prefix).resolve(),
        Path(sys.base_prefix).resolve(),
    }
    output_root = output_dir.resolve()
    # openpyxl 会通过标准库 mimetypes 读取系统 MIME 配置。只放行标准库
    # 列出且实际存在的具体文件，不开放整个 /etc 目录。
    readable_files = {
        Path(item).resolve() for item in mimetypes.knownfiles if Path(item).is_file()
    }

    def audit(event: str, args: tuple) -> None:
        """处理 Python 审计事件并阻止超出策略的操作。"""
        if event == "open" and args:
            raw_path = args[0]
            if not isinstance(raw_path, (str, bytes, os.PathLike)):
                return
            path = Path(raw_path).resolve()
            mode_or_flags = args[1] if len(args) > 1 else "r"
            if isinstance(mode_or_flags, int):
                write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
                is_write = bool(mode_or_flags & write_flags)
            else:
                is_write = any(flag in str(mode_or_flags) for flag in ("w", "a", "+", "x"))
            if is_write and not _is_relative_to(path, output_root):
                raise PermissionError("Runtime 仅允许写入 output 目录")
            if (
                not is_write
                and path not in readable_files
                and not any(_is_relative_to(path, root) for root in readable_roots)
            ):
                raise PermissionError("Runtime 不允许读取工作目录之外的文件")

        # pathlib 底层也会发出 os.* 审计事件，因此需单独限制删除、
        # 重命名、建目录和链接操作，防止绕过 open 事件修改宿主机文件。
        mutation_path_indexes = {
            "os.remove": (0,), "os.rmdir": (0,), "os.mkdir": (0,),
            "os.rename": (0, 1), "os.link": (0, 1), "os.symlink": (0, 1),
            "os.truncate": (0,),
        }
        if event in mutation_path_indexes:
            for index in mutation_path_indexes[event]:
                if index >= len(args) or not isinstance(args[index], (str, bytes, os.PathLike)):
                    continue
                if not _is_relative_to(Path(args[index]).resolve(), output_root):
                    raise PermissionError("Runtime 仅允许修改 output 目录")

        if event == "ctypes.dlopen":
            library = args[0] if args else None
            # numpy 会用 dlopen(None) 获取当前 Python 进程句柄；扩展包
            # 也需加载 Python 安装目录内的自带动态库。
            if library is not None:
                library_path = Path(library).resolve()
                if not any(_is_relative_to(library_path, root) for root in readable_roots):
                    raise PermissionError("Runtime 禁止加载 Python 目录之外的动态库")

        blocked_prefixes = (
            "socket.", "subprocess.", "os.system", "os.exec", "os.spawn", "pty.",
        )
        if event.startswith(blocked_prefixes):
            raise PermissionError(f"Runtime 禁止操作：{event}")

    sys.addaudithook(audit)


def main() -> int:
    """加载执行配置、运行用户代码并写出结构化结果。"""
    if len(sys.argv) != 2:
        print("缺少 Runtime 配置文件", file=sys.stderr)
        return 2

    config_path = Path(sys.argv[1]).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    workspace = Path(config["workspace"]).resolve()
    source_path = Path(config["sourcePath"]).resolve()
    input_dir = Path(config["inputDir"]).resolve()
    output_dir = Path(config["outputDir"]).resolve()
    input_files = config.get("inputFiles") or {}
    arguments = config.get("arguments") or {}

    _install_audit_hook(workspace, output_dir)
    os.chdir(workspace)

    namespace = {
        "__name__": "__main__",
        "INPUT_DIR": str(input_dir),
        "OUTPUT_DIR": str(output_dir),
        "INPUT_FILES": input_files,
        "RUNTIME_ARGS": arguments,
    }
    code = source_path.read_text(encoding="utf-8")
    exec(compile(code, str(source_path), "exec"), namespace, namespace)

    result_path = output_dir / "result.json"
    if not result_path.exists() and "result" in namespace:
        result_path.write_text(
            json.dumps(namespace["result"], ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
