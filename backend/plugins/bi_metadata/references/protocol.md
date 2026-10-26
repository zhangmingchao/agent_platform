# 插件调用协议

## 服务配置与路径

平台字段 `base_url` 是 BI API 根地址，须包含完整 context-path，例如 `https://your-domain/portal-api/bi-docker/api`。目录的 BI path 是 `/eventConfig/findByProductKey` 等相对路径，不重复追加 `/bi-docker/api`。

`portal_base_url` 是 Portal 网关根地址，例如 `https://your-domain/portal-api`。Rule 请求走 `/portal/ab/experiment/...`、`/portal/rule/params/...` 或 `/portal/configDistributionRule/...`。目录同时保留 Rule 原生路径用于源码核对，执行不直接使用内部 `/rule/portal/...` 地址。

路径转换依据 `portal/routers/router/rule_router.go`：AB 前缀映射到 Rule 的 experiment；参数管理映射到 params。Portal 根据登录身份与产品配置补充 `seLoginUserId` 和 `tenantId`，模型不得传入或伪造这些请求头。

`token` 配置为 BI 登录 Token；`rule_token` 可选，留空复用 BI Token。是否能复用由实际环境的身份系统决定。`allow_mutations` 默认 false；启用后修改仍受 Agent 的高风险工具权限控制，插件不自行创建交互审批。

## 请求结构

SolarQuery / SolarMutate 使用以下 JSON 字段：

| 字段 | 类型 | 作用 |
|---|---|---|
| endpoint_id | string | 固定目录中的接口 ID；不能传任意 URL |
| product_key | string | 已确认产品标识，写入 pk 头；不同于 appId |
| query | object | 按 query_schema 提交 URL 参数；数组保持重复同名参数 |
| body | JSON / null | 按 body_schema 提交请求体；没有请求体时为 null |
| path | object | 目录声明的路径占位符参数，通常为空 |
| context | object | 应用选择、语言、时区、系统类型；不是任意 headers |
| change_reason | string | 仅修改工具必填，描述用户要求与目标；不是授权凭证 |

允许的 context：`app_ids`（字符串或整数数组）、`all_apps`（布尔）、`language`（zh/en）、`time_zone`（字符串）、`system_type`（product/app）、`country_region`（字符串）。单应用/多应用和全部应用的选择必须与用户要求一致，不能默认为用户选择全量应用。

目录中 `x-unresolved` 表示动态 JSON、递归、枚举或缺少静态类型，不能宣称字段已经完整校验。`schema_status=declared` 也仅表示已提取声明，不代表通过后端所有业务校验。必填字段来自注解、Go tag 或明确返回错误的空值检查；前后端类型差异按后端契约核对。

## 返回格式

SolarQuery 成功结果示意（仅格式示例，不是实际查询结果）：

```json
{"ok":true,"data":{"endpoint_id":"bi.get.eventConfig_findByProductKey.44438962","service":"bi","http_status":200,"code":200,"data":{"total":1,"list":[{"eventName":"<实际事件标识>","name":"<实际显示名>"}]},"time_zone":null},"error":null}
```

失败结果：

```json
{"ok":false,"data":null,"error":{"code":"NOT_FOUND","message":"接口返回 HTTP 404，请检查服务地址与部署版本；BI 基础地址须包含 /api","retryable":false}}
```

接口返回形状因 endpoint 而异，不把所有返回都当成 `{total,list}`。AB 报告可能返回 `{dataList,...}`；查看源码返回声明和实际数据。返回字段为 null 与缺少字段不同。

## 错误与特殊接口

| 错误 | 处理方式 |
|---|---|
| UNKNOWN_ENDPOINT | 重新检索目录，不猜 ID |
| OPERATION_NOT_ALLOWED | 核对查询/修改入口及可用性；不绕过工具 |
| MUTATION_DISABLED | 请用户在插件配置中允许业务修改，并使用合适 Agent 权限 |
| INVALID_ARGUMENTS | describe 后核对类型、位置、必填项；错误不会回显完整参数值 |
| PRODUCT_MISMATCH | query/body 的产品与 product_key 不一致，纠正身份范围 |
| CONFIGURATION_ERROR | 配置正确 BI/Portal 根地址和 Token |
| NOT_FOUND | HTTP 404，核对服务根路径与部署版本 |
| RESOURCE_NOT_FOUND | 业务 404，查询目标是否存在 |
| UNAUTHENTICATED / PERMISSION_DENIED | 停止重试，处理登录或产品权限 |
| TIMEOUT / NETWORK_ERROR | 查询可谨慎重试；修改先查询状态 |
| OUTPUT_TOO_LARGE | 分页、缩小日期或过滤范围 |
| REDIRECT / INVALID_RESPONSE | 接口地址应返回 JSON，不能使用网站页面地址 |

上传、二进制下载、内部 SDK、回调和运维接口列入目录供追溯，当前 JSON 工具不执行。前端有调用但本地后端未匹配的接口保留为 unverified，不能假定线上存在；需先核对部署源码，再更新目录和插件版本。
