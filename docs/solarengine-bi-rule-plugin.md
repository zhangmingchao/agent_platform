# SolarEngine BI / Rule 插件与 Skill

## 实现方案（work_list）

用户确认后实施：从 solar-engine-fe 的 URL 与实际调用、Java BI Controller/DTO、Go Rule Router/DTO 建立接口目录；用 Portal 代理核对 AB 与参数管理路径。扩展现有 bi-metadata 插件，包含目录检索、只读业务请求和独立修改入口，继续复用用户 Runtime Docker，不需要 MCP Server。

当天执行记录在 [2026-10-25.md](../work_list/2026-10-25.md)。

## 使用方式

插件稳定 ID 为 `bi-metadata`，新版 `2.0.1` 显示为“SolarEngine BI 分析与 AB 测试”。原有 BiCli 工具和连接测试继续可用；工具调试使用通用 JSON 面板，以支持五个工具。

安装新版后切换到 2.0.1，保存配置、启用并关联 Agent。已有旧版本继续保留，可以回切；不修改参考项目或执行生产业务写入。

| 配置 | 含义 |
|---|---|
| base_url | BI API 根地址，包含完整 `/portal-api/bi-docker/api` context-path |
| token | BI 登录 Token；加密保存，不进入模型参数或安装包 |
| portal_base_url | Portal 网关根地址，通常为 `https://your-domain/portal-api`，用于 Rule / AB 测试 |
| rule_token | 可选独立登录 Token；为空时复用 BI Token |
| allow_mutations | 默认 false，开启后仍受 Agent 高风险工具权限控制 |
| timeout_seconds / max_output_bytes | 单次请求超时和响应限制 |

不要直连内部 Rule 服务来绕过 Portal 的登录与产品权限。Portal 会从登录 Token 和产品配置获取用户/租户，插件不接受模型指定 tenantId 或 seLoginUserId 请求头。

## 工具职责

| 工具 | 职责 |
|---|---|
| BiCli | 五类元数据列表命令，保留旧用法 |
| SolarCatalog | 固定目录分页检索与单接口契约详情，不访问线上 |
| SolarQuery | 目录中的 read 接口，包括 POST 行为分析和实验报告 |
| SolarMutate | 目录中的 write 接口，high 风险；明确业务指令、配置开关和平台权限共同决定可执行性 |

Skill 使用 `{{tool:名称}}`，平台安装后替换成真实命名空间工具名。独立 Skill ZIP 已替换为 `plugin__bi_metadata__...`，使用它仍须安装并绑定本插件；仅导入 Skill 不会创建执行工具。

## 接口覆盖与边界

完整统计见包内 `references/coverage.md` 和 `executor/solar_api/catalog.json`。目录覆盖本地活动 Spring Controller 映射、Gin Router 声明，以及目标服务的前端 URL 常量/调用；废弃注释中的路由不计入活动接口。

- matched：前端和本地后端方法、路径匹配。
- backend_only：后端声明存在，未发现对应前端调用。
- frontend_only / unverified：前端调用存在但本地后端不匹配，或方法尚未明确；不直接执行。
- internal：内部 SDK、回调、测试/维护、认证入口，仅供参考。
- special：上传与非 JSON 下载/导出协议，仅供参考。

这是源码契约快照，不能宣称全部接口在线上均已验证。动态拼接 URL 和未解析调用保留源码位置；第三方 pprof/XXL 注册的内部动态路由不会猜测为业务接口。DTO/前端类型中动态 JSON、递归、同名冲突或无法展开的字段以 x-unresolved 标明。执行校验已提取结构，后端仍负责完整业务校验。

前端可能有更新版本的 MaxAgent、错误日志流等接口，本地 BI Controller 不存在相同声明时保留为差异，不能用其他相似接口替代。

## 代码职责与实体

| 文件 | 作用 |
|---|---|
| scripts/solar_frontend_contracts.cjs | TypeScript AST、类型检查器提取 URL、Http/httpGet/httpPost、缓存及混合传参 |
| scripts/build_solar_catalog.py | Java/Go 类型与路由提取、前后端匹配、操作分类、生成完整目录及单接口参考 |
| executor/solar_api/catalog.json | 可分发固定接口身份、请求 Schema、来源和覆盖状态 |
| executor/solar_api/client.py | 实体、目录检索、请求校验、Portal 路由、响应限制和脱敏 |
| executor/main.py | 根据 tool_name 分发一次进程调用，兼容 BiCli |
| manifest.json / requirements.lock | 四工具契约、服务配置、版本、完整 Skill 文件清单和固定依赖 |
| backend/plugins/examples.py | 确定性打包包内客户端和目录，不包含凭据 |
| scripts/export_solar_plugin.py | 输出插件 ZIP 与独立 Skill ZIP，可同步 pre-skill 文档源 |

客户端用 ApiSettings、Endpoint、ApiCall、PreparedCall、CatalogPage、UpstreamResult、ApiFailure、ApiResult 等实体表示配置、契约、请求和结果；动态映射仅存在于 Schema、认证头与业务 JSON 边界。所有客户端参数具有类型，类和方法包含中文职责说明。

## 重新生成和导出

在 agent_platform 根目录运行；参考项目路径由参数明确指定，不写入执行配置。

```bash
node scripts/solar_frontend_contracts.cjs /path/solar-engine-fe /tmp/solar-fe-contracts.json

backend/.venv-langchan/bin/python scripts/build_solar_catalog.py \
  --frontend /path/solar-engine-fe \
  --bidocker /path/bi-docker \
  --rule /path/rule \
  --frontend-contracts /tmp/solar-fe-contracts.json

backend/.venv-langchan/bin/python -m scripts.export_solar_plugin \
  --output dist/plugins --standalone-source pre-skill/bi-metadata
```

生成脚本会同步 manifest 的 skill_files，确保全部参考文件随包分发。变更已发布内容后需增加版本再分发，不能覆盖已安装的同版本不同内容包。执行代码/目录/Skill 一起打包，同一请求固定使用同一激活版本。

## 验证

行为测试覆盖产品身份、数组参数、BI 根路径、Portal 转换、独立 Token、GET 修改隔离、配置开关、复杂 JSON 与 query 分流、认证/404/重定向/超限、结果脱敏、修改不自动重试、源码注释/多 DTO 绑定以及 ZIP 中独立进程调用。

真实环境验证只使用查询。验证结果与交付包路径在当天 work_list 记录。

本次 28 项相关测试通过。375 个接口条目中 BI 304、Rule 71；227 个前后端匹配，16 个仅前端声明，132 个仅后端声明。可执行语义为 read 148 / write 138，其余为内部、特殊传输或未核实接口。

当前用户 Runtime 已安装并激活 2.0.0。目录查询、BI 23 个事件查询、Rule 实验列表和原有连接检测实际通过；Skill/SkillFile 从安装包读取及工具命名空间验证通过。未执行生产修改操作，也未将此验证表述为所有线上接口或大模型完整会话均已测试。


## 2.0.1 事件计数修复

新增 SolarEventCount：产品、事件、日期进入一个固定业务流程，减少模型读取 Skill、搜索目录和手动拼报表的轮次。默认读取产品时区，按服务端时间统计全部应用；支持指定 IANA 时区、实际 appId、客户端时间、最多 31 天日期范围。

实现：`executor/solar_api/event_count.py` 的 EventCountRequest 保存类型化输入，EventCountOutcome 保存统计范围和 count，EventCounter 顺序执行产品时区、事件分类、totalNumber 计算元数据、合计报表四阶段；元数据失败或不唯一则立即停止。日期转为静态自然日，关闭分组、阶段汇总和近似计算；不让模型传入 SQL/funcSqls。每阶段一次请求，总超时 25 秒。

仅解析 `tableData.val` 唯一行的 `event_0`，支持实际单元素数组包装；缺字段、空表、多个汇总行、截断、格式缩写和非整数返回失败。只有明确数值 0 才返回 0；错误 count=null。线上接口 HTTP 200/code500 不代表成功。

通用客户端增加自动 request-id，错误返回固定 endpoint_id/http_status/upstream_code/request_id；不返回任意上游 SQL 或密钥。Skill 主入口路由简单计数问题到 SolarEventCount，失败后结束本轮，不继续手工改接口。其他分析和 AB 流程保留。

边界：插件可改正流程和失败处理，线上报表仍返回通用 code500 时需要上游日志定位；不能把单元测试结果当成线上查询成功。运行验证结果见当天 work_list。


2.0.1 实际 Runtime 验证：产品 `0070db93d7c6c36c` 的 `_appEnd` 在 `2026-10-25` 查询时返回 21,456 条（全部应用、Etc/GMT-8、服务端时间）。该数值是当次实时验证结果，不作为固定示例答案或后续查询缓存。


真实模型验收边界：已使用当前 Agent 配置构建新版工具并发起独立验证，模型接口第一轮返回 403（PermissionDeniedError），尚未进入工具选择。因此当前验证结论是 Runtime 工具完整业务流程成功、Skill 名称与版本匹配；完整模型自动对话尚未通过。此次未修改模型或 Agent 的迭代配置。
