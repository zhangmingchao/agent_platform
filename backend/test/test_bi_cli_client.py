"""BI API 客户端认证、返回协议和错误映射测试。"""

import json
import unittest

import httpx

from backend.bi_cli.client import BiApiClient
from backend.bi_cli.commands import parse_bi_cli_command
from backend.bi_cli.models import BiCliExitCode, BiCliSettings


class BiApiClientTests(unittest.IsolatedAsyncioTestCase):
    """使用 HTTPX MockTransport 验证请求不会泄漏或绕过 BI 权限参数。"""

    async def test_sends_token_product_key_and_request_id(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.headers["token"], "readonly-token")
            self.assertEqual(request.headers["pk"], "app-1")
            self.assertEqual(request.headers["x-request-id"], "req-100")
            self.assertEqual(request.url.path, "/portal-api/bi-docker/analysisBody/bodyList")
            return httpx.Response(
                200,
                json={"code": 200, "msg": "操作成功", "data": [{"id": 1}], "timeZone": "Asia/Shanghai"},
            )

        settings = BiCliSettings(
            base_url="http://bi.test/portal-api/bi-docker",
            access_token="readonly-token",
            request_id="req-100",
        )
        request = parse_bi_cli_command(
            ["metadata", "analysis-bodies", "list", "--product-key", "app-1"]
        )

        result = await BiApiClient(settings, httpx.MockTransport(handler)).execute(request)

        self.assertTrue(result.ok)
        self.assertEqual(result.data, [{"id": 1}])
        self.assertEqual(result.time_zone, "Asia/Shanghai")

    async def test_maps_business_permission_error(self) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            del request
            return httpx.Response(200, json={"code": 420, "msg": "没有接口访问权限", "data": None})

        settings = BiCliSettings(
            base_url="http://bi.test",
            access_token="readonly-token",
        )
        request = parse_bi_cli_command(
            ["metadata", "metrics", "list", "--product-key", "app-1"]
        )

        result = await BiApiClient(settings, httpx.MockTransport(handler)).execute(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.exit_code, BiCliExitCode.PERMISSION_DENIED)
        self.assertEqual(result.error_code, "PERMISSION_DENIED")

    async def test_rejects_response_over_output_limit(self) -> None:
        payload = {"code": 200, "data": ["x" * 200]}

        async def handler(request: httpx.Request) -> httpx.Response:
            del request
            return httpx.Response(200, content=json.dumps(payload).encode("utf-8"))

        settings = BiCliSettings(
            base_url="http://bi.test",
            access_token="readonly-token",
            max_output_bytes=64,
        )
        request = parse_bi_cli_command(
            ["metadata", "events", "list", "--product-key", "app-1"]
        )

        result = await BiApiClient(settings, httpx.MockTransport(handler)).execute(request)

        self.assertFalse(result.ok)
        self.assertEqual(result.exit_code, BiCliExitCode.OUTPUT_TOO_LARGE)
        self.assertEqual(result.error_code, "OUTPUT_TOO_LARGE")


if __name__ == "__main__":
    unittest.main()
