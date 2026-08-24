"""模型生成代码的静态安全策略。

本模块只能降低误操作风险，不构成强安全边界；真正不可信的代码仍应使用容器、
gVisor 或虚拟机隔离。当前策略用于本地开发模式下的受限子进程执行。
"""

import ast
from typing import Iterable


ALLOWED_IMPORT_ROOTS = {
    "collections", "csv", "datetime", "decimal", "docx", "fractions",
    "functools", "itertools", "json", "math", "matplotlib", "numpy",
    "openpyxl", "pandas", "pathlib", "pypdf", "random", "re", "statistics",
}

DENIED_CALL_NAMES = {
    "__import__", "breakpoint", "compile", "eval", "exec", "globals",
    "help", "input", "locals", "memoryview",
}

DENIED_ATTRIBUTE_NAMES = {
    "__bases__", "__class__", "__code__", "__func__", "__globals__",
    "__mro__", "__subclasses__",
}


class RuntimePolicyError(ValueError):
    """表示代码不符合本地 Runtime 的安全策略。"""


def _import_roots(names: Iterable[ast.alias]) -> set[str]:
    """提取 import 语句中的顶级包名。"""
    return {item.name.split(".", 1)[0] for item in names}


def validate_python_code(code: str) -> None:
    """解析并校验模型生成的 Python 代码，拒绝明显危险的语法。"""
    if not isinstance(code, str) or not code.strip():
        raise RuntimePolicyError("Python 代码不能为空")
    if len(code.encode("utf-8")) > 200_000:
        raise RuntimePolicyError("Python 代码超过 200KB 限制")

    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise RuntimePolicyError(f"Python 语法错误：{exc.msg}（第 {exc.lineno} 行）") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            denied = _import_roots(node.names) - ALLOWED_IMPORT_ROOTS
            if denied:
                raise RuntimePolicyError(f"不允许导入模块：{', '.join(sorted(denied))}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if not root or root not in ALLOWED_IMPORT_ROOTS:
                raise RuntimePolicyError(f"不允许导入模块：{node.module or '相对导入'}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in DENIED_CALL_NAMES:
                raise RuntimePolicyError(f"不允许调用：{node.func.id}")
        elif isinstance(node, ast.Attribute) and node.attr in DENIED_ATTRIBUTE_NAMES:
            raise RuntimePolicyError(f"不允许访问属性：{node.attr}")
