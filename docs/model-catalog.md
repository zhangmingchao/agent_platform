# 百炼模型目录

模型管理点击「添加模型」后默认进入阿里云百炼目录，可按名称或 ID 搜索、分页和刷新。点击选择自动填写名称、模型 ID、提供商和兼容基础地址，再填写自己的推理 API Key，测试连接后创建。切换「自定义添加」可手动填写其他模型。编辑配置仍使用现有表单，API Key 留空保留原值。

## 后端配置

- `BAILIAN_CATALOG_URL`：目录接口，默认本项目百炼实例的 `/api/v1/models`。
- `BAILIAN_INFERENCE_BASE_URL`：同实例 `/compatible-mode/v1`，不要附加 `/chat/completions`，SDK 会补齐路径。
- `BAILIAN_CATALOG_API_KEY`：目录查询凭据，优先从环境变量读取。
- `BAILIAN_CATALOG_API_KEY_FILE`：未配置环境变量时读取此文件，默认 `backend/data/bailian_catalog_api_key`。文件只包含 Key，建议权限 `0600`；data 已忽略版本管理。
- `BAILIAN_CATALOG_CACHE_SECONDS`：完整目录缓存秒数，默认 300。

本地目录凭据已配置在上述忽略的文件中。环境变量变更需要重启 API；本地凭据文件更新后可以点击刷新目录。凭据不进入前端资源和目录响应。目录凭据用于查询，用户推理凭据仍走现有模型加密存储，两者相互独立。

## 接口与范围

`GET /api/models/catalog?page_no=1&page_size=10&search=qwen&refresh=false` 必须登录。页码从 1 开始，页长 1～100，搜索词最多 100 字；主动刷新受用户限流约束。返回公开实体 `items/total/page_no/page_size/source`，不返回 Key 或上游完整响应。

服务每批读取 100 条上游记录，完整成功后才更新缓存，五分钟内搜索和分页不重复请求上游。总请求超时 25 秒。网络、鉴权、业务或格式错误显示安全提示，可重试或使用自定义添加。上游鉴权错误映射为 503，避免触发前端登录失效流程。

初筛要求 TG 文本生成能力、Text 输入与输出、非 realtime 且无下线信息。目录声明不能保证具体模型支持 Chat Completions 或当前推理 Key 有权调用，因此仍需测试连接；语音、向量等专用接口模型应使用对应接口，不通过本聊天模型入口添加。百炼模型统一沿用 qwen 的 OpenAI 兼容适配器，无须修改 Agent 调用链或数据库。
