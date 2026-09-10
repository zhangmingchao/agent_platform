"""本地 Python Runtime 静态策略测试。"""

import unittest

from backend.runtime.policy import RuntimePolicyError, validate_python_code


class RuntimePolicyTests(unittest.TestCase):
    """验证常用数据处理代码可用，明显危险代码被拒绝。"""

    def test_allows_data_processing_imports(self) -> None:
        """允许 JSON、数学和安全路径处理模块。"""
        validate_python_code("import json\nimport math\nfrom pathlib import Path\nresult = math.sqrt(4)")

    def test_denies_dangerous_imports_and_calls(self) -> None:
        """拒绝操作系统、网络、子进程及动态执行入口。"""
        samples = ("import os", "import subprocess", "import socket", "eval('1 + 1')")
        for code in samples:
            with self.subTest(code=code), self.assertRaises(RuntimePolicyError):
                validate_python_code(code)


if __name__ == "__main__":
    unittest.main()
