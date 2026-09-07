import unittest

from backend.core.workflow_conditions import evaluate_workflow_conditions


class WorkflowConditionTests(unittest.TestCase):
    """验证工作流文本条件和结构化字段条件的分支选择行为。"""

    @staticmethod
    def _structured_condition(
        field: str,
        value: str = "",
        operator: str = "eq",
    ) -> list[dict[str, str]]:
        """创建带默认分支的结构化条件配置。

        参数：
        - ``field``：需要读取的 JSON 字段路径；
        - ``value``：前端填写的期望值文本；
        - ``operator``：字段比较操作符。
        """
        return [
            {
                "label": "结构化分支",
                "type": "structured",
                "field": field,
                "operator": operator,
                "value": value,
            },
            {"label": "默认分支", "type": "else"},
        ]

    def test_matches_top_level_number_field(self) -> None:
        """顶层数字字段 type=1 应命中结构化分支。"""
        result = evaluate_workflow_conditions(
            self._structured_condition("type", "1"),
            '{"type": 1}',
        )
        self.assertEqual(result.branch_index, 0)
        self.assertEqual(result.actual_value, 1)

    def test_reads_nested_object_and_array_path(self) -> None:
        """点号路径应支持嵌套对象和数组下标。"""
        result = evaluate_workflow_conditions(
            self._structured_condition("items.0.name", "Excel"),
            '{"items": [{"name": "Excel"}]}',
        )
        self.assertEqual(result.branch_index, 0)
        self.assertEqual(result.actual_value, "Excel")

    def test_compares_json_types_strictly(self) -> None:
        """布尔值、数字和字符串不得因 Python 隐式规则被判为相等。"""
        number_result = evaluate_workflow_conditions(
            self._structured_condition("type", "1"),
            '{"type": true}',
        )
        string_result = evaluate_workflow_conditions(
            self._structured_condition("type", '"1"'),
            '{"type": "1"}',
        )
        self.assertEqual(number_result.branch_index, 1)
        self.assertEqual(string_result.branch_index, 0)

    def test_supports_order_comparison_and_contains(self) -> None:
        """大小比较和集合包含操作符应按 JSON 实际类型判断。"""
        greater_result = evaluate_workflow_conditions(
            self._structured_condition("score", "80", "gte"),
            '{"score": 90}',
        )
        contains_result = evaluate_workflow_conditions(
            self._structured_condition("tags", "excel", "contains"),
            '{"tags": ["excel", "report"]}',
        )
        self.assertEqual(greater_result.branch_index, 0)
        self.assertEqual(contains_result.branch_index, 0)

    def test_supports_field_existence_operators(self) -> None:
        """字段存在和不存在判断应区分缺失字段与 null 字段。"""
        exists_result = evaluate_workflow_conditions(
            self._structured_condition("result", operator="exists"),
            '{"result": null}',
        )
        missing_result = evaluate_workflow_conditions(
            self._structured_condition("error", operator="not_exists"),
            '{"result": null}',
        )
        self.assertEqual(exists_result.branch_index, 0)
        self.assertEqual(missing_result.branch_index, 0)

    def test_parses_fenced_json_and_falls_back_on_invalid_json(self) -> None:
        """Markdown JSON 代码块可解析，非法 JSON 应进入默认分支。"""
        conditions = self._structured_condition("type", "1")
        fenced_result = evaluate_workflow_conditions(
            conditions,
            '```json\n{"type": 1}\n```',
        )
        invalid_result = evaluate_workflow_conditions(conditions, "not-json")
        self.assertEqual(fenced_result.branch_index, 0)
        self.assertEqual(invalid_result.branch_index, 1)

    def test_keeps_contains_and_regex_compatibility(self) -> None:
        """旧版关键词与正则条件仍应保持原有匹配方式。"""
        conditions = [
            {"label": "关键词", "type": "contains", "value": "成功"},
            {"label": "编号", "type": "regex", "value": r"ID-\d+"},
            {"label": "默认", "type": "else"},
        ]
        contains_result = evaluate_workflow_conditions(conditions, "执行成功")
        regex_result = evaluate_workflow_conditions(conditions, "结果 ID-1024")
        self.assertEqual(contains_result.branch_index, 0)
        self.assertEqual(regex_result.branch_index, 1)


if __name__ == "__main__":
    unittest.main()
