import unittest

from backend.core.agent_output import (
    append_schema_instruction,
    parse_and_validate_structured_output,
    render_prompt_template,
    validate_output_schema,
)


class AgentOutputTests(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "type": "object",
            "required": ["risk_level", "approved"],
            "properties": {
                "risk_level": {"type": "string", "enum": ["low", "high"]},
                "approved": {"type": "boolean"},
            },
            "additionalProperties": False,
        }

    def test_runtime_variables_override_defaults(self):
        rendered = render_prompt_template(
            "使用{{language}}回答 {{username}}：{{user_input}}；保留{{missing}}",
            {"language": "中文", "username": "错误名称"},
            {"username": "张三", "user_input": "你好"},
        )
        self.assertEqual(rendered, "使用中文回答 张三：你好；保留{{missing}}")

    def test_schema_instruction_is_appended(self):
        prompt = append_schema_instruction("你是审核员", self.schema)
        self.assertIn("合法 JSON", prompt)
        self.assertIn('"risk_level"', prompt)

    def test_parses_and_validates_json_and_fenced_json(self):
        expected = {"risk_level": "high", "approved": False}
        self.assertEqual(
            parse_and_validate_structured_output('{"risk_level":"high","approved":false}', self.schema),
            expected,
        )
        self.assertEqual(
            parse_and_validate_structured_output('```json\n{"risk_level":"high","approved":false}\n```', self.schema),
            expected,
        )

    def test_rejects_output_that_does_not_match_schema(self):
        with self.assertRaisesRegex(ValueError, "不符合 Schema"):
            parse_and_validate_structured_output('{"risk_level":"medium","approved":false}', self.schema)

    def test_rejects_invalid_schema(self):
        with self.assertRaisesRegex(ValueError, "output_schema 无效"):
            validate_output_schema({"type": "unknown"})


if __name__ == "__main__":
    unittest.main()
