"""受控 BiCli LangChain 工具测试。"""

import json
import unittest
from unittest.mock import AsyncMock, patch

from backend.core.agent_factory import build_all_tools
from backend.core.bi_cli_tool import BiCliProcessResult, build_bi_cli_tools
from backend.runtime.models import RuntimeContext


class BiCliToolTests(unittest.IsolatedAsyncioTestCase):
    """验证工具注册、参数隔离和结构化输出。"""

    def test_returns_empty_when_disabled(self) -> None:
        with patch("backend.core.bi_cli_tool.BI_CLI_ENABLED", False):
            tools = build_bi_cli_tools(RuntimeContext(user_id=7))

        self.assertEqual(tools, [])

    async def test_registers_bi_cli_in_agent_tool_collection(self) -> None:
        """启用 BI CLI 后，应进入 Agent 的统一工具权限与审计流水线。"""
        with patch("backend.core.bi_cli_tool.BI_CLI_ENABLED", True):
            tools = await build_all_tools([], [], RuntimeContext(user_id=7))

        self.assertIn("BiCli", [tool.name for tool in tools])

    async def test_executes_fixed_cli_with_argument_array(self) -> None:
        process_result = BiCliProcessResult(
            exit_code=0,
            stdout=json.dumps(
                {"ok": True, "command": "metadata.events.list", "data": [{"id": 1}]},
                ensure_ascii=False,
            ),
        )
        with (
            patch("backend.core.bi_cli_tool.BI_CLI_ENABLED", True),
            patch(
                "backend.core.bi_cli_tool._execute_bi_cli_process",
                new=AsyncMock(return_value=process_result),
            ) as execute,
        ):
            tool = build_bi_cli_tools(RuntimeContext(user_id=7))[0]
            output = await tool.ainvoke(
                {
                    "arguments": [
                        "metadata", "events", "list", "--product-key", "app-1",
                    ]
                }
            )

        parsed = json.loads(output)
        self.assertTrue(parsed["ok"])
        execute.assert_awaited_once_with(
            ["metadata", "events", "list", "--product-key", "app-1"],
            "",
        )

    async def test_rejects_shell_control_characters_before_process(self) -> None:
        with (
            patch("backend.core.bi_cli_tool.BI_CLI_ENABLED", True),
            patch(
                "backend.core.bi_cli_tool._execute_bi_cli_process",
                new=AsyncMock(),
            ) as execute,
        ):
            tool = build_bi_cli_tools(RuntimeContext(user_id=7))[0]
            output = await tool.ainvoke(
                {"arguments": ["metadata", "events", "list", "; rm -rf /"]}
            )

        parsed = json.loads(output)
        self.assertFalse(parsed["ok"])
        self.assertEqual(parsed["error"]["code"], "INVALID_ARGUMENTS")
        execute.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
