# 外部 Agent 聊天 API

本文说明后端系统如何通过用户 API Key 调用 Agent Platform。外部接口与平台网页
聊天相互独立：平台维护自己的会话和消息，外部调用方负责保存并在每次请求中提交
完整历史。

## 1. 数据边界

| 调用来源 | 鉴权方式 | 历史来源 | 平台消息持久化 | Trace 来源 |
|---|---|---|---|---|
| 平台聊天 | `Authorization: Bearer <JWT>` | `chat_messages` | 保存 | `platform` |
| 外部 API | `X-API-Key: <key>` | 请求体 `messages` | 不保存 | `api` |
| 工作流 | 平台登录态 | 工作流节点 State | 不写聊天消息 | `workflow` |

API 调用仍会产生 Trace、模型 Token 用量和工具执行记录，但这些数据不会被下一次
API 请求自动加载为聊天历史。

## 2. 管理 API Key

密钥管理接口只能使用平台 JWT 调用。用户也可以在页面右上角用户菜单的
`API Key` 弹窗中完成相同操作。

### 2.1 查询状态

```http
GET /api/api-key
Authorization: Bearer <platform-jwt>
```

```json
{
  "configured": true,
  "key_prefix": "ap_live_0123456789abcdef",
  "status": "active",
  "created_at": "2026-09-18T10:00:00",
  "last_used_at": null
}
```

### 2.2 创建或轮换

```http
POST /api/api-key
Authorization: Bearer <platform-jwt>
```

```json
{
  "api_key": "ap_live_0123456789abcdef.secret",
  "key_prefix": "ap_live_0123456789abcdef",
  "created_at": "2026-09-18T10:00:00"
}
```

完整 `api_key` 只返回一次。再次调用该接口会立即使旧密钥失效。

### 2.3 吊销

```http
DELETE /api/api-key
Authorization: Bearer <platform-jwt>
```

## 3. 调用 Agent

```http
POST /api/v1/agents/{agent_id}/chat/stream
X-API-Key: ap_live_0123456789abcdef.secret
Content-Type: application/json
```

请求示例：

```json
{
  "messages": [
    {"role": "user", "content": "我叫张三"},
    {"role": "assistant", "content": "你好，张三"},
    {"role": "user", "content": "我刚才叫什么？"}
  ],
  "client_conversation_id": "customer-session-10001"
}
```

字段约定：

| 字段 | 必填 | 约束 | 作用 |
|---|---|---|---|
| `messages` | 是 | 1-100 条，只允许 `user`、`assistant` | 调用方维护的完整历史 |
| `messages[].content` | 是 | 单条 1-20000 字符 | 消息文本 |
| `client_conversation_id` | 否 | 最长 100 字符 | 调用方排查和关联请求使用 |

`messages` 最后一条必须是 `user`。接口拒绝 `system` 和 `tool` 角色，Agent 的系统提示词
始终使用平台配置。全部消息合计不能超过 100000 个字符。未知字段会被拒绝，因此不能
传入平台 `session_id`。

每次请求都会返回响应头：

```http
X-Request-ID: <本次平台请求ID>
```

该编号同时保存到 `trace_runs.request_id`，并具有唯一约束。它只标识本次生成请求，
不代表客户会话，也不能代替 API Key。排查调用问题或提交生成反馈时，应保存并使用该编号。

## 4. SSE 响应

响应类型为 `text/event-stream`，每个数据块采用统一结构：

```text
data:{"type":"事件类型","content":"事件内容",...}
```

常用事件：

| 事件 | 说明 |
|---|---|
| `llm_round_start` | 一轮模型调用开始 |
| `pending_text_delta` | 当前模型轮次的增量文本 |
| `llm_round_classified` | 将对应轮次标记为 `answer` 或 `thinking` |
| `tool_started` | Agent 开始调用工具 |
| `tool_completed` | 工具执行完成 |
| `structured_result` | Agent 配置结构化输出时的校验结果 |
| `response_completed` | 完整最终回答，外部调用方可直接使用该事件的 `content` |
| `plan_created` | Agent 开启显式规划后生成任务计划，`plan` 包含步骤列表 |
| `plan_step_started` | 一个计划步骤开始执行，`step` 包含当前步骤和状态 |
| `plan_step_completed` | 一个计划步骤执行完成，`step` 包含结果摘要 |
| `plan_step_failed` | 一个计划步骤执行失败，后续步骤停止执行 |
| `plan_completed` | 整体计划结束，`plan.status` 表示完成或失败 |
| `error` | 本次执行失败；`code=agent_timeout` 表示达到 Agent 整体时限 |
| `done` | SSE 流结束 |

`response_completed` 还可能包含 `reasoning_content` 和 `structured_content`。调用方只需要
最终结果时，可以忽略其他事件并等待 `response_completed`；收到 `done` 后关闭本次流。

Agent 整体时限由平台中的 Agent 配置决定，默认 `120` 秒，允许范围为 `10-1800` 秒。
它覆盖规划、全部模型轮次、工具调用和最终汇总，但不为单次模型调用设置独立时限。
达到时限时，接口会依次返回：

```text
data:{"type":"error","content":"Agent 执行超过 120 秒，已自动终止","code":"agent_timeout","timeout_seconds":120}

data:{"type":"done","content":""}
```

外部调用方可以通过关闭 HTTP/SSE 连接主动取消请求；服务端收到断连后会终止仍在执行的
Agent，并将对应 Trace 标记为 `cancelled`。系统自动超时的 Trace 状态为 `timeout`。

## 5. 调用示例

```bash
curl --no-buffer \
  --request POST \
  --header 'X-API-Key: ap_live_0123456789abcdef.secret' \
  --header 'Content-Type: application/json' \
  --data '{"messages":[{"role":"user","content":"你好"}]}' \
  http://127.0.0.1:20000/api/v1/agents/1/chat/stream
```

## 6. 安全与限额

- API Key 只能放在 `X-API-Key` 请求头中，不能放入 URL。
- 数据库只保存 API Key 的 SHA-256 哈希，不保存完整明文。
- API Key 只开放外部 Agent 接口，不能用于密码、模型和用户管理接口。
- Agent 必须属于 API Key 对应用户，否则返回 `404`。
- API Key 认证按来源 IP 限流，聊天调用按 API Key 限流。
- 模型每日 Token 限额仍按 API Key 所属用户和模型配置执行。
- 生产环境必须通过 HTTPS 暴露接口，并避免在代理日志中记录请求头。
