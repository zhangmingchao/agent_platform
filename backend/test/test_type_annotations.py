"""项目 Python 方法返回值类型规范测试。"""

import ast
import unittest
from pathlib import Path


class ReturnTypeAnnotationTests(unittest.TestCase):
    """确保项目自有 Python 方法都声明明确的返回值类型。"""

    def test_all_project_functions_declare_return_types(self) -> None:
        """扫描正式源码、Demo、脚本和测试，报告缺少返回类型的方法。"""
        backend_root = Path(__file__).resolve().parents[1]
        excluded_directories = {
            ".venv",
            ".venv-langchan",
            "__pycache__",
            # Runtime 目录包含大模型生成的用户代码，不属于平台源码。
            "data",
        }
        missing_annotations: list[str] = []

        for source_path in sorted(backend_root.rglob("*.py")):
            if any(part in excluded_directories for part in source_path.parts):
                continue
            syntax_tree = ast.parse(
                source_path.read_text(encoding="utf-8"),
                filename=str(source_path),
            )
            for node in ast.walk(syntax_tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.returns is None:
                        relative_path = source_path.relative_to(backend_root.parent)
                        missing_annotations.append(
                            f"{relative_path}:{node.lineno} {node.name}"
                        )

        self.assertEqual(
            missing_annotations,
            [],
            "以下方法缺少返回值类型标注：\n" + "\n".join(missing_annotations),
        )


if __name__ == "__main__":
    unittest.main()
