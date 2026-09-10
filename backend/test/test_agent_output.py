import unittest

from backend.core.agent_output import (
    append_schema_instruction,
    parse_and_validate_structured_output,
    render_prompt_template,
    validate_output_schema,
)
from backend.core.schema_dsl import json_schema_to_python_schema, python_schema_to_json_schema


class AgentOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = {
            "type": "object",
            "required": ["risk_level", "approved"],
            "properties": {
                "risk_level": {"type": "string", "enum": ["low", "high"]},
                "approved": {"type": "boolean"},
            },
            "additionalProperties": False,
        }

    def test_runtime_variables_override_defaults(self) -> None:
        rendered = render_prompt_template(
            "使用{{language}}回答 {{username}}：{{user_input}}；保留{{missing}}",
            {"language": "中文", "username": "错误名称"},
            {"username": "张三", "user_input": "你好"},
        )
        self.assertEqual(rendered, "使用中文回答 张三：你好；保留{{missing}}")

    def test_schema_instruction_is_appended(self) -> None:
        prompt = append_schema_instruction("你是审核员", self.schema)
        self.assertIn("合法 JSON", prompt)
        self.assertIn('"risk_level"', prompt)

    def test_parses_and_validates_json_and_fenced_json(self) -> None:
        expected = {"risk_level": "high", "approved": False}
        self.assertEqual(
            parse_and_validate_structured_output('{"risk_level":"high","approved":false}', self.schema),
            expected,
        )
        self.assertEqual(
            parse_and_validate_structured_output('```json\n{"risk_level":"high","approved":false}\n```', self.schema),
            expected,
        )

    def test_rejects_output_that_does_not_match_schema(self) -> None:
        with self.assertRaisesRegex(ValueError, "不符合 Schema"):
            parse_and_validate_structured_output('{"risk_level":"medium","approved":false}', self.schema)

    def test_rejects_invalid_schema(self) -> None:
        with self.assertRaisesRegex(ValueError, "output_schema 无效"):
            validate_output_schema({"type": "unknown"})

    def test_converts_python_schema_description_without_execution(self) -> None:
        source = '''
class PersonInfo(BaseModel):
    name: str = Field(description="人物的姓名")
    age: int = Field(ge=0, le=150, description="人物的年龄")
    hobby: Optional[str] = Field(default=None, description="人物的爱好")
    tags: list[str] = Field(default_factory=list)
'''
        schema = python_schema_to_json_schema(source)
        self.assertEqual(schema["title"], "PersonInfo")
        self.assertEqual(schema["required"], ["name", "age"])
        self.assertEqual(schema["properties"]["age"]["minimum"], 0)
        self.assertEqual(schema["properties"]["hobby"]["default"], None)
        self.assertEqual(schema["properties"]["tags"]["type"], "array")

    def test_python_schema_rejects_executable_statements(self) -> None:
        with self.assertRaisesRegex(ValueError, "顶层只允许"):
            python_schema_to_json_schema('open("/tmp/unsafe", "w")\nclass Result(BaseModel):\n    answer: str')
        with self.assertRaisesRegex(ValueError, "只允许带类型标注"):
            python_schema_to_json_schema('class Result(BaseModel):\n    def run(self):\n        return 1')

    def test_supports_safe_imports_and_required_ellipsis(self) -> None:
        schema = python_schema_to_json_schema('''
from pydantic import BaseModel, Field
from typing import Optional

class Result(BaseModel):
    answer: str = Field(..., description="回答")
    note: Optional[str] = None
''')
        self.assertEqual(schema["required"], ["answer"])
        self.assertEqual(schema["properties"]["answer"]["description"], "回答")

    def test_rejects_root_model_recursive_reference(self) -> None:
        with self.assertRaisesRegex(ValueError, "递归引用"):
            python_schema_to_json_schema('class Node(BaseModel):\n    children: list[Node]')

    def test_json_schema_can_be_rendered_and_parsed_again(self) -> None:
        source = json_schema_to_python_schema(self.schema)
        reparsed = python_schema_to_json_schema(source)
        self.assertEqual(reparsed["properties"]["risk_level"]["enum"], ["low", "high"])
        self.assertEqual(reparsed["required"], ["risk_level", "approved"])


if __name__ == "__main__":
    unittest.main()
