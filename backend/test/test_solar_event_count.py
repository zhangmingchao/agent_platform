"""事件计数业务验证：日期口径、统计值解析、失败停止及请求可追踪。"""
from __future__ import annotations

import asyncio
import json
import unittest
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from unittest.mock import patch

import httpx

from backend.plugins.bi_metadata.executor.solar_api.client import ApiCatalog, ApiInputError, ApiSettings, SolarApiClient
from backend.plugins.bi_metadata.executor.solar_api.event_count import EventCounter, EventCountRequest


class EventCountTests(unittest.IsolatedAsyncioTestCase):
    """使用固定响应模拟实际四阶段 HTTP 流程；requests 保存请求以验证边界与停止行为。"""
    def setUp(self) -> None:
        """准备测试配置，不读取真实用户配置、生产数据库或 Token。"""
        self.requests: list[httpx.Request] = []
        self.catalog = ApiCatalog()
        self.settings = ApiSettings('https://fixture.test/api', 'fixture-token')

    def respond(self, request: httpx.Request) -> httpx.Response:
        """按 request 固定路径返回业务响应，使用前后端源码实际定义的字段形状。"""
        self.requests.append(request)
        data: object
        if request.url.path.endswith('/getCurrentTimeZoneDetail'):
            data = {'timeZone': 'Etc/GMT-8'}
        elif request.url.path.endswith('/findEventList'):
            data = [{'eventName': '_appEnd', 'eventClassify': 1}]
        elif request.url.path.endswith('/findProfileArithListByEvent'):
            data = {'preset': [{'id': '-1', 'code': 'totalNumber', 'tableType': 0}, {'id': '-2', 'code': 'userNumber'}]}
        else:
            data = {'tableData': {'column': ['dt', 'event_0'], 'val': [{'dt': '合计', 'event_0': ['42']}]}, 'numUpLimit': False}
        return httpx.Response(200, json={'code': 200, 'data': data})

    def counter(self, handler: Callable[[httpx.Request], httpx.Response | Awaitable[httpx.Response]] | None = None) -> EventCounter:
        """创建使用 handler 响应的计数器；时钟固定在 UTC 10 月 24 日、东八区 25 日。"""
        client = SolarApiClient(self.catalog, self.settings, httpx.MockTransport(handler or self.respond))
        return EventCounter(client, lambda: datetime(2026, 10, 24, 17, 0, tzinfo=timezone.utc))

    async def test_today_uses_product_zone_and_real_metric_in_one_flow(self) -> None:
        """today 按产品时区转换；所有请求保持产品与应用范围，报表使用合计和真实指标。"""
        result = await self.counter().execute(EventCountRequest('product', '_appEnd'))
        self.assertTrue(result.ok)
        self.assertEqual(result.data.count, 42)
        self.assertEqual(result.data.start_date, '2026-10-25')
        self.assertEqual(result.data.time_zone, 'Etc/GMT-8')
        self.assertEqual(len(self.requests), 4)
        body = json.loads(self.requests[-1].content)
        self.assertEqual(body['dateType'], 0)
        self.assertEqual(body['timeParticle'], 5)
        self.assertFalse(body['isShowSummary'])
        self.assertFalse(body['isApproximate'])
        self.assertEqual(body['behaviorContents'][0]['arithId'], '-1')
        self.assertNotIn('funcSqls', body['behaviorContents'][0])
        for request in self.requests:
            self.assertEqual(request.headers['pk'], 'product')
            self.assertEqual(request.headers['isallapp'], '1')
            self.assertTrue(request.headers['request-id'])

    async def test_explicit_zone_apps_and_client_time_preserve_scope(self) -> None:
        """指定时区跳过产品时区查询；应用 ID 与客户端时间传给每个相关请求。"""
        request = EventCountRequest.from_arguments({'product_key': 'product', 'event_name': '_appEnd', 'date': 'yesterday',
                                                   'time_zone': 'Asia/Shanghai', 'app_ids': [13], 'time_type': 'client'})
        result = await self.counter().execute(request)
        self.assertTrue(result.ok)
        self.assertEqual(result.data.start_date, '2026-10-24')
        self.assertEqual(len(self.requests), 3)
        self.assertEqual(json.loads(self.requests[-1].content)['timeType'], 2)
        for item in self.requests:
            self.assertEqual(item.headers['appids'], '13')
            self.assertEqual(item.headers['isallapp'], '0')

    async def test_upstream_business_failure_stops_without_retry_and_keeps_scope(self) -> None:
        """HTTP 200/code500 不返回 0，保留 stage、接口、请求编号且不重复查询。"""
        def fail(request: httpx.Request) -> httpx.Response:
            """报表 request 模拟业务失败，其他接口使用正常元数据。"""
            if request.url.path.endswith('/eventAnalysis'):
                self.requests.append(request)
                return httpx.Response(200, json={'code': 500, 'msg': 'fixture-token SELECT private_secret'})
            return self.respond(request)
        result = await self.counter(fail).execute(EventCountRequest('product', '_appEnd'))
        self.assertFalse(result.ok)
        self.assertIsNone(result.data.count)
        self.assertEqual(result.data.start_date, '2026-10-25')
        self.assertEqual(result.error.stage, 'report_query')
        self.assertEqual(result.error.upstream_code, 500)
        self.assertEqual(result.error.request_id, self.requests[-1].headers['request-id'])
        self.assertEqual(len(self.requests), 4)
        self.assertNotIn('private_secret', result.to_json(('fixture-token',)))

    async def test_missing_event_or_metric_never_calls_report(self) -> None:
        """无事件或无总次数元数据时结束，不使用猜测分类或用户数继续调用报表。"""
        for failed_path, code in (('/findEventList', 'EVENT_NOT_RESOLVED'), ('/findProfileArithListByEvent', 'METRIC_NOT_RESOLVED')):
            self.requests.clear()
            def missing(request: httpx.Request) -> httpx.Response:
                """failed_path 对应 request 返回空元数据，其他阶段正常。"""
                if request.url.path.endswith(failed_path):
                    self.requests.append(request)
                    return httpx.Response(200, json={'code': 200, 'data': []})
                return self.respond(request)
            result = await self.counter(missing).execute(EventCountRequest('product', '_appEnd'))
            self.assertEqual(result.error.code, code)
            self.assertIsNone(result.data.count)
            self.assertFalse(any(r.url.path.endswith('/eventAnalysis') for r in self.requests))

    def test_zero_is_valid_but_empty_ambiguous_or_formatted_counts_are_unknown(self) -> None:
        """真实零、整数有效；空表、重复汇总、单位缩写、非整数及截断不能推断条数。"""
        self.assertEqual(EventCounter.count({'tableData': {'val': [{'event_0': [0]}]}}), 0)
        self.assertEqual(EventCounter.count({'tableData': {'val': [{'event_0': '123.00'}]}}), 123)
        for data in ({'total': 42}, {'tableData': {'val': []}}, {'tableData': {'val': [{'event_0': 42}, {'event_0': 42}]}},
                     {'tableData': {'val': [{'event_0': '1.2万'}]}}, {'tableData': {'val': [{'event_0': 1.5}]}},
                     {'numUpLimit': True, 'tableData': {'val': [{'event_0': 42}]}}):
            with self.assertRaises(ApiInputError):
                EventCounter.count(data)

    async def test_invalid_scope_and_overall_timeout_stop_before_more_requests(self) -> None:
        """拒绝任意凭据、无效日期和超大范围；总超时取消执行，不进入后续阶段。"""
        for values in ({'token': 'spoof'}, {'date': '20261025'}, {'app_ids': []}, {'time_zone': 'unknown/zone'}):
            with self.assertRaises(ApiInputError):
                EventCountRequest.from_arguments({'product_key': 'product', 'event_name': '_appEnd', **values})
        result = await self.counter().execute(EventCountRequest('product', '_appEnd', '2026-01-01', '2026-10-25', 'Asia/Shanghai'))
        self.assertFalse(result.ok)
        self.assertEqual(self.requests, [])
        async def slow(request: httpx.Request) -> httpx.Response:
            """模拟 request 卡住；验证总期限生效，不等到单接口 30 秒超时。"""
            self.requests.append(request)
            await asyncio.sleep(1)
            return httpx.Response(200, json={'code': 200})
        original_timeout = asyncio.timeout
        with patch('backend.plugins.bi_metadata.executor.solar_api.event_count.asyncio.timeout', side_effect=lambda _: original_timeout(0.01)):
            result = await self.counter(slow).execute(EventCountRequest('product', '_appEnd'))
        self.assertEqual(result.error.code, 'COUNT_TIMEOUT')
        self.assertEqual(result.error.stage, 'time_zone')
        self.assertEqual(len(self.requests), 1)


if __name__ == '__main__':
    unittest.main()
