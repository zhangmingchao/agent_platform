"""从前端 AST 契约和 BI Java / Rule Go 源码生成插件接口目录与分模块参考。

使用参数 --frontend、--bidocker、--rule 指定参考项目；--frontend-contracts 是 AST 提取结果。
脚本只读取业务源码，不连接线上服务。未知类型、前后端差异和内部接口保留明确状态。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def clean_comments(text: str) -> str:
    """移除 text 的代码注释，保留字符串和字符偏移，避免把注释中的旧接口计入目录。"""
    pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`[^`]*`|/\*[\s\S]*?\*/|//[^\n]*'
    return re.sub(pattern, lambda m: re.sub(r'[^\n]', ' ', m[0]) if m[0].startswith(('/*', '//')) else m[0], text)


def closing(text: str, start: int, left: str = '{', right: str = '}') -> int:
    """在 text 中查找 start 起始的成对 left/right；忽略字符串，失败时拒绝静默截断。"""
    level = 0
    string = ''
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if string:
            if char == string and not escaped:
                string = ''
            escaped = char == '\\' and not escaped
            continue
        if char in ('"', "'", '`'):
            string = char
        elif char == left:
            level += 1
        elif char == right:
            level -= 1
            if level == 0:
                return index
    raise ValueError('源码括号不成对')


def split_types(text: str) -> list[str]:
    """按逗号分割 text 参数/泛型，保留注解、泛型和数组内部的逗号。"""
    result: list[str] = []
    levels = 0
    start = 0
    quote = False
    for i, char in enumerate(text):
        if char == '"' and (i == 0 or text[i - 1] != '\\'):
            quote = not quote
        if quote:
            continue
        if char in '(<[{':
            levels += 1
        elif char in ')>]}':
            levels -= 1
        elif char == ',' and levels == 0:
            result.append(text[start:i].strip())
            start = i + 1
    if text[start:].strip():
        result.append(text[start:].strip())
    return result


def note(raw: str) -> str:
    """清理 raw 源码注释为可阅读的业务说明，保留中文含义。"""
    return re.sub(r'\s+', ' ', re.sub(r'/\*\*?|\*/|//|^\s*\*', '', raw, flags=re.M)).strip()[:800]


@dataclass
class TypeSource:
    """源码类型索引；name 为类型名，path/text 保存声明，language 决定解析规则。"""
    name: str
    path: Path
    text: str
    language: str
    parent: str = ''


@dataclass
class SourceIndex:
    """参考工程的类型注册表；roots 为工程根目录，types 为 Java/Go 声明索引。"""
    roots: dict[str, Path]
    types: dict[str, TypeSource] = field(default_factory=dict)
    ambiguous: set[str] = field(default_factory=set)

    def register(self, key: str, source: TypeSource) -> None:
        """登记 key 对应 source，同名冲突明确标为未解析，不能选择最后扫描到的定义。"""
        if key in self.types and self.types[key].path != source.path:
            self.ambiguous.add(key)
        self.types[key] = source

    def location(self, path: Path, text: str, offset: int = 0) -> dict[str, Any]:
        """用 path/text/offset 返回工程名、相对路径和一基行号。"""
        root_name, root = next((name, root) for name, root in self.roots.items() if path.is_relative_to(root))
        return {'project': root_name, 'file': path.relative_to(root).as_posix(), 'line': text[:offset].count('\n') + 1}

    def load(self) -> None:
        """扫描根目录内的业务类型，跳过构建目录与依赖；不执行源码。"""
        for project, root in self.roots.items():
            suffix = '*.java' if project == 'bi-docker' else '*.go'
            for path in sorted(root.rglob(suffix)):
                if {'target', 'vendor', 'runtime', '.git'} & set(path.parts):
                    continue
                raw = path.read_text(errors='replace')
                text = clean_comments(raw)
                if project == 'bi-docker':
                    match = re.search(r'\b(?:class|enum|interface)\s+(\w+)(?:\s+extends\s+(\w+))?', text)
                    if match:
                        name = match[1]
                        self.register('java:' + name, TypeSource(name, path, raw, 'java', match[2] or ''))
                else:
                    for match in re.finditer(r'\btype\s+(\w+)\s+struct\s*\{', text):
                        begin = text.index('{', match.start())
                        end = closing(text, begin)
                        source = TypeSource(match[1], path, raw[begin + 1:end], 'go')
                        self.register('go:' + match[1], source)
                        package = re.search(r'\bpackage\s+(\w+)', text)[1]
                        self.register('go:' + package + '.' + match[1], source)

    def schema(self, typename: str, language: str, depth: int = 0, seen: tuple[str, ...] = ()) -> dict[str, Any]:
        """将 typename 转为 Schema；language 为源码语言，depth/seen 限制递归并明确未解析边界。"""
        typename = typename.strip().replace('...', '[]')
        nullable = typename.startswith('*')
        typename = typename.lstrip('*')
        simple = typename.rsplit('.', 1)[-1]
        if typename.endswith('[]') or typename.startswith('[]'):
            child = typename[2:] if typename.startswith('[]') else typename[:-2]
            return {'type': 'array', 'items': self.schema(child, language, depth + 1, seen)}
        generic = re.match(r'(\w+)\s*<(.*)>$', typename)
        if generic:
            name, args = generic[1], split_types(generic[2])
            if name in ('List', 'Set', 'Collection', 'ArrayList', 'Page'):
                return {'type': 'array', 'items': self.schema(args[0], language, depth + 1, seen)}
            if name in ('Map', 'HashMap', 'LinkedHashMap'):
                return {'type': 'object', 'additionalProperties': self.schema(args[-1], language, depth + 1, seen)}
            return {'x-source-type': typename, 'x-unresolved': '泛型包装，查看返回结构说明'}
        if typename.startswith('map['):
            return {'type': 'object', 'additionalProperties': self.schema(typename.split(']', 1)[1], language, depth + 1, seen)}
        primitives = {'string': 'string', 'String': 'string', 'char': 'string', 'Character': 'string', 'int': 'integer', 'long': 'integer', 'Integer': 'integer', 'Long': 'integer', 'Short': 'integer', 'short': 'integer', 'byte': 'integer', 'Byte': 'integer', 'double': 'number', 'float': 'number', 'Double': 'number', 'Float': 'number', 'BigDecimal': 'number', 'bool': 'boolean', 'boolean': 'boolean', 'Boolean': 'boolean'}
        for size in (8, 16, 32, 64):
            primitives.update({f'int{size}': 'integer', f'uint{size}': 'integer', f'float{size}': 'number'})
        if simple in primitives:
            kind = primitives[simple]
            return {'type': [kind, 'null'] if nullable else kind}
        if simple in ('Date', 'LocalDate', 'LocalDateTime', 'Time'):
            return {'type': 'string', 'description': '日期格式按调用页面/后端约定，不能推测时区'}
        if simple in ('any', 'Object', 'JSONObject', 'interface{}'):
            return {'x-source-type': typename, 'x-unresolved': '动态 JSON，参数形状需查调用页面'}
        qualified = language + ':' + typename
        key = qualified if qualified in self.types else language + ':' + simple
        source = self.types.get(key)
        if source is None or key in self.ambiguous or depth >= 6 or key in seen:
            return {'x-source-type': typename, 'x-unresolved': '类型未解析或递归；按源码位置查完整定义'}
        result: dict[str, Any] = {'type': 'object', 'properties': {}, 'x-source-type': typename, 'x-source': self.location(source.path, source.path.read_text())}
        properties = result['properties']
        required: list[str] = []
        if source.parent:
            properties.update(self.schema(source.parent, language, depth + 1, (*seen, key)).get('properties', {}))
        if language == 'java':
            # 只处理字段声明，不将 getter、局部变量、初始化对象内容误作为参数。
            clean = clean_comments(source.text)
            brace_depth = 0
            last_end = 0
            for match in re.finditer(r'\b(?:private|protected|public)\s+(?!static\b|final\b)([\w.$<>?, \[\]]+)\s+(\w+)\s*(?:=[^;]*)?;', clean):
                segment = clean[last_end:match.start()]
                brace_depth += segment.count('{') - segment.count('}')
                # 顶层类型字段所在大括号层数为一。
                last_end = match.start()
                if brace_depth != 1 or '(' in match[1]:
                    continue
                propschema = self.schema(match[1], language, depth + 1, (*seen, key))
                before = source.text[max(0, match.start() - 500):match.start()]
                comments = list(re.finditer(r'/\*[\s\S]*?\*/|//[^\n]*', before))
                if comments:
                    propschema['description'] = note(comments[-1][0])
                if re.search(r'@(NotNull|NotBlank|NotEmpty)\b', before[before.rfind(';') + 1:]):
                    required.append(match[2])
                properties[match[2]] = propschema
        else:
            for line in source.text.splitlines():
                match = re.match(r'\s*(\w+)\s+(\S+)\s*(?:`([^`]*)`)?\s*(?://(.*))?$', line)
                if not match or match[1][0].islower():
                    continue
                name, kind, tags, comment = match.groups()
                tags = tags or ''
                wire = re.search(r'(?:json|form):"([^",]+)', tags)
                if wire and wire[1] == '-':
                    continue
                name = wire[1] if wire else name
                propschema = self.schema(kind, language, depth + 1, (*seen, key))
                if comment:
                    propschema['description'] = comment.strip()
                if re.search(r'(?:binding|validate):"[^"]*required|valid:"[^"]*Required', tags):
                    required.append(name)
                properties[name] = propschema
        if required:
            result['required'] = sorted(set(required))
        if not properties:
            return {'x-source-type': typename, 'x-source': result['x-source'], 'x-unresolved': '枚举/类型没有可提取字段'}
        return result


def mapping_values(arguments: str) -> list[str]:
    """读取 Spring 映射 arguments 的 value/path 字符串，忽略 consumes 等属性。"""
    explicit = re.search(r'\b(?:value|path)\s*=\s*(\{[^}]*\}|"[^"]*")', arguments)
    selected = explicit[1] if explicit else arguments.split(',')[0].strip()
    return re.findall(r'"([^"]*)"', selected) or ['']


def java_endpoints(index: SourceIndex) -> list[dict[str, Any]]:
    """从 index 的 Java 工程提取活动 Controller 映射、参数和响应声明。"""
    root = index.roots['bi-docker']
    results: list[dict[str, Any]] = []
    for path in sorted(root.rglob('*Controller.java')):
        if 'target' in path.parts:
            continue
        raw = path.read_text(errors='replace')
        text = clean_comments(raw)
        class_match = re.search(r'\bclass\s+(\w+)', text)
        if not class_match or '@RestController' not in text and '@Controller' not in text:
            continue
        class_start = text.index('{', class_match.end())
        prefix_match = re.search(r'@RequestMapping\s*\(', text[:class_match.start()])
        prefixes = ['']
        if prefix_match:
            begin = text.index('(', prefix_match.start())
            end = closing(text, begin, '(', ')')
            prefixes = mapping_values(text[begin + 1:end])
        for match in re.finditer(r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(', text[class_start:]):
            offset = class_start + match.start()
            begin = text.index('(', offset)
            end = closing(text, begin, '(', ')')
            mapping_args = text[begin + 1:end]
            method_name = match[1].removesuffix('Mapping').upper()
            methods = re.findall(r'RequestMethod\.(\w+)', mapping_args) if method_name == 'REQUEST' else [method_name]
            methods = methods or ['ANY']
            signature = re.search(r'\bpublic\s+(?:static\s+)?([\w<>?, .\[\]]+?)\s+(\w+)\s*\(', text[end:])
            if signature is None:
                continue
            signature_start = end + signature.start()
            param_start = end + signature.end() - 1
            param_end = closing(text, param_start, '(', ')')
            query: dict[str, Any] = {'type': 'object', 'properties': {}}
            body: dict[str, Any] | None = None
            required: list[str] = []
            headers: list[str] = []
            path_params: dict[str, Any] = {'type': 'object', 'properties': {}}
            encoding = 'json'
            for param in split_types(text[param_start + 1:param_end]):
                annotation = param
                plain = re.sub(r'@\w+(?:\([^)]*\))?\s*', '', param).replace('final ', '').strip()
                pm = re.match(r'(.+?)\s+(\w+)$', plain)
                if not pm or '@LoginAccount' in annotation or pm[1] in ('HttpServletRequest', 'HttpServletResponse', 'Model', 'BindingResult'):
                    continue
                typename, name = pm[1], pm[2]
                ps = index.schema(typename, 'java')
                if 'MultipartFile' in typename:
                    encoding = 'multipart'
                desc = re.search(r'@ApiParam\((.*?)\)', annotation)
                if desc:
                    words = re.findall(r'"([^"]+)"', desc[1])
                    if words:
                        ps['description'] = words[0]
                anno = re.search(r'@(RequestParam|PathVariable|RequestHeader)\s*(?:\((.*?)\))?', annotation)
                if anno:
                    value = re.search(r'(?:\b(?:value|name)\s*=\s*)?"([^"]+)"', anno[2] or '')
                    name = value[1] if value else name
                if '@RequestHeader' in annotation:
                    headers.append(name)
                elif '@RequestBody' in annotation:
                    body = ps
                elif '@PathVariable' in annotation:
                    path_params['properties'][name] = ps
                elif ps.get('type') == 'object' and not anno:
                    query['properties'].update(ps.get('properties', {}))
                    required.extend(ps.get('required', []))
                else:
                    query['properties'][name] = ps
                    if anno and anno[1] == 'RequestParam' and 'required = false' not in annotation and 'required=false' not in annotation and 'defaultValue' not in annotation:
                        required.append(name)
                    default = re.search(r'defaultValue\s*=\s*"([^"]+)"', annotation)
                    if default:
                        value: Any = default[1]
                        if ps.get('type') == 'integer' and value.lstrip('-').isdigit():
                            value = int(value)
                        elif ps.get('type') == 'boolean':
                            value = value == 'true'
                        ps['default'] = value
            if required:
                query['required'] = sorted(set(required))
            before = raw[max(class_start, offset - 600):offset]
            operation = re.findall(r'@ApiOperation\s*\((?:value\s*=\s*)?"([^"]+)"', before)
            description = operation[-1] if operation else signature[2]
            for prefix in prefixes:
                for route in mapping_values(mapping_args):
                    route = '/' + '/'.join(part.strip('/') for part in (prefix, route) if part.strip('/'))
                    for method in methods:
                        results.append({'service': 'bi', 'path': route, 'method': method, 'description': description, 'backend_sources': [index.location(path, raw, offset)], 'handler': signature[2], 'query_schema': query, 'body_schema': body, 'path_schema': path_params, 'encoding': encoding, 'backend_response_type': signature[1].strip(), 'backend_response_schema': index.schema(signature[1].strip(), 'java'), 'backend_headers': headers})
    return results


def go_endpoints(index: SourceIndex) -> list[dict[str, Any]]:
    """提取 index 的 Gin 分组路由和 handler 中的参数；分组路径以 /rule 为服务根。"""
    root = index.roots['rule']
    handlers: dict[str, tuple[Path, str, int, str]] = {}
    for path in sorted((root / 'router').rglob('*.go')):
        raw = path.read_text()
        clean = clean_comments(raw)
        package = re.search(r'package\s+(\w+)', clean)[1]
        for match in re.finditer(r'\bfunc\s+(\w+)\s*\([^)]*\)\s*\{', clean):
            begin = clean.index('{', match.start())
            end = closing(clean, begin)
            handlers[package + '.' + match[1]] = (path, raw, match.start(), clean[begin + 1:end])
    results: list[dict[str, Any]] = []
    for path in sorted((root / 'router').rglob('*.go')):
        raw = path.read_text()
        text = clean_comments(raw)
        groups: dict[str, str] = {'router': '', 'r': ''}
        for offset, line in enumerate(text.splitlines()):
            group = re.search(r'(\w+)\s*:?=\s*(\w+)\.Group\(\s*(?:groupPath\(\s*)?"([^"]+)"', line)
            if group:
                name, parent, part = group.groups()
                base = '/rule' if 'groupPath(' in line else groups.get(parent, '')
                groups[name] = base.rstrip('/') + '/' + part.strip('/')
            route = re.search(r'(\w+)\.(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|Any)\(\s*"([^"]+)"\s*,\s*([\w.]+)', line)
            if not route:
                continue
            parent, method, part, handler = route.groups()
            route_path = groups.get(parent, '') + '/' + part.lstrip('/')
            hkey = handler if '.' in handler else 'router.' + handler
            query: dict[str, Any] = {'type': 'object', 'properties': {}}
            body: dict[str, Any] | None = None
            sources = [{'project': 'rule', 'file': path.relative_to(root).as_posix(), 'line': offset + 1}]
            description = handler
            if hkey in handlers:
                hp, hraw, hpos, block = handlers[hkey]
                sources.append(index.location(hp, hraw, hpos))
                before = hraw[max(0, hpos - 300):hpos]
                comments = re.findall(r'//([^\n]*)', before)
                description = comments[-1].strip() if comments else handler
                query_names = re.findall(r'\.(?:GetQuery|Query|DefaultQuery|QueryArray)\(\s*"([^"]+)"', block)
                query_names.extend(re.findall(r'\.Query\(\)\.Get\(\s*"([^"]+)"', block))
                for name in query_names:
                    query['properties'][name] = {'x-unresolved': 'Gin 查询字符串，按业务转换为数字/字符串', 'x-source-type': 'query'}
                # Gin 以 form tag 绑定 GET，以 JSON tag 绑定 JSON POST。
                declarations = dict(re.findall(r'\b(\w+)\s+([\w.]+)\s*(?:\n|\))', block))
                declarations.update(dict(re.findall(r'\b(\w+)\s*:=\s*&([\w.]+)\s*\{', block)))
                bound_names = re.findall(r'(?:BindAndValid|ShouldBind(?:JSON|Query)?|BindJSON|BindAndShouldBind(?:Json|JSON)?)\([^\n]*?(?:&|,\s*)(\w+)\s*\)', block)
                for bound_name in bound_names:
                    typename = declarations.get(bound_name)
                    if not typename:
                        continue
                    ps = index.schema(typename, 'go')
                    # 业务显式的空值检查同时作为必填约束，保留 Go tag 与字段名的对应关系。
                    zero_checks = []
                    for condition in re.finditer(r'\bif\s+([^{}]+)\{', block):
                        begin = block.index('{', condition.start())
                        branch = block[begin + 1:closing(block, begin)]
                        if 'return' in branch and ('.Response' in branch or 'InvalidParams' in branch):
                            zero_checks.extend(re.findall(r'\b' + re.escape(bound_name) + r'\.(\w+)\s*(?:==\s*(?:0|"")|<=\s*0)', condition[1]))
                    source_type = index.types.get('go:' + typename) or index.types.get('go:' + typename.rsplit('.', 1)[-1])
                    for checked in zero_checks:
                        wire = re.search(r'\b' + checked + r'\s+\S+\s+`[^`]*(?:json|form):"([^",]+)', source_type.text) if source_type else None
                        wire_name = wire[1] if wire else checked
                        ps['required'] = sorted(set([*ps.get('required', []), wire_name]))
                    if method == 'GET':
                        query['properties'].update(ps.get('properties', {}))
                        query.setdefault('required', []).extend(ps.get('required', []))
                    else:
                        body = ps
                for name in query['properties']:
                    variable = re.search(r'(\w+)\s*(?:,\s*_\s*)?:?=\s*[\w.]+\.(?:GetQuery|Query\(\)\.Get)\("' + re.escape(name) + '"\)', block)
                    if variable and re.search(r'\b' + variable[1] + r'\s*==\s*""', block):
                        query.setdefault('required', []).append(name)
                if query.get('required'):
                    query['required'] = sorted(set(query['required']))
            native = route_path.removeprefix('/rule') if route_path.startswith('/rule/') else route_path
            gateway = None
            if native.startswith('/portal/experiment'):
                gateway = native.replace('/portal/experiment', '/portal/ab/experiment', 1)
            elif native.startswith('/portal/params'):
                gateway = native.replace('/portal/params', '/portal/rule/params', 1)
            elif native.startswith('/portal/configDistributionRule'):
                gateway = native
            results.append({'service': 'rule', 'path': native, 'gateway_path': gateway, 'method': method.upper(), 'description': description, 'backend_sources': sources, 'handler': handler, 'query_schema': query, 'body_schema': body, 'path_schema': {'type': 'object', 'properties': {}}, 'encoding': 'json', 'backend_response_type': 'e.Response {code,msg,data,trace,timeZone}', 'backend_headers': ['seLoginUserId', 'tenantId'], 'backend_response_schema': {'type': 'object', 'properties': {'code': {'type': 'integer'}, 'msg': {'type': 'string'}, 'data': {}, 'trace': {'type': 'string'}, 'timeZone': {'type': 'string'}}}})
    return results


def classify(endpoint: dict[str, Any]) -> tuple[str, str]:
    """依据 endpoint 的路径/业务含义分类，GET 不自动等于查询；未知语义按修改入口处理。"""
    path = endpoint['path'].lower()
    name = path.rsplit('/', 1)[-1]
    internal_controllers = ('TestController.java', 'RefreshDataController.java', 'AuthController.java', 'ApiDoController.java', 'NoLoginController.java', 'NoLoginCdpAudienceConfigController.java')
    if any(source['file'].endswith(internal_controllers) for source in endpoint.get('backend_sources', [])):
        return 'internal', '测试、维护、认证或服务间调用 Controller，非 Agent 业务入口'
    if endpoint['service'] == 'rule' and not endpoint.get('gateway_path'):
        return 'internal', '内部 SDK、回调或运维接口，无 Portal 业务代理'
    if any(part in path for part in ('/test/', '/health/', '/nologin/', '/refreshdata', '/auth/', '/apido', '/ab/report/', 'notify', 'callback', '/cdpaudienceconfig')):
        return 'internal', '测试、免登录、服务间调用或维护接口'
    if endpoint['method'] not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
        return 'unverified', '未确定 HTTP 方法或非业务方法'
    if endpoint['encoding'] == 'multipart':
        return 'special', '文件上传契约，需通过上传页面提供文件；当前工具不接受任意文件路径'
    if any(part in path for part in ('/download', '/export/', 'getfileuploadtemplate')):
        return 'special', '下载或导出协议，当前工具只接收 JSON；目录保留接口说明'
    write = ('add', 'save', 'create', 'upd', 'edit', 'modify', 'delete', 'del', 'remove', 'setonline', 'setoffline', 'online', 'offline', 'pushout', 'setshow', 'setdefault', 'setaudience', 'temp', 'cache', 'sync', 'ignore', 'refresh', 'initt', 'initrule', 'clear', 'cancel', 'open', 'clean')
    if name.endswith('check') or name.endswith('verify') or name.startswith(('check', 'find', 'get', 'list', 'query', 'detail', 'select', 'verify', 'conflict')):
        # check/verify 明确为前置检查；其余包含 write 前缀的动作不允许进查询工具。
        return 'read', ''
    if name.startswith(write) or endpoint['method'] in ('PUT', 'PATCH', 'DELETE'):
        return 'write', ''
    read = ('analysis', 'indsummary', 'inddetailbyday', 'retention', 'samplecomputer', 'basicinfo', 'bodylist', 'metriclist', 'report', 'tagresult', 'industrytag', 'usertaglist', 'entergroupsql', 'dimension', 'currenttime', 'status')
    if any(part in name for part in read) or name.endswith(('list', 'detail', 'info')):
        return 'read', ''
    return 'write', '源码未明确证明只读，使用修改入口；需核实业务意图'


def module(endpoint: dict[str, Any]) -> str:
    """按 endpoint 路径选择 Skill 参考模块。"""
    path = endpoint['path'].lower()
    if endpoint['service'] == 'rule':
        if '/experiment' in path:
            return 'ab-testing'
        return 'rule-config'
    if any(word in path for word in ('/report/', '/analysis/')):
        return 'analysis'
    if any(word in path for word in ('board', 'reportform', 'grouptemplate')):
        return 'reports-boards'
    if 'usertag' in path or 'usergroup' in path or 'audience' in path:
        return 'audiences-tags'
    if any(word in path for word in ('event', 'profile', 'analysisbody', 'dimension', 'arith', 'collect', 'buried', 'debug', 'hotprofile')):
        return 'metadata'
    return 'utilities-internal'


def normalize_front(path: str) -> tuple[str, str] | None:
    """将前端 path 转为 BI/Rule 相对路径；只接受目标服务常量。"""
    if path.startswith('/bi-docker/api/'):
        return 'bi', path.removeprefix('/bi-docker/api')
    for prefix, native in (('/portal/ab/experiment', '/portal/experiment'), ('/portal/rule/params', '/portal/params'), ('/portal/configDistributionRule', '/portal/configDistributionRule')):
        if path.startswith(prefix):
            return 'rule', native + path.removeprefix(prefix)
    return None


def build(frontend: Path, bidocker: Path, rule: Path, contracts: Path, target: Path) -> None:
    """读取 frontend/bidocker/rule 与 contracts，向 target 生成目录及逐接口参考，不调用线上接口。"""
    index = SourceIndex({'bi-docker': bidocker, 'rule': rule})
    index.load()
    endpoints = java_endpoints(index) + go_endpoints(index)
    registry: dict[tuple[str, str, str], dict[str, Any]] = {}
    for endpoint in endpoints:
        key = endpoint['service'], endpoint['path'], endpoint['method']
        if key in registry:
            registry[key]['backend_sources'].extend(endpoint['backend_sources'])
        else:
            registry[key] = endpoint
    front = json.loads(contracts.read_text())
    matched_refs: set[str] = set()
    for call in front['calls']:
        normalized = normalize_front(call['path'])
        if normalized is None:
            continue
        service, route = normalized
        key = service, route, call['method']
        entry = registry.get(key)
        if entry is None:
            entry = {'service': service, 'path': route, 'method': call['method'], 'description': call['description'] or call['reference'], 'backend_sources': [], 'query_schema': {'type': 'object', 'properties': {}}, 'body_schema': None, 'path_schema': {'type': 'object', 'properties': {}}, 'encoding': 'json'}
            registry[key] = entry
        entry.setdefault('frontend_calls', []).append(call)
        entry.setdefault('frontend_paths', []).append(call['path'])
        matched_refs.add(call['reference'])
        if not entry['description'] or entry['description'] == entry.get('handler'):
            entry['description'] = call['description'] or entry['description']
        input_schema = call['input_schema']
        if call.get('wire_mode') == 'query_body':
            for name, schema in call['frontend_query_schema'].get('properties', {}).items():
                entry['query_schema']['properties'].setdefault(name, schema)
            if entry['body_schema'] is None:
                entry['body_schema'] = call.get('frontend_body_schema')
            input_schema = call.get('frontend_body_schema') or {}
        elif call.get('wire_mode') == 'binary':
            entry['encoding'] = 'multipart'
        if input_schema.get('type') == 'object':
            if entry['method'] == 'GET':
                for name, schema in input_schema.get('properties', {}).items():
                    if name not in entry['query_schema']['properties'] or 'x-unresolved' in entry['query_schema']['properties'][name]:
                        entry['query_schema']['properties'][name] = schema
            elif (entry['body_schema'] is None and not entry['backend_sources']) or 'x-unresolved' in (entry['body_schema'] or {}):
                entry['body_schema'] = input_schema
        if service == 'rule':
            entry['gateway_path'] = call['path']
    # 未被前端调用的 URL 仍保留，避免丢失废弃接口或路由差异。
    unused = []
    for url in front['urls']:
        normalized = normalize_front(url['path'])
        if normalized and url['reference'] not in matched_refs:
            unused.append(url)
    result = []
    for key, entry in sorted(registry.items()):
        entry['frontend_paths'] = sorted(set(entry.get('frontend_paths', [])))
        entry['match_status'] = 'matched' if entry['backend_sources'] and entry.get('frontend_calls') else 'backend_only' if entry['backend_sources'] else 'frontend_only'
        operation, reason = classify(entry)
        if entry['match_status'] == 'frontend_only':
            operation, reason = 'unverified', '前端有调用，本地后端无同方法/同路径声明；不可假定部署版本支持'
        entry['operation'], entry['unavailable_reason'] = operation, reason
        entry['module'] = module(entry)
        digest = hashlib.sha256((' '.join(key)).encode()).hexdigest()[:8]
        friendly = re.sub(r'[^a-zA-Z0-9]+', '_', entry['path']).strip('_')
        entry['id'] = f"{entry['service']}.{entry['method'].lower()}.{friendly}.{digest}"
        for schema_name in ('query_schema', 'path_schema'):
            schema = entry[schema_name]
            schema['additionalProperties'] = False
        for name in ('pageSize', 'pageNum'):
            prop = entry['query_schema']['properties'].get(name)
            if prop and prop.get('type') in ('integer', 'number'):
                prop['minimum'] = 1
                prop['default'] = 50 if name == 'pageSize' else 1
                if name == 'pageSize':
                    prop['maximum'] = 200
        # 请求体结构允许保留前端新增字段；未解析并不表示字段已被完整校验。
        entry['schema_status'] = 'partial' if 'x-unresolved' in json.dumps([entry['query_schema'], entry['body_schema']], ensure_ascii=False) else 'declared'
        result.append(entry)
    revisions = {}
    for name, root in (('solar-engine-fe', frontend), ('bi-docker', bidocker), ('rule', rule)):
        revision = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], capture_output=True, text=True)
        revisions[name] = revision.stdout.strip() if revision.returncode == 0 else 'not-git'
    summary = {'endpoints': len(result), 'frontend_url_constants': len(front['urls']), 'frontend_http_calls': len(front['calls']), 'unused_target_urls': len(unused), 'unresolved_frontend_calls': len(front.get('unresolved_calls', []))}
    for field_name in ('service', 'match_status', 'operation'):
        summary[field_name] = {name: sum(e[field_name] == name for e in result) for name in sorted({e[field_name] for e in result})}
    target.mkdir(parents=True, exist_ok=True)
    # 目录版本跟随插件声明，重新生成时不会把新版本退回硬编码的旧版本。
    package_version = json.loads((target.parent.parent / 'manifest.json').read_text())['version']
    catalog = {'version': package_version, 'source_revisions': revisions, 'summary': summary, 'endpoints': result, 'unused_frontend_urls': unused, 'unresolved_frontend_calls': front.get('unresolved_calls', []), 'notes': ['目录是本地源码声明快照，不代表所有接口已在线上验证。', '未被本地后端声明匹配的接口不可执行；内部、上传下载接口供参考。', 'x-unresolved 明确表示动态、递归或无法提取的字段，需进一步查阅源码。']}
    (target / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    references = target.parent.parent / 'references'
    references.mkdir(parents=True, exist_ok=True)
    for module_name in sorted({e['module'] for e in result}):
        lines = [f'# {module_name} 接口参考', '', '自动对照前后端源码生成。目录状态不等于线上验证；调用前使用 `SolarCatalog` 的 describe 获取完整契约。', '', '| 接口 ID | 方法与路径 | 用途 | 状态 / 操作 |', '|---|---|---|---|']
        module_entries = [e for e in result if e['module'] == module_name]
        for e in module_entries:
            lines.append(f"| `{e['id']}` | {e['method']} {e['path']} | {e['description'].replace('|', '/').replace(chr(10), ' ')} | {e['match_status']} / {e['operation']} |")
        api_dir = references / 'api'
        api_dir.mkdir(exist_ok=True)
        lines.extend(['', '## 使用方式', '', '每个接口的参数、返回声明及源码位置见 `references/api/<接口ID>.md`，或调用 SolarCatalog.describe。先检索再读取单个契约，不应一次读取所有接口。'])
        for e in module_entries:
            detail = [f"# {e['id']}", '', e['description'], '', f"- 服务：{e['service']}；后端相对路径：`{e['path']}`；方法：{e['method']}。", f"- 前端路径：{', '.join(e['frontend_paths']) or '未发现前端调用'}。", f"- 状态：{e['match_status']}；操作：{e['operation']}；Schema：{e['schema_status']}。"]
            if e['unavailable_reason']:
                detail.append('- 说明：' + e['unavailable_reason'])
            for source in e['backend_sources']:
                detail.append(f"- 后端源码：{source['project']}/{source['file']}:{source['line']}。")
            for call in e.get('frontend_calls', []):
                detail.append(f"- 前端源码：solar-engine-fe/{call['source']['file']}:{call['source']['line']}；方法 {call['function']}；参数类型 `{call['input_type']}`。")
            detail.extend(['', '请求参数（query / body / path）：', '', '```json', json.dumps({name: e[name] for name in ('query_schema', 'body_schema', 'path_schema')}, ensure_ascii=False, indent=2), '```', '', '返回声明：', '', '```json', json.dumps({'backend_type': e.get('backend_response_type', '未匹配'), 'backend_schema': e.get('backend_response_schema'), 'frontend_schemas': [c['response_schema'] for c in e.get('frontend_calls', [])]}, ensure_ascii=False, indent=2), '```'])
            (api_dir / (e['id'] + '.md')).write_text('\n'.join(detail) + '\n')
        (references / (module_name + '-api.md')).write_text('\n'.join(lines) + '\n')
    lines = ['# 接口覆盖与差异', '', '```json', json.dumps(summary, ensure_ascii=False, indent=2), '```', '', '前端存在、后端缺失的契约和未使用 URL 均保留，不能凭 URL 名称推测可调用性。', '', '## 未使用的前端 URL 常量', '', '| 常量 | 路径 | 源码 |', '|---|---|---|']
    for url in unused:
        lines.append(f"| {url['reference']} | {url['path']} | {url['source']['file']}:{url['source']['line']} |")
    lines.extend(['', '## 动态路径或未解析的前端调用', '', '以下调用保留源码位置；运行时拼接的路径不会被猜测成新的可执行接口。目标服务由固定 URL 目录及后端路由对照确认。', '', '| 方法 | 表达式 | 源码 |', '|---|---|---|'])
    for call in front.get('unresolved_calls', []):
        lines.append(f"| {call['method']} | {call['expression'].replace('|', '/')} | {call['source']['file']}:{call['source']['line']} |")
    (references / 'coverage.md').write_text('\n'.join(lines) + '\n')
    manifest_path = target.parent.parent / 'manifest.json'
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        manifest['skill_files'] = ['SKILL.md', *[path.relative_to(target.parent.parent).as_posix() for path in sorted(references.rglob('*.md'))]]
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False))


def main() -> None:
    """解析参考工程路径和生成位置，调用可重复生成流程。"""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('frontend', 'bidocker', 'rule', 'frontend-contracts'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--target', type=Path, default=Path('backend/plugins/bi_metadata/executor/solar_api'))
    args = parser.parse_args()
    build(args.frontend, args.bidocker, args.rule, args.frontend_contracts, args.target)


if __name__ == '__main__':
    main()
