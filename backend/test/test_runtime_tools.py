"""Python Runtime 工具注册测试。"""

import unittest
from unittest.mock import patch

from backend.runtime.models import RuntimeContext
from backend.runtime.tools import build_runtime_tools


class RuntimeToolsTests(unittest.TestCase):
    """验证 Agent 只注册仍受支持的 Runtime 工具。"""

    def test_builds_only_execute_python_tool(self) -> None:
        """启用 Runtime 且存在上下文时，只注册 ExecutePython。"""
        context = RuntimeContext(user_id=7, session_id=88)

        with patch("backend.runtime.tools.PYTHON_RUNTIME_ENABLED", True):
            tools = build_runtime_tools(context)

        self.assertEqual([tool.name for tool in tools], ["ExecutePython"])
        self.assertNotIn("RunSkillScript", [tool.name for tool in tools])

    def test_returns_empty_list_when_runtime_is_disabled(self) -> None:
        """关闭 Runtime 时不向 Agent 注册代码执行工具。"""
        context = RuntimeContext(user_id=7, session_id=88)

        with patch("backend.runtime.tools.PYTHON_RUNTIME_ENABLED", False):
            tools = build_runtime_tools(context)

        self.assertEqual(tools, [])

    def test_returns_empty_list_without_runtime_context(self) -> None:
        """缺少用户隔离上下文时不注册代码执行工具。"""
        with patch("backend.runtime.tools.PYTHON_RUNTIME_ENABLED", True):
            tools = build_runtime_tools(None)

        self.assertEqual(tools, [])


if __name__ == "__main__":
    unittest.main()
