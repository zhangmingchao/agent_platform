"""基于固定接口目录执行 BI / Rule 业务请求；配置与密钥只由平台环境注入。"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit
from uuid import uuid4

import httpx
from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class ApiFailure:
    """失败实体；code 为稳定错误类别，message 为脱敏说明，retryable 仅标记可重试查询。"""
    code: str
    message: str
    retryable: bool = False
    # 固定接口身份、HTTP/业务状态和请求编号用于定位失败，不回传任意上游文本。
    endpoint_id: str | None = None
    http_status: int | None = None
    upstream_code: int | str | None = None
    request_id: str | None = None
    stage: str | None = None


@dataclass(frozen=True)
class ApiResult:
    """插件结果实体；ok 表示调用成功，data 为实体或业务 JSON，error 为结构化失败。"""
    ok: bool
    data: Any = None
    error: ApiFailure | None = None

    def to_json(self, secrets: tuple[str, ...] = ()) -> str:
        """序列化并脱敏；secrets 是当前平台注入的 Token，禁止出现在任何结果字段。"""
        def clean(value: Any) -> Any:
            """递归清理 value 的认证字段和敏感字符串，仅用于 JSON 输出边界。"""
            if isinstance(value, dict):
                return {key: ('[REDACTED]' if key.lower().replace('_', '').replace('-', '') in {'token', 'accesstoken', 'authorization', 'password', 'encryptedtoken'} else clean(item)) for key, item in value.items()}
            if isinstance(value, list):
                return [clean(item) for item in value]
            if isinstance(value, str):
                for secret in sorted(set(secrets), key=len, reverse=True):
                    if secret:
                        value = value.replace(secret, '[REDACTED]')
            return value
        return json.dumps(clean(asdict(self)), ensure_ascii=False, allow_nan=False)


class ApiInputError(ValueError):
    """可预期的输入/契约错误；code 和 message 返回业务失败，不回显认证配置。"""
    def __init__(self, code: str, message: str) -> None:
        """初始化错误；code 为失败类别，message 为可公开的中文说明。"""
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Endpoint:
    """接口实体；id/path/method 固定请求身份，operation 决定查询或修改入口。

    service 区分 BI/Rule；gateway_path 为 Portal 代理路径；schemas 保存请求契约。
    document 是源码追溯、前端返回声明及可用性说明，仅用于查询目录。
    """
    id: str
    service: str
    path: str
    method: str
    operation: str
    gateway_path: str | None
    query_schema: dict[str, Any]
    body_schema: dict[str, Any] | None
    path_schema: dict[str, Any]
    document: dict[str, Any] = field(repr=False)

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> Endpoint:
        """将 document 目录边界结构转换成请求实体，不执行目录中的任何源码内容。"""
        return cls(**{key: document.get(key) for key in ('id', 'service', 'path', 'method', 'operation', 'gateway_path', 'query_schema', 'body_schema', 'path_schema')}, document=document)


@dataclass(frozen=True)
class CatalogPage:
    """目录查询分页；total/offset/limit 描述页位置，items 是轻量接口摘要，summary 是覆盖统计。"""
    total: int
    offset: int
    limit: int
    items: list[dict[str, Any]]
    summary: dict[str, Any]


class ApiCatalog:
    """固定包内接口目录；entries 索引实体，metadata 保存源码版本及覆盖统计。"""
    def __init__(self, path: Path | None = None) -> None:
        """读取 path 指定的受信任目录；生产默认为同目录 catalog.json，模型不能覆盖此路径。"""
        self.metadata = json.loads((path or Path(__file__).with_name('catalog.json')).read_text())
        self.entries = {item['id']: Endpoint.from_document(item) for item in self.metadata['endpoints']}

    def describe(self, endpoint_id: str) -> Endpoint:
        """按 endpoint_id 返回完整实体；未知接口在网络请求之前拒绝。"""
        if endpoint_id not in self.entries:
            raise ApiInputError('UNKNOWN_ENDPOINT', '接口 ID 不存在，请先用 SolarCatalog 搜索')
        return self.entries[endpoint_id]

    def search(self, search: str = '', service: str = 'all', module: str = '', operation: str = 'all', offset: int = 0, limit: int = 20) -> CatalogPage:
        """检索目录；search 为关键词，service/module/operation 过滤，offset/limit 控制分页。"""
        if service not in ('all', 'bi', 'rule') or operation not in ('all', 'read', 'write', 'internal', 'special', 'unverified'):
            raise ApiInputError('INVALID_ARGUMENTS', '服务或操作类型无效')
        if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= 50:
            raise ApiInputError('INVALID_ARGUMENTS', '目录 offset 必须非负，limit 在 1 到 50 之间')
        keywords = search.strip().lower().split()
        matches = []
        for endpoint in self.entries.values():
            doc = endpoint.document
            text = ' '.join((endpoint.id, endpoint.path, doc['description'], *doc.get('frontend_paths', []))).lower()
            if (service == 'all' or service == endpoint.service) and (not module or module == doc['module']) and (operation == 'all' or operation == endpoint.operation) and all(word in text for word in keywords):
                matches.append({key: doc.get(key) for key in ('id', 'service', 'method', 'path', 'description', 'module', 'operation', 'match_status', 'schema_status', 'unavailable_reason')})
        return CatalogPage(len(matches), offset, limit, matches[offset:offset + limit], self.metadata['summary'])


@dataclass(frozen=True)
class ApiSettings:
    """执行配置；BI 地址、Portal 网关地址及 Token 按用户注入，allow_mutations 控制修改能力。

    timeout_seconds/max_output_bytes 限制网络和输出；rule_token 留空时复用 BI 登录 Token。
    """
    base_url: str
    token: str = field(repr=False)
    portal_base_url: str = ''
    rule_token: str = field(default='', repr=False)
    allow_mutations: bool = False
    timeout_seconds: int = 30
    max_output_bytes: int = 1024 * 1024

    @classmethod
    def from_environment(cls, values: dict[str, Any], secrets: dict[str, str]) -> ApiSettings:
        """从平台 values 普通配置与 secrets 凭据构造实体，不从模型输入读取认证参数。"""
        return cls(str(values.get('base_url') or ''), secrets.get('token', ''), str(values.get('portal_base_url') or ''), secrets.get('rule_token', ''), values.get('allow_mutations') is True, int(values.get('timeout_seconds', 30)), int(values.get('max_output_bytes', 1048576)))


@dataclass(frozen=True)
class ApiCall:
    """业务调用实体；endpoint_id 固定工具契约，product_key 确定产品，query/body/path 为业务参数。

    context 仅接受应用选择与时区/语言；change_reason 为修改意图说明，不是用户授权凭证。
    """
    endpoint_id: str
    product_key: str
    query: dict[str, Any] = field(default_factory=dict)
    body: Any = None
    path: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    change_reason: str = ''


@dataclass(frozen=True)
class UpstreamResult:
    """上游结果；endpoint_id 标识接口，http_status/code 描述成功状态，data 保留业务返回结构。"""
    endpoint_id: str
    service: str
    http_status: int
    code: int | str | None
    data: Any
    time_zone: str | None = None


@dataclass(frozen=True)
class PreparedCall:
    """已校验的 HTTP 请求实体；endpoint/url 固定目标，headers 隐藏凭据，query/body 保留参数位置。"""
    endpoint: Endpoint
    url: str
    headers: dict[str, str] = field(repr=False)
    query: dict[str, Any] = field(default_factory=dict)
    body: Any = None


class SolarApiClient:
    """固定目录 HTTP 客户端；catalog 提供路径与语义，settings 提供配置，transport 用于行为测试。"""
    def __init__(self, catalog: ApiCatalog, settings: ApiSettings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        """创建客户端；catalog/settings 不来自模型，transport 只在测试中覆盖网络传输。"""
        self.catalog = catalog
        self.settings = settings
        self.transport = transport

    @staticmethod
    def validate(value: Any, schema: dict[str, Any], section: str) -> None:
        """校验 value 对应 schema；section 是 query/body/path 标签，错误只显示字段位置。"""
        errors = list(Draft202012Validator(schema).iter_errors(value))
        if errors:
            location = '.'.join(str(part) for part in errors[0].path)
            raise ApiInputError('INVALID_ARGUMENTS', f'{section}.{location or "参数"} 不符合接口契约（{errors[0].validator}），请读取接口详情')

    def prepare(self, call: ApiCall, mutation: bool) -> PreparedCall:
        """校验 call 并构建请求；mutation 由工具名称决定，模型不能将修改接口伪装为查询。"""
        endpoint = self.catalog.describe(call.endpoint_id)
        expected = 'write' if mutation else 'read'
        if endpoint.operation != expected:
            raise ApiInputError('OPERATION_NOT_ALLOWED', endpoint.document.get('unavailable_reason') or f'此接口为 {endpoint.operation}，不能使用当前工具执行')
        if mutation and (not self.settings.allow_mutations or not call.change_reason.strip()):
            raise ApiInputError('MUTATION_DISABLED', '修改操作需要插件配置允许修改，并明确填写 change_reason；仍受平台工具权限控制')
        if not call.product_key.strip() or len(call.product_key) > 200:
            raise ApiInputError('INVALID_ARGUMENTS', 'product_key 必须为明确的产品标识')
        base = self.settings.base_url if endpoint.service == 'bi' else self.settings.portal_base_url
        token = self.settings.token if endpoint.service == 'bi' else self.settings.rule_token or self.settings.token
        parsed = urlsplit(base)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or not token.strip():
            raise ApiInputError('CONFIGURATION_ERROR', '请配置对应服务基础地址和登录 Token；Rule 使用 Portal 网关地址，不直连内部服务')
        route = endpoint.path if endpoint.service == 'bi' else endpoint.gateway_path
        if route is None or '..' in route or not route.startswith('/') or route.startswith('//'):
            raise ApiInputError('INVALID_CONTRACT', '目录接口路径不可执行')
        self.validate(call.path, endpoint.path_schema, 'path')
        for key, value in call.path.items():
            if str(value) in ('.', '..'):
                raise ApiInputError('INVALID_ARGUMENTS', '路径参数不能为目录跳转')
            route = route.replace('{' + key + '}', quote(str(value), safe=''))
        if '{' in route or '}' in route:
            raise ApiInputError('INVALID_ARGUMENTS', '缺少接口路径参数')
        query = dict(call.query)
        body = json.loads(json.dumps(call.body, allow_nan=False)) if call.body is not None else None
        for name in ('productKey', 'proKey'):
            if name in query and query[name] != call.product_key or isinstance(body, dict) and name in body and body[name] != call.product_key:
                raise ApiInputError('PRODUCT_MISMATCH', '请求产品标识与 product_key 不一致')
        if 'productKey' in endpoint.query_schema.get('properties', {}):
            query.setdefault('productKey', call.product_key)
        if isinstance(body, dict) and 'productKey' in (endpoint.body_schema or {}).get('properties', {}):
            body.setdefault('productKey', call.product_key)
        for key, schema in endpoint.query_schema.get('properties', {}).items():
            if 'default' in schema:
                query.setdefault(key, schema['default'])
        self.validate(query, endpoint.query_schema, 'query')
        if endpoint.body_schema is None and body is not None:
            raise ApiInputError('INVALID_ARGUMENTS', '此接口没有已解析的 JSON 请求体，不能发送任意 body')
        if endpoint.body_schema is not None:
            self.validate(body, endpoint.body_schema, 'body')
        if any(isinstance(value, dict) or isinstance(value, list) and any(isinstance(item, (dict, list)) for item in value) for value in query.values()):
            raise ApiInputError('INVALID_ARGUMENTS', 'query 只接受标量或标量数组，嵌套条件请按接口契约放入 body')
        context_schema = {'type': 'object', 'additionalProperties': False, 'properties': {'app_ids': {'type': 'array', 'items': {'type': ['string', 'integer']}, 'maxItems': 200}, 'all_apps': {'type': 'boolean'}, 'language': {'enum': ['zh', 'en']}, 'time_zone': {'type': 'string', 'maxLength': 80}, 'system_type': {'enum': ['product', 'app']}, 'country_region': {'type': 'string', 'maxLength': 20}}}
        self.validate(call.context, context_schema, 'context')
        headers = {'Accept': 'application/json', 'token': token, 'pk': call.product_key, 'language': call.context.get('language', 'zh'), 'request-id': uuid4().hex}
        headers['SystemType'] = call.context.get('system_type', 'product')
        if 'app_ids' in call.context:
            headers['appids'] = ','.join(str(value) for value in call.context['app_ids'])
            headers['isallapp'] = '0'
        elif call.context.get('all_apps') is True:
            headers['isallapp'] = '1'
            headers['appids'] = ''
        if call.context.get('time_zone'):
            headers['timeZone'] = call.context['time_zone']
        if call.context.get('country_region'):
            headers['Country-Region'] = call.context['country_region']
        return PreparedCall(endpoint, base.rstrip('/') + route, headers, query, body)

    async def execute(self, call: ApiCall, mutation: bool = False) -> ApiResult:
        """执行 call 并返回实体；mutation 对应修改工具，网络失败不自动重试修改。"""
        try:
            prepared = self.prepare(call, mutation)
            endpoint = prepared.endpoint
        except ApiInputError as exc:
            return ApiResult(False, error=ApiFailure(exc.code, str(exc)))
        query_items = [(key, ('true' if item is True else 'false' if item is False else item)) for key, value in prepared.query.items() for item in (value if isinstance(value, list) else [value]) if item is not None]
        try:
            async with httpx.AsyncClient(timeout=self.settings.timeout_seconds, transport=self.transport, follow_redirects=False) as client:
                async with client.stream(endpoint.method, prepared.url, headers=prepared.headers, params=query_items, json=prepared.body) as response:
                    chunks = bytearray()
                    async for chunk in response.aiter_bytes():
                        chunks.extend(chunk)
                        if len(chunks) > self.settings.max_output_bytes:
                            return ApiResult(False, error=ApiFailure('OUTPUT_TOO_LARGE', '结果超过配置上限，请缩小日期范围或使用分页'))
                    status = response.status_code
        except httpx.TimeoutException:
            message = '修改接口超时，可能已执行，请先查状态' if mutation else '查询接口超时，本次未取得结果，请勿解释为 0'
            return ApiResult(False, error=ApiFailure('TIMEOUT', message, not mutation, endpoint.id, request_id=prepared.headers['request-id']))
        except httpx.HTTPError:
            return ApiResult(False, error=ApiFailure('NETWORK_ERROR', '接口网络异常；请检查容器网络和服务配置', not mutation))
        if status == 404:
            message = '接口返回 HTTP 404，请检查服务地址与部署版本；BI 基础地址须包含 /api'
            return ApiResult(False, error=ApiFailure('NOT_FOUND', message))
        if 300 <= status < 400:
            return ApiResult(False, error=ApiFailure('REDIRECT', '接口返回重定向，请配置最终 API 地址'))
        try:
            payload = json.loads(chunks)
        except (ValueError, UnicodeError):
            return ApiResult(False, error=ApiFailure('INVALID_RESPONSE', f'接口未返回 JSON（HTTP {status}），请检查 API 地址'))
        code = payload.get('code') if isinstance(payload, dict) else None
        try:
            numeric = int(code) if code is not None else None
        except (ValueError, TypeError):
            numeric = -1
        if status >= 400 or numeric not in (None, 200):
            if status == 401 or numeric in (401, 405, 406, 407, 408, 409, 20001, 20002, 20003, 20004, 300009):
                error = 'UNAUTHENTICATED'
            elif status == 403 or numeric in (403, 420, 1005, 4001):
                error = 'PERMISSION_DENIED'
            elif status == 429:
                error = 'RATE_LIMITED'
            elif numeric == 404:
                error = 'RESOURCE_NOT_FOUND'
            else:
                error = 'UPSTREAM_ERROR'
            # 不转发任意上游错误文本，保留状态码方便定位，避免泄露 Token 或 SQL。
            return ApiResult(False, error=ApiFailure(error, f'接口业务失败（HTTP {status}，code={code}）；未取得结果，请按 request_id 定位服务端日志，不要原样重复调用', not mutation and (status == 429 or status >= 500), endpoint.id, status, code, prepared.headers['request-id']))
        business = payload.get('data') if isinstance(payload, dict) and 'code' in payload else payload
        zone = payload.get('timeZone') if isinstance(payload, dict) else None
        return ApiResult(True, UpstreamResult(endpoint.id, endpoint.service, status, code, business, zone))


async def dispatch(tool_name: str, arguments: dict[str, Any], values: dict[str, Any], secrets: dict[str, str]) -> ApiResult:
    """分发 tool_name；arguments 是业务参数，values/secrets 只由平台注入，返回统一实体。"""
    try:
        catalog = ApiCatalog()
        if tool_name == 'SolarEventCount':
            # 业务流程在一次工具调用内执行，模型只提供产品、事件与统计范围。
            from .event_count import EventCountRequest, EventCounter
            request = EventCountRequest.from_arguments(arguments)
            return await EventCounter(SolarApiClient(catalog, ApiSettings.from_environment(values, secrets))).execute(request)
        if tool_name == 'SolarCatalog':
            action = arguments.get('action', 'search')
            if action == 'describe':
                endpoint = catalog.describe(str(arguments.get('endpoint_id', '')))
                return ApiResult(True, endpoint.document)
            if action != 'search':
                raise ApiInputError('INVALID_ARGUMENTS', 'action 仅支持 search / describe')
            return ApiResult(True, catalog.search(**{key: arguments[key] for key in ('search', 'service', 'module', 'operation', 'offset', 'limit') if key in arguments}))
        if tool_name not in ('SolarQuery', 'SolarMutate'):
            raise ApiInputError('UNKNOWN_TOOL', '工具名称不存在')
        allowed = {'endpoint_id', 'product_key', 'query', 'body', 'path', 'context', 'change_reason'}
        if set(arguments) - allowed:
            raise ApiInputError('INVALID_ARGUMENTS', '不允许传入 URL、认证字段或任意请求头')
        call = ApiCall(**arguments)
        return await SolarApiClient(catalog, ApiSettings.from_environment(values, secrets)).execute(call, tool_name == 'SolarMutate')
    except ApiInputError as exc:
        return ApiResult(False, error=ApiFailure(exc.code, str(exc)))
    except (TypeError, ValueError):
        return ApiResult(False, error=ApiFailure('INVALID_ARGUMENTS', '工具参数或配置格式错误，请先读取接口契约'))
