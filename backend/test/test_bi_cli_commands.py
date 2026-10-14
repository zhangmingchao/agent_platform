"""BI CLI 只读命令解析测试。"""

import unittest

from backend.bi_cli.commands import parse_bi_cli_command
from backend.bi_cli.errors import BiCliError
from backend.bi_cli.models import BiHttpMethod


class BiCliCommandTests(unittest.TestCase):
    """验证 CLI 参数只会映射到第一期允许的五个只读接口。"""

    def test_parses_analysis_body_list(self) -> None:
        request = parse_bi_cli_command(
            ["metadata", "analysis-bodies", "list", "--product-key", "app-1"]
        )

        self.assertEqual(request.command_name, "metadata.analysis-bodies.list")
        self.assertEqual(request.method, BiHttpMethod.GET)
        self.assertEqual(request.path, "/analysisBody/bodyList")
        self.assertEqual(dict(request.query_items), {"productKey": "app-1"})

    def test_parses_event_list_filters_and_pagination(self) -> None:
        request = parse_bi_cli_command(
            [
                "metadata", "events", "list",
                "--product-key", "app-1",
                "--page-num", "2",
                "--page-size", "20",
                "--search-text", "登录",
                "--event-classify", "1",
                "--event-classify", "3",
            ]
        )

        self.assertEqual(request.path, "/eventConfig/findByProductKey")
        self.assertEqual(
            [item for item in request.query_items if item[0] == "eventClassifyArr"],
            [("eventClassifyArr", 1), ("eventClassifyArr", 3)],
        )
        self.assertIn(("pageNum", 2), request.query_items)
        self.assertIn(("searchText", "登录"), request.query_items)

    def test_parses_user_property_list(self) -> None:
        request = parse_bi_cli_command(
            [
                "metadata", "user-properties", "list",
                "--product-key", "app-1",
                "--entity-type", "users",
                "--profile-classify-list", "1,2",
            ]
        )

        self.assertEqual(request.path, "/profileUser/findAllUserProfList")
        self.assertIn(("entityType", "users"), request.query_items)
        self.assertIn(("profileClassifyList", "1,2"), request.query_items)

    def test_parses_event_property_list_body(self) -> None:
        request = parse_bi_cli_command(
            [
                "metadata", "event-properties", "list",
                "--product-key", "app-1",
                "--profile-classify", "1",
                "--profile-type", "2",
            ]
        )

        self.assertEqual(request.method, BiHttpMethod.POST)
        self.assertEqual(request.path, "/profileType/findByProductKey")
        self.assertEqual(
            request.json_body,
            {"productKey": "app-1", "profileClassifyList": [1], "profileTypeList": [2]},
        )

    def test_parses_metric_list_defaults(self) -> None:
        request = parse_bi_cli_command(
            ["metadata", "metrics", "list", "--product-key", "app-1"]
        )

        self.assertEqual(request.path, "/eventMetric/metricList")
        self.assertIn(("pageNum", 1), request.query_items)
        self.assertIn(("pageSize", 50), request.query_items)

    def test_rejects_page_size_over_limit(self) -> None:
        with self.assertRaises(BiCliError) as raised:
            parse_bi_cli_command(
                [
                    "metadata", "events", "list",
                    "--product-key", "app-1",
                    "--page-size", "201",
                ]
            )

        self.assertEqual(raised.exception.failure.error_code, "INVALID_ARGUMENTS")


if __name__ == "__main__":
    unittest.main()
