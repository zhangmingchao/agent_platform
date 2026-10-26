"""BI/Rule 插件的业务行为验证；不对生产环境执行写入。"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator

from backend.plugins.bi_metadata.executor.solar_api.client import ApiCall, ApiCatalog, ApiSettings, SolarApiClient
from backend.plugins.examples import export_builtin
from backend.plugins.packages import check_package
from scripts.build_solar_catalog import SourceIndex, go_endpoints, java_endpoints


class SolarPluginTests(unittest.IsolatedAsyncioTestCase):
    """验证固定目录、参数分流、平台凭据、修改语义和真实进程打包契约。"""
    def setUp(self) -> None:
        """创建受信任目录和仅用于测试的配置，不读取数据库或真实 Token。"""
        self.catalog = ApiCatalog()
        self.settings = ApiSettings('https://bi.test/portal-api/bi-docker/api', 'fixture-token', 'https://portal.test/portal-api')
        self.requests: list[httpx.Request] = []

    def endpoint_id(self, path: str) -> str:
        """按测试 path 获取目录 ID，断言测试覆盖的是已登记接口。"""
        return next(e.id for e in self.catalog.entries.values() if e.path == path)

    def success(self, request: httpx.Request) -> httpx.Response:
        """模拟 request 的业务成功响应，保存请求用于确认实际 HTTP 契约。"""
        self.requests.append(request)
        return httpx.Response(200, json={'code': 200, 'data': {'total': 23, 'list': []}})

    async def test_bi_query_fills_product_and_preserves_array_query(self) -> None:
        """产品头与查询参数一致；数组按重复键传参，BI 地址不重复拼接服务前缀。"""
        client = SolarApiClient(self.catalog, self.settings, httpx.MockTransport(self.success))
        result = await client.execute(ApiCall(self.endpoint_id('/eventConfig/findByProductKey'), 'fixture-product', {'pageNum': 2, 'pageSize': 50, 'eventClassifyArr': [1, 3]}))
        self.assertTrue(result.ok)
        request = self.requests[0]
        self.assertEqual(request.url.path, '/portal-api/bi-docker/api/eventConfig/findByProductKey')
        self.assertEqual(request.headers['pk'], 'fixture-product')
        self.assertEqual(request.headers['token'], 'fixture-token')
        self.assertEqual(request.url.params['productKey'], 'fixture-product')
        self.assertEqual(request.url.params.get_list('eventClassifyArr'), ['1', '3'])

    async def test_rule_uses_portal_gateway_and_separate_token(self) -> None:
        """Rule 走已核对的 Portal 代理路径；身份头不由 Agent 伪造，可配置独立 Token。"""
        settings = ApiSettings('https://bi.test/api', 'bi-only', 'https://portal.test/portal-api', 'rule-only')
        client = SolarApiClient(self.catalog, settings, httpx.MockTransport(self.success))
        result = await client.execute(ApiCall(self.endpoint_id('/portal/experiment/list'), 'fixture-product', {'appId': 17}))
        self.assertTrue(result.ok)
        request = self.requests[0]
        self.assertEqual(request.url.path, '/portal-api/portal/ab/experiment/list')
        self.assertEqual(request.headers['token'], 'rule-only')
        self.assertNotIn('tenantId', request.headers)
        self.assertNotIn('seLoginUserId', request.headers)

    async def test_get_mutation_cannot_bypass_query_and_configuration(self) -> None:
        """GET 上线仍为修改；查询工具或未允许修改的配置不得发出网络请求。"""
        client = SolarApiClient(self.catalog, self.settings, httpx.MockTransport(self.success))
        call = ApiCall(self.endpoint_id('/portal/experiment/setOnline'), 'fixture-product', {'id': 7}, change_reason='用户要求上线指定实验')
        self.assertEqual((await client.execute(call)).error.code, 'OPERATION_NOT_ALLOWED')
        self.assertEqual((await client.execute(call, True)).error.code, 'MUTATION_DISABLED')
        self.assertEqual(self.requests, [])
        enabled = ApiSettings('https://bi.test/api', 'fixture-token', 'https://portal.test/portal-api', allow_mutations=True)
        self.assertTrue((await SolarApiClient(self.catalog, enabled, httpx.MockTransport(self.success)).execute(call, True)).ok)
        self.assertEqual(self.requests[0].method, 'GET')

    async def test_validation_blocks_wrong_product_unknown_headers_and_internal_routes(self) -> None:
        """跨产品、任意身份头、超大分页、缺少 appId 与内部回调在网络前拒绝。"""
        client = SolarApiClient(self.catalog, self.settings, httpx.MockTransport(self.success))
        event_id = self.endpoint_id('/eventConfig/findByProductKey')
        calls = [ApiCall(event_id, 'a', {'productKey': 'b'}), ApiCall(event_id, 'a', context={'tenantId': 'spoof'}), ApiCall(event_id, 'a', {'pageSize': 201}), ApiCall(self.endpoint_id('/portal/experiment/list'), 'a'), ApiCall(self.endpoint_id('/config/get'), 'a')]
        for call in calls:
            with self.subTest(call=call.endpoint_id):
                self.assertFalse((await client.execute(call)).ok)
        self.assertEqual(self.requests, [])

    async def test_analysis_query_keeps_json_and_query_parameters_separate(self) -> None:
        """POST 分析是查询；showSql 位于 URL，BehaviorViewModel 作为 JSON 请求体。"""
        client = SolarApiClient(self.catalog, self.settings, httpx.MockTransport(self.success))
        call = ApiCall(self.endpoint_id('/report/eventAnalysis'), 'fixture-product', {'showSql': False}, {'behaviorContents': [{'eventName': 'fixture-event'}], 'startDate': '2026-10-01', 'endDate': '2026-10-02'})
        self.assertTrue((await client.execute(call)).ok)
        request = self.requests[0]
        self.assertEqual(request.method, 'POST')
        self.assertEqual(request.url.params['showSql'], 'false')
        self.assertEqual(json.loads(request.content)['productKey'], 'fixture-product')
        self.assertNotIn('showSql', json.loads(request.content))

    async def test_http_404_auth_errors_redirects_and_bounded_response(self) -> None:
        """区分根路径 404、认证和跳转；过大响应不进入模型上下文。"""
        call = ApiCall(self.endpoint_id('/eventConfig/findByProductKey'), 'fixture')
        cases = [(httpx.Response(404, text='<html/>'), 'NOT_FOUND'), (httpx.Response(200, json={'code': 20002}), 'UNAUTHENTICATED'), (httpx.Response(302, headers={'location': 'https://other.test'}), 'REDIRECT'), (httpx.Response(200, text='x' * 200), 'OUTPUT_TOO_LARGE')]
        small = ApiSettings('https://bi.test/api', 'fixture', max_output_bytes=100)
        for response, code in cases:
            client = SolarApiClient(self.catalog, small, httpx.MockTransport(lambda _: response))
            with self.subTest(code=code):
                self.assertEqual((await client.execute(call)).error.code, code)

    async def test_response_redacts_token_and_does_not_retry_mutations(self) -> None:
        """上游即便回显凭据也会脱敏；修改超时仅返回状态，不自行重试。"""
        transport = httpx.MockTransport(lambda _: httpx.Response(200, json={'code': 200, 'data': {'token': 'fixture-token', 'note': 'fixture-token'}}))
        result = await SolarApiClient(self.catalog, self.settings, transport).execute(ApiCall(self.endpoint_id('/eventConfig/findByProductKey'), 'fixture'))
        self.assertNotIn('fixture-token', result.to_json(('fixture-token',)))
        count = 0
        def timeout(request: httpx.Request) -> httpx.Response:
            """模拟 request 已发送后的超时，count 记录尝试次数。"""
            nonlocal count
            count += 1
            raise httpx.ReadTimeout('fixture', request=request)
        enabled = ApiSettings('https://bi.test/api', 'fixture-token', 'https://portal.test/portal-api', allow_mutations=True)
        call = ApiCall(self.endpoint_id('/portal/experiment/setOnline'), 'fixture', {'id': 7}, change_reason='明确的测试修改意图')
        failed = await SolarApiClient(self.catalog, enabled, httpx.MockTransport(timeout)).execute(call, True)
        self.assertFalse(failed.error.retryable)
        self.assertEqual(count, 1)

    def test_catalog_contracts_and_packaged_process_are_self_contained(self) -> None:
        """所有可执行契约合法且有后端证据；ZIP 在独立目录中可搜索接口，不依赖业务源码仓库。"""
        for endpoint in self.catalog.entries.values():
            for schema in (endpoint.query_schema, endpoint.body_schema, endpoint.path_schema):
                if schema is not None:
                    Draft202012Validator.check_schema(schema)
            if endpoint.operation in ('read', 'write'):
                self.assertTrue(endpoint.document['backend_sources'])
                self.assertFalse(any(source['file'].endswith('TestController.java') for source in endpoint.document['backend_sources']))
        content = export_builtin('bi-metadata')
        checked = check_package(content)
        self.assertEqual(checked.manifest.version, '2.0.1')
        self.assertEqual(checked.manifest.tools, ['BiCli', 'SolarEventCount', 'SolarCatalog', 'SolarQuery', 'SolarMutate'])
        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                archive.extractall(directory)
            root = Path(directory)
            self.assertTrue((root / 'executor/solar_api/catalog.json').exists())
            for name in checked.manifest.skill_files:
                self.assertTrue((root / name).is_file())
            env = {**os.environ, 'PLUGIN_VALUES': '{}', 'PLUGIN_SECRETS': '{}'}
            result = subprocess.run([sys.executable, str(root / 'executor/main.py')], input=json.dumps({'tool_name': 'SolarCatalog', 'arguments': {'action': 'search', 'service': 'rule', 'search': 'experiment list', 'limit': 5}}), capture_output=True, text=True, env=env, cwd=directory, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload['ok'])
            self.assertGreater(payload['data']['total'], 0)


class SourceExtractionTests(unittest.TestCase):
    """用精简源码验证提取器忽略废弃注释并保持复杂参数和多次 Gin 绑定。"""
    def test_java_ignores_commented_route_and_preserves_body_and_query(self) -> None:
        """JSON DTO 与 showSql 查询分开，已注释的旧路由不计入覆盖。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'DemoController.java'
            source.write_text('''@RestController @RequestMapping("report") public class DemoController {
            // @PostMapping("old") public Object old() {return null;}
            @PostMapping("eventAnalysis") public Object query(@RequestBody DemoDto dto, @RequestParam(value="showSql", required=false) boolean showSql) {return null;}}
            ''')
            (root / 'DemoDto.java').write_text('public class DemoDto { private String productKey; private java.util.List<String> events; }')
            index = SourceIndex({'bi-docker': root})
            index.load()
            endpoints = java_endpoints(index)
            self.assertEqual(len(endpoints), 1)
            self.assertEqual(endpoints[0]['path'], '/report/eventAnalysis')
            self.assertIn('showSql', endpoints[0]['query_schema']['properties'])
            self.assertIn('productKey', endpoints[0]['body_schema']['properties'])

    def test_go_multiple_bindings_and_defaults_are_not_false_requirements(self) -> None:
        """GET 多个 DTO 都要提取；默认 TimeType=1 不应误标成必填。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'router').mkdir()
            (root / 'router/routes.go').write_text('''package router
            func routes(r *gin.Engine) {
              group := r.Group(groupPath("portal/experiment"))
              group.GET("/list", List)
            }
            func List(c *gin.Context) {
              var page Page
              var query Query
              c.ShouldBind(&page)
              c.ShouldBind(&query)
              secondary := c.Request.URL.Query().Get("secondary")
              if secondary == "" { appG.Response(200, e.InvalidParams, nil); return }
              if query.AppId <= 0 { appG.Response(200, e.InvalidParams, nil); return }
              if query.TimeType == 0 { query.TimeType = 1 }
            }
            type Page struct { PageNum int `form:"pageNum"` }
            type Query struct {
              AppId int `form:"appId"`
              TimeType int `form:"timeType"`
            }
            ''')
            index = SourceIndex({'rule': root})
            index.load()
            endpoint = go_endpoints(index)[0]
            self.assertEqual(endpoint['gateway_path'], '/portal/ab/experiment/list')
            self.assertIn('appId', endpoint['query_schema']['properties'])
            self.assertIn('pageNum', endpoint['query_schema']['properties'])
            self.assertEqual(endpoint['query_schema']['required'], ['appId', 'secondary'])


if __name__ == '__main__':
    unittest.main()
