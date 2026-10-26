---
name: bi-metadata
description: 基于 SolarEngine 前端、BI 与 Rule 后端接口，查询元数据、行为分析、报表看板、分群标签、AB 实验与报告，以及按用户明确指令操作配置和实验。
---

# SolarEngine BI 分析与 AB 测试

本 Skill 随 `bi-metadata@2.0.1` 插件安装，执行仍在用户 Runtime Docker。基础地址与 Token 由平台配置并注入；不要让模型生成 Token、任意 URL 或认证请求头。

## 事件数量查询优先入口

用户问某个事件“今天/昨天有多少条、多少次、某日期触发数量”，优先直接调用 `plugin__bi_metadata__SolarEventCount`。
从会话复用已确认 product_key；事件使用原始标识（例如 `_appEnd`）。未指定应用时查询产品全部应用；未指定时区时自动读取产品时区；默认按服务端时间统计，并在答案中说明口径。

```json
{"product_key":"<已确认的产品标识>","event_name":"_appEnd","date":"today"}
```

该工具内部完成元数据获取和参数组装，不需要先 SolarCatalog.search/describe，也不需要 ExecutePython 或手工写 SQL。
成功时读取 `data.count`，同时展示 `data.start_date/end_date/time_zone/time_type`。失败时 count 为 null，说明 `error.stage/code/request_id`，结束本轮统计；不要原样重试或换用通用报表接口尝试同一查询。接口未返回数据不等于 0 条。
用户需要属性过滤、分组、用户去重或复杂指标时使用通用分析流程，不能用总次数代替用户数。具体协议见 [事件总次数](references/event-count.md)。

## 选择工具

- `plugin__bi_metadata__SolarEventCount`：事件总次数业务工具，适用于单日或最多 31 天的日期范围。
- `plugin__bi_metadata__SolarCatalog`：搜索接口或读取完整契约。目录查询不访问线上服务。
- `plugin__bi_metadata__SolarQuery`：调用目录中 `operation=read` 的接口；包含 GET 列表和 POST 分析查询。
- `plugin__bi_metadata__SolarMutate`：调用 `operation=write` 的接口；需要用户明确的业务指令、插件允许修改以及平台工具权限。`change_reason` 只是意图说明，不是授权凭证。
- `plugin__bi_metadata__BiCli`：保留原有五类元数据列表命令，参数格式见 `references/commands.md`。

先判断用户意图，再查接口；不要仅根据 GET/POST 判断操作类型。上线、删除等 GET 接口依然是修改操作。

## 按需读取参考

| 用户意图 | 参考文件 |
|---|---|
| 调用协议、身份、分页、错误与响应 | `references/protocol.md` |
| 完整业务流程与参数模板 | `references/workflows.md` |
| 事件、属性、分析主体、指标、埋点调试 | `references/metadata-api.md` |
| 事件、漏斗、留存、路径、分布、用户属性分析 | `references/analysis-api.md` |
| 报表、看板、全局筛选、协作与模板 | `references/reports-boards-api.md` |
| 分群、用户标签、条件/结果标签 | `references/audiences-tags-api.md` |
| AB 实验、实验层、实验报告与样本计算 | `references/ab-testing-api.md` |
| 参数管理、引用、规则和配置下发 | `references/rule-config-api.md` |
| 工具、内部调用及维护接口 | `references/utilities-internal-api.md` |
| 前后端覆盖、差异与未使用 URL | `references/coverage.md` |

模块文件是索引。单接口参数、返回声明及源码位置在 `references/api/<endpoint_id>.md`，也可用目录工具 describe 获取。不要一次读取全部接口。

## 标准执行步骤

1. 确认产品 `product_key`；需要应用 ID 时确认实际 `appId`，两者不能互相代替。上下文缺少且工具无法获取时询问用户，不能从产品标识推算 ID。
2. 除上述事件总次数查询外，使用 SolarCatalog.search 按服务、关键词和业务模块找到接口，再 describe 获取完整契约。
3. 核对 `operation`、`match_status`、`schema_status`、`query_schema`、`body_schema` 与前端使用方式。`frontend_only`/`unverified` 表示本地后端未核实；`internal`/`special` 仅供参考，不能当成普通业务工具调用。
4. 普通查询使用 SolarQuery。分析查询先取得事件/属性/主体/计算方式，再构造嵌套条件；日期、时区、过滤和统计口径以用户要求及实际返回为准。
5. 修改先查询目标、说明具体变更并按用户指令执行；遵循实验下线、推全、删除实验层等前置检查。失败或超时先确认当前状态，不能直接重复提交。
6. 根据真实工具结果回答，保留指标单位、时区、日期、筛选及分组条件。接口元数据存在不代表某个日期有行为数据；不能猜测事件、属性或实验存在。

## 目录和查询示例

```json
{"action":"search","service":"bi","search":"eventConfig findByProductKey","operation":"read","limit":10}
```

```json
{"action":"describe","endpoint_id":"bi.get.eventConfig_findByProductKey.44438962"}
```

```json
{"endpoint_id":"bi.get.eventConfig_findByProductKey.44438962","product_key":"<product_key>","query":{"pageNum":1,"pageSize":50},"body":null,"path":{},"context":{}}
```

产品占位符必须替换成已确认值；工具会自动填写声明中的 `productKey`，禁止再传入与之不一致的值。

原有 BiCli 示例：

```json
{"arguments":["metadata","events","list","--product-key","app_001","--page-num","1","--page-size","50"]}
```

BiCli 支持 `analysis-bodies`、`events`、`user-properties`、`event-properties`、`metrics` 的 `list` 命令。不要传可执行文件名、Python、Shell、管道或重定向。

优先搜索和分页。目录每页最多 50 条，常见列表每页最多 200 条；各接口分页字段和总数结构可能不同。用户需要全部数据时顺序翻页，检测重复页/空页，不以 `pages=0` 推断没有事件。

业务结果外层 `ok` 表示调用是否成功。SolarQuery/SolarMutate 的业务数据在 `data.data`；目录 search 的列表在 `data.items`，describe 的契约在 `data`。不同工具结果不能按同一种分页结构解释。

失败时读取外层 `error.code`。认证或权限失败停止重试；HTTP 404 检查配置和部署版本，业务 404 表示对象不存在。未知/内部接口失败不要绕过工具改用 Shell/curl。禁止输出 Token、密码和认证请求头。
