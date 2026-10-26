"""事件总次数流程：固定接口获取真实元数据，一次工具调用完成报表查询。"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .client import ApiCall, ApiFailure, ApiInputError, ApiResult, SolarApiClient, UpstreamResult


@dataclass(frozen=True)
class EventCountRequest:
    """统计请求；产品/事件明确身份，date 为 today/yesterday/自然日，end_date 为可选末日。

    time_zone 留空时读取产品时区；app_ids 指定应用数字 ID，空元组表示全部应用；
    time_type 区分 server 服务端时间和 client 客户端时间，不允许模型传入 SQL 或凭据。
    """
    product_key: str
    event_name: str
    date: str = 'today'
    end_date: str | None = None
    time_zone: str | None = None
    app_ids: tuple[int, ...] = ()
    time_type: str = 'server'

    @classmethod
    def from_arguments(cls, arguments: dict[str, Any]) -> EventCountRequest:
        """校验 arguments 工具 JSON 边界并返回实体；拒绝未知字段和不明确的应用范围。"""
        schema = {'type': 'object', 'additionalProperties': False, 'required': ['product_key', 'event_name'], 'properties': {
            'product_key': {'type': 'string', 'minLength': 1, 'maxLength': 200},
            'event_name': {'type': 'string', 'minLength': 1, 'maxLength': 200},
            'date': {'type': 'string', 'minLength': 1}, 'end_date': {'type': 'string', 'minLength': 1},
            'time_zone': {'type': 'string', 'minLength': 1, 'maxLength': 80},
            'app_ids': {'type': 'array', 'minItems': 1, 'maxItems': 200, 'uniqueItems': True, 'items': {'type': 'integer', 'minimum': 1}},
            'time_type': {'enum': ['server', 'client']}}}
        SolarApiClient.validate(arguments, schema, '参数')
        request = cls(**{**arguments, 'app_ids': tuple(arguments.get('app_ids', []))})
        if not request.product_key.strip() or not request.event_name.strip():
            raise ApiInputError('INVALID_ARGUMENTS', '产品与事件不能为空白字符串')
        # 静态日期在网络访问前校验，today/yesterday 在产品时区确定后解析。
        for value in (request.date, request.end_date):
            if value is not None and value not in ('today', 'yesterday'):
                cls.parse_date(value)
        if request.time_zone:
            cls.zone(request.time_zone)
        return request

    @staticmethod
    def parse_date(value: str) -> date:
        """解析 value 的 YYYY-MM-DD 格式，避免把时间戳或相对表达式误作自然日。"""
        try:
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError()
            return parsed
        except ValueError as exc:
            raise ApiInputError('INVALID_ARGUMENTS', '日期仅支持 today、yesterday 或 YYYY-MM-DD') from exc

    @staticmethod
    def zone(value: str) -> ZoneInfo:
        """把 value 转为 IANA 时区实体；未知时区不得回退到容器的本地时区。"""
        try:
            return ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ApiInputError('INVALID_TIME_ZONE', '时区无法识别，请指定有效 IANA 时区，例如 Asia/Shanghai') from exc


@dataclass(frozen=True)
class EventCountOutcome:
    """统计结果；count 为明确返回的总次数，失败时为 None，绝不把错误或空表当成 0。

    日期为包含首尾的自然日；time_zone/time_type/app_ids 记录统计范围；
    stage 记录执行阶段，queried_at 是请求开始时间，endpoint_id 指向固定报表契约。
    """
    product_key: str
    event_name: str
    count: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    time_zone: str | None = None
    time_type: str = 'server'
    app_ids: tuple[int, ...] = ()
    all_apps: bool = True
    stage: str = 'time_zone'
    queried_at: str = ''
    metric: str = 'totalNumber'
    endpoint_id: str = 'bi.post.report_eventAnalysis.e914f96e'


def objects(value: Any) -> Iterator[dict[str, Any]]:
    """遍历 value 的业务 JSON 对象，仅用于检索事件和计算方式，不执行其中表达式。"""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


class EventCounter:
    """固定事件计数流程；client 为目录客户端，now 为可测试的 UTC 时钟。

    每阶段最多请求一次；总耗时最多 25 秒。字段与结果以实体传递，JSON 只存在接口边界。
    """
    def __init__(self, client: SolarApiClient, now: Callable[[], datetime] | None = None) -> None:
        """初始化；client 复用平台配置，now 可替换时钟以验证跨时区与跨日行为。"""
        self.client = client
        self.now = now or (lambda: datetime.now(timezone.utc))

    async def call(self, path: str, request: EventCountRequest, context: dict[str, Any], body: Any = None) -> ApiResult:
        """调用固定 path；request 提供产品身份，context 提供应用/时区，body 为内部构造业务体。"""
        endpoint = next(e for e in self.client.catalog.entries.values() if e.path == path and e.operation == 'read')
        return await self.client.execute(ApiCall(endpoint.id, request.product_key, body=body, context=context))

    @staticmethod
    def business(result: ApiResult) -> Any:
        """读取 result 的接口业务数据；不是标准接口结果时拒绝推测数据位置。"""
        if not isinstance(result.data, UpstreamResult):
            raise ApiInputError('INVALID_RESPONSE', '接口没有返回标准业务结果')
        return result.data.data

    @staticmethod
    def count(result: Any) -> int:
        """提取 result.tableData.val 的唯一总计 event_0；拒绝分页总数、汇总重复和格式不明的值。

        源码依据：EventAnalysisTools.Convert/putGroupResult；timeParticle=5、无分组、
        isShowSummary=false 时只应有一个总计行，event_0 可包装为单元素数组。
        """
        if not isinstance(result, dict) or result.get('numUpLimit'):
            raise ApiInputError('INVALID_COUNT_RESULT', '统计结果不完整，无法确认总次数')
        table = result.get('tableData')
        rows = table.get('val') if isinstance(table, dict) else None
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            raise ApiInputError('INVALID_COUNT_RESULT', '报表未返回唯一总计行，不能把空结果解释为 0')
        value = rows[0].get('event_0')
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise ApiInputError('INVALID_COUNT_RESULT', '总次数值缺失或格式无法识别')
        try:
            number = Decimal(str(value))
            if not number.is_finite() or number < 0 or number != number.to_integral_value():
                raise InvalidOperation()
            return int(number)
        except InvalidOperation as exc:
            raise ApiInputError('INVALID_COUNT_RESULT', '总次数不是明确的非负整数，不返回估算值') from exc

    async def execute(self, request: EventCountRequest) -> ApiResult:
        """执行 request 的一次完整只读统计，失败携带阶段和范围信息，不自动重试上游请求。"""
        started = self.now()
        outcome = EventCountOutcome(request.product_key, request.event_name, time_type=request.time_type,
                                    app_ids=request.app_ids, all_apps=not request.app_ids, queried_at=started.isoformat())
        context: dict[str, Any] = {'app_ids': list(request.app_ids)} if request.app_ids else {'all_apps': True}

        def failure(result: ApiResult) -> ApiResult:
            """将 result 失败与当前 outcome 合并；保留请求编号，count 保持未知。"""
            error = result.error or ApiFailure('INVALID_RESPONSE', '接口未返回可识别结果')
            return ApiResult(False, outcome, replace(error, stage=outcome.stage))

        try:
            async with asyncio.timeout(25):
                zone_name = request.time_zone
                if not zone_name:
                    result = await self.call('/timeZone/getCurrentTimeZoneDetail', request, context)
                    if not result.ok:
                        return failure(result)
                    data = self.business(result)
                    zone_name = data.get('timeZone') if isinstance(data, dict) else None
                    if not isinstance(zone_name, str) or not zone_name:
                        raise ApiInputError('INVALID_TIME_ZONE', '无法取得产品时区，请明确指定 time_zone')
                zone = EventCountRequest.zone(zone_name)
                today = started.astimezone(zone).date()

                def resolve(value: str) -> date:
                    """把 value 的相对自然日按照已确认产品时区解析。"""
                    return today if value == 'today' else today - timedelta(days=1) if value == 'yesterday' else EventCountRequest.parse_date(value)

                first, last = resolve(request.date), resolve(request.end_date or request.date)
                if first > last or (last - first).days > 30 or last > today:
                    raise ApiInputError('INVALID_ARGUMENTS', '日期范围需首日不晚于末日，最多 31 天，且不能包含未来日期')
                context['time_zone'] = zone_name
                outcome = replace(outcome, start_date=first.isoformat(), end_date=last.isoformat(), time_zone=zone_name, stage='event_metadata')
                result = await self.call('/eventConfig/findEventList', request, context)
                if not result.ok:
                    return failure(result)
                matches = [item for item in objects(self.business(result)) if item.get('eventName') == request.event_name and 'eventClassify' in item]
                if len(matches) != 1 or not isinstance(matches[0]['eventClassify'], int):
                    raise ApiInputError('EVENT_NOT_RESOLVED', '事件不存在或分类不唯一，请核对事件标识；未执行报表查询')
                event = matches[0]
                outcome = replace(outcome, stage='metric_metadata')
                result = await self.call('/profileType/findProfileArithListByEvent', request, context, {
                    'productKey': request.product_key, 'eventName': request.event_name,
                    'eventClassify': event['eventClassify'], 'analysisType': 1})
                if not result.ok:
                    return failure(result)
                metrics = [item for item in objects(self.business(result)) if item.get('code') == 'totalNumber' and str(item.get('id')) == '-1']
                if len(metrics) != 1:
                    raise ApiInputError('METRIC_NOT_RESOLVED', '接口未返回唯一的总次数计算方式，不猜测指标参数')
                metric = metrics[0]
                outcome = replace(outcome, stage='report_query')
                # 与前端指标选择一致：总次数使用真实 arithId；不让模型编写 funcSqls。
                body = {'productKey': request.product_key, 'dateType': 0, 'startDate': first.isoformat(), 'endDate': last.isoformat(),
                        'timeParticle': 5, 'timeType': 1 if request.time_type == 'server' else 2, 'entityType': '_user_id',
                        'behaviorContents': [{'eventName': request.event_name, 'eventClassify': event['eventClassify'],
                                              'analysisType': 1, 'arithId': str(metric['id']), 'type': 1,
                                              'tableType': metric.get('tableType', 0), 'name': f'{request.event_name} 总次数',
                                              'filtrate': [], 'indFormat': 0}],
                        'groups': [], 'filtrate': [], 'relation': 'and', 'isShowSummary': False, 'isApproximate': False}
                result = await self.call('/report/eventAnalysis', request, context, body)
                if not result.ok:
                    return failure(result)
                outcome = replace(outcome, stage='parse_result')
                count = self.count(self.business(result))
                return ApiResult(True, replace(outcome, count=count, stage='completed'))
        except TimeoutError:
            return failure(ApiResult(False, error=ApiFailure('COUNT_TIMEOUT', '事件统计超过 25 秒，未取得结果；请停止本轮查询，不要原样重试')))
        except ApiInputError as exc:
            return failure(ApiResult(False, error=ApiFailure(exc.code, str(exc))))
