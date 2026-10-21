# 插件管理

## 实现方案（work_list）

1. 使用内置 `manifest.json` 声明插件身份、版本、配置字段、工具、权限和技能文件。
2. 按用户保存通用配置，每个密钥独立使用 AES-256-GCM 加密；通过配置版本号防止旧页面覆盖新配置。
3. 根据 capabilities 显示环境导入、连接测试和工具调试，未声明的操作在接口层拒绝。
4. Agent 按需绑定插件，在统一工具工厂中注册工具和可选 Skill，沿用权限执行流水线。
5. 前端按 fields 自动生成控件，无配置插件直接启用；固定执行器适配不同插件的实际行为。

## 首次使用

菜单进入「插件管理」，点击 BI 元数据查询的配置按钮，填写 BI 服务地址与 BI Token，保存配置。
在概览页输入有读取权限的产品标识，点击「测试连接」。测试会真实执行一次第一页、每页一条的事件查询；无需调用大模型。
启用插件后，在 Agent 编辑页的「关联插件」选择 BI 元数据查询并保存。新发起的对话、外部 API 和工作流请求会加载插件。
BI 工具调试支持五类只读元数据查询，可使用专用表单或工具输入 JSON 对象；查询结果仅显示在当前调试界面，不写入插件操作记录。

「JSON 格式处理」是可实际运行的无配置插件，可直接启用。在工具调试中执行预置示例，或提交自己的 JSON 文本，得到校验、格式化或压缩结果；此插件不访问网络，也没有服务地址、Token、环境导入或连接检测。

配置草稿允许留空；启用前按各插件声明验证必填项和执行器约束。BI 插件要求地址和有效可解密凭据。已保存密钥不会回显，输入框留空保留原值；每个密钥都有独立的「清除」选项。
配置变更后连接状态重置为未测试。启用状态与连接检测结果独立，测试失败不会自动停用插件。
停用插件会保留 Agent 绑定，后续请求不再加载其工具及配套 Skill；进行中的请求继续使用已取得的配置快照。移除配置前必须先解除绑定。

## 目录和实体

- `backend/plugins/bi_metadata/manifest.json`：内置 BI 插件声明。
- `backend/plugins/json_tools/manifest.json`：无配置 JSON 插件声明。
- `backend/plugins/registry.py`：固定插件注册表与声明文件白名单，不导入用户指定的 Python 模块。
- `backend/plugins/configuration.py`：通用字段类型、长度、范围、枚举及必填校验。
- `backend/plugins/executors.py`：受信任执行器契约及 BI/JSON 实现，负责插件特定行为。
- `pre-skill/bi-metadata/`：插件配套 Skill 与参考文件。
- `backend/models/plugin.py`：配置输入、公开视图、调试结果、操作记录等强类型接口实体。
- `backend/services/plugin_service.py`：配置事务、用户隔离、健康检测、绑定和运行快照。
- `backend/core/bi_cli_tool.py`：固定模块子进程执行，给每次调用独立注入配置，禁止 Shell。
- `backend/core/plugin_tools.py`：通用工具构建、声明核对、独立配置闭包、脱敏与审计。
- `frontend/src/views/plugins/PluginList.vue`：插件列表与详情、配置、诊断、关联和日志界面。
- `frontend/src/views/plugins/PluginFields.vue`：按字段声明生成配置/检测控件；`BiPluginDebug.vue` 单独维护 BI 专用表单。

新增表：`plugin_configs`、`agent_plugins`、`plugin_activity`，由应用启动 `init_db()` 幂等创建。
`plugin_configs.values_json` 保存普通字段，`secrets_json` 保存字段名到密文的映射。升级时自动新增这两列；历史 BI 行兼容读取，下次保存时写入通用列并清空旧地址和密文列。部署时应重启全部后端进程，使页面、接口和运行工具使用同一版本。
加密沿用 `MODEL_API_KEY_ENCRYPTION_KEY` 主密钥，使用插件专属认证上下文；生产环境应固定主密钥，变更后旧密文无法解密。
操作记录只存操作类型、状态、静态摘要、耗时和 Agent/Trace 标识，不保存 Token、请求头、服务地址或完整业务结果。
日志按每页 30 条游标分页，运行调用的审计写入失败不会重试业务查询。

## API

所有接口都要求登录，使用认证用户 ID 查询配置；客户端不能指定其他用户。

| 接口 | 作用 |
| --- | --- |
| `GET /api/plugins` | 内置目录和当前用户状态 |
| `GET /api/plugins/{id}` | 公开详情，config_values 为普通字段，configured_secrets 仅列已保存密钥名 |
| `PUT /api/plugins/{id}/config` | 保存配置，携带 revision |
| `PUT /api/plugins/{id}/enabled` | 启停，携带 enabled 和 revision |
| `POST /api/plugins/{id}/import-environment?revision=N` | 显式导入当前服务器环境配置 |
| `POST /api/plugins/{id}/test` | parameters 对象，按 test_fields 校验后检测 |
| `POST /api/plugins/{id}/debug` | tool_name 和 input 对象，按工具 Schema 校验后执行 |
| `GET /api/plugins/{id}/tools` | 工具说明和参数 Schema |
| `GET /api/plugins/{id}/skill?path=SKILL.md` | 声明中的只读 Skill 文件 |
| `GET /api/plugins/{id}/activity?before_id=N` | 最近操作及调用记录 |
| `DELETE /api/plugins/{id}?revision=N` | 无绑定时移除用户配置 |

Agent 创建/编辑接口增加 `plugin_ids` 字符串数组；省略或传 null 时不修改已有绑定，空数组解除全部绑定。新绑定要求插件已配置且启用，已停用的原有绑定可保留。
无配置插件的 `config_status` 为 `not_required`，首次启用可直接提交 `{"enabled":true,"revision":0}`；保存后按接口返回的 revision 更新。
版本不匹配返回 409；未知插件返回 404；参数或配置不完整返回 400/422。健康检测的上游业务失败用 `ok=false` 返回，并保留结构化 CLI 错误码。

通用保存示例（revision 使用最近读取的版本）：

```json
{
  "values": {"base_url": "https://bi.example.test", "timeout_seconds": 30, "max_output_bytes": 1048576},
  "secrets": {"token": "example-placeholder"},
  "clear_secrets": [],
  "revision": 0
}
```

普通字段未提交则保留原值或默认值；密钥未提交或传空字符串保留原值。通过 `clear_secrets: ["token"]` 明确清除；同一个密钥不能同时设置新值和清除。未声明字段、错误类型或通过 values 提交密钥均拒绝。

检测示例：`{"parameters":{"product_key":"example-product"}}`。
BI 调试示例：`{"tool_name":"BiCli","input":{"arguments":["metadata","events","list","--product-key","example-product","--page-num","1","--page-size","50"]}}`。
JSON 调试示例：`{"tool_name":"JsonFormat","input":{"content":"{\"b\":2,\"a\":1}","indent":2,"sort_keys":true}}`。
旧 BI 扁平配置、product_key 检测请求及 arguments 调试请求在协议边界兼容转换，新页面统一使用上述通用格式。

## 运行加载与兼容

每次创建 Agent 工具时，按当前用户和 Agent 绑定读取独立配置快照，再交给对应的固定执行器。BI 插件注册 `BiCli` 并合并 `bi-metadata` Skill；JSON 插件只注册 `JsonFormat`。同名数据库 Skill 由插件版本替代。工具名称与 MCP 等来源冲突时明确失败。
尚未保存 BI 插件配置的用户继续使用原 `BI_CLI_ENABLED` 等环境变量入口。保存用户配置后，该用户改由插件启停及 Agent 绑定控制，不再向未绑定 Agent 注入全局 `BiCli`。
移除用户配置后会恢复旧环境变量兼容逻辑。环境变量不会自动复制到用户配置，导入需在页面显式操作。
目前提供受信任的内置 BI 和 JSON 插件，暂不支持上传和执行第三方 Python 包、在线市场或自动升级。

## 扩展内置插件

1. 新增经过审查的 manifest，声明身份、执行器、工具、权限和配置；加入 `registry.py` 固定注册表。
2. `fields` 支持 `string`、`secret`、`integer`、`boolean`、`select`，分别显示文本、密钥、数字、开关和枚举控件。声明 key、label、required、default，以及 minimum/maximum、max_length、format=url、placeholder 或 options。空数组表示无需配置。
3. `capabilities` 中 connection_test、environment_import、debug 默认关闭。只有声明并实现的能力才开放；连接检测参数由 `test_fields` 描述，配置区标题由 `config_title` 描述。
4. 在 `executors.py` 实现并固定注册执行器：`validate(settings)`、`build_tools(context, settings)`；按需实现 `probe(settings, parameters)` 和 `environment()`。工具必须有 Pydantic 参数实体，其名称必须与清单一致。工具输出使用 JSON，至少包含布尔值 ok，业务数据放 data，失败用 error.code。
5. 通用调试默认展示工具输入 JSON 对象；`definitions()` 可返回 `example_input`。确需专用表单时增加经过审查的组件映射，禁止根据清单执行任意前端代码。
6. Skill 为可选项。有 Skill 时声明 skill_name/skill_files，并注册受信任目录；没有 Skill 时省略，页面和运行时不会创建空 Skill。
7. 补充声明校验、密钥生命周期、用户隔离、工具执行和页面验证。公共管理服务无需增加业务字段分支。

manifest 只声明能力，不会自动安装依赖或创建任意工具；新增执行器仍需服务端代码适配与审查。Python 服务使用 `PluginSettings`、`StoredPlugin`、`RuntimePlugins` 等实体，动态字段映射仅用于配置内容和 JSON 协议边界。

## 验证记录

- 后端 `unittest discover -s backend/test -p 'test_*.py'`：执行 138 项，137 项通过，1 项数据库集成默认跳过。
- `PLUGIN_DB_TEST=1 backend/.venv-langchan/bin/python -m unittest backend.test.test_plugins`：14 项全部通过，临时用户及关联记录已清理。
- 数据库集成覆盖用户隔离、Token 加密与保留/清除、版本冲突、Agent 绑定、启停、审计脱敏、重复检测及旧检测不能覆盖新配置。
- 连接检测与调试使用本机模拟 BI HTTP 服务，并实际启动固定 CLI 子进程；未访问真实业务 BI 或调用模型。
- 前端生产构建通过，保留项目已有的依赖注释、CJS API 与大包提示。
- 通用字段校验覆盖默认值、合法 0/False、整数/布尔/枚举错误、未知字段、地址校验及多个任意名称的密钥保留/清除。
- 数据库集成额外覆盖历史 BI 列升级、通用密钥 JSON 密文、无配置插件直接启用、JsonFormat 运行加载与调用审计。
- Playwright 使用临时账号验证 BI 配置保存与密钥保留、连接检测和调试，JSON 插件直接启用、实际执行、无 Skill 表单，以及双插件 Agent 绑定展示。
- 1440px/390px 页面截图已检查；手机端无横向溢出和脚本错误，切换插件后字段、工具输入和结果正确重置，启用时清除必填 Token 会被拒绝。

本次预览服务使用 `http://127.0.0.1:20003/plugins`，日志位于 `/tmp/agent-platform-plugin-preview.log`。使用原有项目账号登录；原 20000 端口服务需重启后才能加载新的后端路由。
