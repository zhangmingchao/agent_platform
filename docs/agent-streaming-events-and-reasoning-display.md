# Agent 流式事件与“思维过程”展示实现文档

> 2026-09-01 协议升级：单 Agent 聊天已改为按 LLM 轮次确认分类。下文如仍出现
> `thinking/chunk/reclassify`，仅用于说明旧协议，不应再用于新客户端实现。

## 现行单 Agent 事件协议（v2）

模型文本先通过 `pending_text_delta` 实时显示在“处理中”区域。一轮调用结束后，后端检查
完整输出：存在 `tool_calls` 时发送 `llm_round_classified(thinking)`，否则发送
`llm_round_classified(answer)`。分类以 `round_id` 为作用域，连续或并行工具调用不会互相覆盖。

```text
llm_round_start
  -> pending_text_delta (0..N)
  -> llm_round_classified: thinking | answer
  -> tool_started/tool_completed (如有)
  -> 下一轮 llm_round_start
  -> done
```

工具事件使用 LangChain 运行 ID 作为 `tool_run_id`，前端按 ID 更新对应工具，不能假设最后
一个工具就是当前完成的工具。正式回答保存到 `chat_messages.content`，执行说明保存到
`chat_messages.reasoning_content`；历史消息中的执行说明默认折叠、可主动展开，且不会重新
注入 LLM 上下文。

这里展示的是模型主动输出的解释文本和工具规划，不代表、也不尝试获取模型供应商未返回的
内部思维链。正式回答使用主文字色；执行说明采用中性灰 `#4b5563`、标题采用
`#6b7280`，配合浅灰背景降低视觉层级。

## 1. 文档目标

本文说明 Agent Platform 如何利用 LangChain/LangGraph 事件和 SSE 展示 Agent 的实时执行过程，并对每一种后端事件、前端处理和页面效果逐一对应。

本文覆盖两种运行模式：

1. 单 Agent 聊天。
2. 多 Agent 工作流。

需要首先明确：

> 页面中的“思维过程”不是模型内部隐藏的完整 Chain of Thought，而是模型主动输出的文本、Tool Calling、节点状态和系统可观测事件。

商业产品更准确的名称是“执行过程”“任务处理过程”或“运行轨迹”。

---

## 2. 总体原理

```text
用户请求
  ↓
FastAPI 创建 LangGraph Agent
  ↓
agent.astream_events(...)
  ↓
监听 LangChain/LangGraph 原始事件
  ├── on_chat_model_start
  ├── on_chat_model_stream
  ├── on_chat_model_end
  ├── on_tool_start
  └── on_tool_end
  ↓
转换成平台业务事件
  ├── thinking
  ├── chunk/token
  ├── tool_start
  ├── tool_end
  ├── structured_result
  ├── error
  └── done
  ↓
通过 SSE 推送浏览器
  ↓
前端根据事件类型更新不同 UI 区域
```

SSE 的作用只是实时传输事件。事件的分类、持久化和页面展示由平台自己控制。

---

## 3. 为什么不能直接称为完整 CoT

大模型可能存在内部推理过程，但平台通常只能安全获得以下内容：

- 模型主动生成的文本 Token。
- 模型生成的 Tool Call。
- Tool 的输入和输出。
- LangGraph 节点开始、结束、失败等事件。
- 平台生成的状态摘要。

平台不应该：

- 尝试提取或承诺展示模型隐藏推理。
- 把系统 Prompt、密钥或完整 Tool Secret 展示给用户。
- 将未经处理的模型草稿当作可靠结论。
- 将 Tool 原始返回中的敏感信息直接暴露到页面。

因此推荐产品文案：

```text
不推荐：查看模型完整思维链
推荐：查看执行过程
推荐：查看任务处理详情
推荐：查看 Agent 运行轨迹
```

---

## 4. 两套 SSE 事件协议

当前项目存在两套相关但不同的 SSE 协议。

| 模式 | 后端入口 | 传输来源 | 前端页面 |
|---|---|---|---|
| 单 Agent 聊天 | `POST /api/chat/stream` | FastAPI 直接生成 SSE | `Chat.vue` |
| 多 Agent 工作流 | `GET /api/workflows/runs/{run_id}/events` | Redis Stream 转换为 SSE | `WorkflowRun.vue` |

### 4.1 单 Agent SSE 格式

单 Agent 使用无命名 SSE，事件类型放在 JSON 的 `type` 字段中：

```text
data:{"type":"chunk","content":"北京今天晴"}

```

前端读取：

```javascript
const event = JSON.parse(payload)

if (event.type === 'chunk') {
  streamingText.value += event.content
}
```

### 4.2 工作流 SSE 格式

工作流使用标准命名 SSE：

```text
id: 1720000000000-0
event: node_start
data: {"runId":7,"nodeId":"agent-1",...}

```

事件先写入 Redis Stream，再由 HTTP 接口读取并转换为 SSE。

这种方式允许：

- 浏览器断开后后台继续执行。
- 重新订阅历史事件。
- 使用 Redis Stream ID 恢复读取。
- 多 Agent 节点共享统一事件流。

---

## 5. 单 Agent 聊天事件处理原理

核心实现：

- `backend/core/streaming.py`
- `backend/services/chat_service.py`
- `backend/routers/chat.py`
- `frontend/src/views/chat/Chat.vue`

### 5.1 原始事件来源

后端调用：

```python
async for event in agent_executor.astream_events(
    {"messages": messages},
    config=config,
    version="v2",
):
    ...
```

`astream_events()` 在 Agent 执行期间持续产生事件，而不是等全部执行完成后一次返回。

---

## 6. 单 Agent 事件逐项对照

### 6.1 `on_chat_model_start`

#### 来源

LangChain/LangGraph 原始事件，表示一次 LLM 调用开始。

#### 后端处理

- 重置本轮文本分类状态。
- 创建 LLM Trace Span。
- 记录模型名和输入摘要。

#### 是否直接发送前端

当前不直接发送独立 SSE 事件。

#### 页面效果

页面仍保持“AI 思考中”或现有执行状态。

---

### 6.2 `on_chat_model_stream`

#### 来源

模型流式返回的 Token 或 Tool Call 片段。

#### 后端判断

```text
chunk.tool_call_chunks 不为空
  → 模型正在产生 Tool Call
  → has_seen_tool = true

chunk.content 不为空
  → 根据当前阶段分类为 thinking 或 chunk
```

#### 平台事件

- `thinking`
- `chunk`

#### 页面效果

- `thinking` 追加到折叠的执行过程区域。
- `chunk` 追加到最终回答区域。

---

### 6.3 `thinking`

#### 事件结构

```json
{
  "type": "thinking",
  "content": "正在分析用户的问题……"
}
```

#### 当前分类规则

模型尚未出现 Tool Call 时产生的文本，暂时被归类为 `thinking`。

#### 前端处理

```javascript
thinkingText.value += event.content || ''
```

#### 页面效果

显示在“思考过程”折叠面板。

#### 注意

这只是临时分类。一次没有 Tool 调用的普通回答，开始时也可能被暂时放入 `thinking`，之后通过 `reclassify` 修正。

---

### 6.4 `chunk`

#### 事件结构

```json
{
  "type": "chunk",
  "content": "北京今天晴，气温约 26℃。"
}
```

#### 当前分类规则

已经出现过 Tool Call 后，后续模型输出被视为最终回答。

#### 前端处理

```javascript
streamingText.value += event.content || ''
```

#### 页面效果

逐字显示在最终回答区域，并显示流式光标。

---

### 6.5 `on_chat_model_end`

#### 来源

一次 LLM 调用结束。

#### 后端处理

- 完成 LLM Trace Span。
- 检查输出中是否包含 `tool_calls`。
- 必要时发送 `reclassify` 修正文本分类。

---

### 6.6 `reclassify`

#### 目的

解决流式过程中无法提前确定一段文本是“过程文本”还是“最终回答”的问题。

#### `reclassify: answer`

事件：

```json
{
  "type": "reclassify",
  "content": "answer"
}
```

适用情况：模型没有调用 Tool，之前暂存在 `thinking` 的内容其实是最终回答。

前端处理：

```javascript
streamingText.value = thinkingText.value + streamingText.value
thinkingText.value = ''
```

#### `reclassify: thinking`

事件：

```json
{
  "type": "reclassify",
  "content": "thinking"
}
```

适用情况：某段文本后来被确认属于 Tool 调用前的过程内容。

前端处理：

```javascript
thinkingText.value += streamingText.value
streamingText.value = ''
```

---

### 6.7 `on_tool_start` → `tool_start`

#### 原始事件

LangChain 在执行 Tool 前产生 `on_tool_start`。

#### 平台事件

```json
{
  "type": "tool_start",
  "content": "{\"name\":\"ExecutePython\",\"input\":\"...\"}"
}
```

#### 后端处理

- 创建 Tool Trace Span。
- Tool 输入最大展示 200 个字符。
- 发送 Tool 名称和输入摘要。

#### 前端处理

```javascript
toolCalls.value.push({
  name: toolData.name,
  input: toolData.input,
  status: 'running'
})
```

#### 页面效果

工具面板新增一项：

```text
执行中  ExecutePython  {code: ...}
```

---

### 6.8 `on_tool_end` → `tool_end`

#### 原始事件

Tool 执行结束时产生。

#### 平台事件

```json
{
  "type": "tool_end",
  "content": "工具输出摘要"
}
```

#### 后端处理

- 完成 Tool Trace Span。
- Trace 保存工具输出。
- 前端事件只发送截断后的摘要。

#### 前端处理

```javascript
toolCalls.value[toolCalls.value.length - 1].status = 'done'
```

#### 页面效果

当前工具从执行中变为已完成。

---

### 6.9 `structured_result`

#### 产生条件

Agent 配置了结构化输出 JSON Schema，并且最终完整输出通过 Schema 校验。

#### 事件结构

```json
{
  "type": "structured_result",
  "content": "{\"risk_level\":\"high\",\"approved\":false}"
}
```

#### 前端处理

- 将 `content` 解析为 JSON。
- 保存到 `structuredResult`。
- 使用格式化 JSON 区域展示。

#### 持久化

保存到：

```text
chat_messages.structured_content
```

---

### 6.10 `error`

#### 事件结构

```json
{
  "type": "error",
  "content": "错误原因"
}
```

#### 产生场景

- LLM 调用失败。
- Tool 执行失败且未被正常转换为 Tool 结果。
- 结构化输出不是合法 JSON。
- 结构化输出不符合 Schema。
- Agent 执行发生未处理异常。

#### 前端处理

显示 Element Plus 错误消息。

---

### 6.11 `done`

#### 事件结构

```json
{
  "type": "done",
  "content": ""
}
```

#### 语义

本次单 Agent SSE 执行已经结束。

#### 前端处理

- 设置 `streaming=false`。
- 将完整回复加入消息列表。
- 清理临时流式状态。

对于结构化输出，后端会先校验并发送 `structured_result`，最后才发送 `done`。

---

## 7. 单 Agent 文本分类状态机

当前核心状态：

```python
has_seen_tool = False
current_call_text_phase = None
```

简化状态流：

```text
开始调用 LLM
  ↓
收到文本，但尚未发现 Tool
  ↓
发送 thinking
  ├── 后来发现 tool_calls
  │     → 保持 thinking
  │     → 执行 Tool
  │     → 下一轮模型文本发送 chunk
  │
  └── 本轮结束且没有 tool_calls
        → 发送 reclassify:answer
        → 前端把 thinking 移到最终回答
```

该算法是 UI 分类算法，不是对模型内部推理的读取。

---

## 8. 单 Agent 事件对照总表

| LangChain 原始事件 | 平台 SSE 类型 | 前端状态 | 页面区域 | 是否持久化 |
|---|---|---|---|---|
| `on_chat_model_start` | 无 | 重置调用阶段 | AI 思考中 | Trace Span 开始 |
| `on_chat_model_stream` | `thinking` | `thinkingText += content` | 执行过程 | 最终根据分类处理 |
| `on_chat_model_stream` | `chunk` | `streamingText += content` | 最终回答 | 完成后写消息 |
| `on_chat_model_end` | `reclassify` | 移动 thinking/chunk | 修正显示区域 | 修正后写消息 |
| `on_tool_start` | `tool_start` | 添加 running Tool | 工具面板 | Trace Span 开始 |
| `on_tool_end` | `tool_end` | Tool 改为 done | 工具面板 | Trace Span 完成 |
| Schema 校验成功 | `structured_result` | 保存 JSON | 结构化结果 | `structured_content` |
| 执行异常 | `error` | 错误提示 | 消息提示 | Trace Error |
| Agent 完成 | `done` | `streaming=false` | 结束流式状态 | 回复已保存 |

---

## 9. 多 Agent 工作流事件原理

核心实现：

- `backend/services/workflow_service.py`
- `backend/core/event_publisher.py`
- `backend/routers/workflows.py`
- `frontend/src/views/workflows/WorkflowRun.vue`

工作流执行与浏览器连接解耦：

```text
工作流执行器
  ↓ publisher.publish(...)
Redis Stream
  ↓ XREAD
FastAPI SSE 接口
  ↓
浏览器
```

Redis Stream Key：

```text
agent:run:{run_id}:events
```

---

## 10. 工作流事件统一结构

每个工作流 SSE 事件包含：

```json
{
  "id": "Redis Stream ID",
  "type": "node_start",
  "runId": 7,
  "nodeId": "agent-1",
  "sequence": 2
}
```

字段说明：

| 字段 | 作用 |
|---|---|
| `id` | Redis Stream ID，用于恢复订阅 |
| `type` | 业务事件类型 |
| `runId` | 工作流 Run ID |
| `nodeId` | 当前节点 ID，可为空 |
| `sequence` | 发布器内部事件序号 |

---

## 11. 工作流事件逐项对照

### 11.1 `start`

表示工作流开始执行。

```json
{
  "type": "start",
  "run_id": 7,
  "workflow_id": 3,
  "input": "分析需求"
}
```

前端：初始化 Run 信息，并在日志中显示“运行已启动”。

### 11.2 `node_start`

表示 Agent 节点开始执行。

```json
{
  "type": "node_start",
  "node_id": "agent-1",
  "node_type": "agent",
  "label": "需求分析师",
  "step_order": 1
}
```

前端：

- 将节点状态设为 `running`。
- 设置当前活动节点。
- 创建步骤展示记录。
- 流程图节点显示运行中样式。

### 11.3 `token`

表示工作流 Agent 节点的实时模型文本。

```json
{
  "type": "token",
  "node_id": "agent-1",
  "content": "正在分析需求"
}
```

前端：追加到对应节点的 `streamOutput`。

注意：当前工作流没有单独的 `thinking` 事件，节点文本统一使用 `token`。

### 11.4 `tool_start`

表示某个工作流 Agent 节点开始调用 Tool。

```json
{
  "type": "tool_start",
  "node_id": "agent-1",
  "tool": "ExecutePython"
}
```

前端：向执行日志追加“调用工具”。

### 11.5 `tool_end`

表示 Tool 调用完成。

```json
{
  "type": "tool_end",
  "node_id": "agent-1",
  "tool": "ExecutePython",
  "output": "返回摘要"
}
```

前端：向执行日志追加“工具返回”。

### 11.6 `structured_result`

表示节点结构化输出通过 JSON Schema 校验。

```json
{
  "type": "structured_result",
  "node_id": "agent-1",
  "data": {
    "risk_level": "high",
    "approved": false
  }
}
```

前端：

- 保存到节点 `output_json`。
- 显示“结构化结果校验通过”。
- 使用 JSON 格式展示。

数据库保存到：

```text
multi_agent_run_steps.output_json
```

### 11.7 `node_done`

表示节点成功完成。

```json
{
  "type": "node_done",
  "node_id": "agent-1",
  "output": "节点最终输出"
}
```

前端：

- 节点状态改为 `success`。
- 保存节点最终文本。
- 流程图节点显示完成样式。

### 11.8 `branch`

表示条件节点已经选择某个分支。

```json
{
  "type": "branch",
  "node_id": "condition-1",
  "branch_idx": 0,
  "branch_label": "高风险",
  "target_node_id": "approval-1"
}
```

前端：在执行日志中显示命中的条件分支。

### 11.9 `parallel_start`

表示并行节点开始执行多个分支。

```json
{
  "type": "parallel_start",
  "node_id": "parallel-1",
  "branch_count": 3
}
```

前端：显示并行分支数量。

### 11.10 `parallel_done`

表示全部并行分支完成并合并结果。

```json
{
  "type": "parallel_done",
  "node_id": "parallel-1",
  "branch_count": 3,
  "merged_output": "合并后的结果"
}
```

前端：显示并行执行完成。

### 11.11 `approval_required`

表示执行到人工确认节点并暂停。

```json
{
  "type": "approval_required",
  "run_id": 7,
  "step_id": 20,
  "node_id": "approval-1",
  "label": "发布审核",
  "prompt": "确认发布？",
  "input": "待审核内容"
}
```

前端：

- Run 状态设为 `waiting_approval`。
- 显示批准、拒绝和审批意见输入框。
- 当前 SSE 连接正常结束。

### 11.12 `approval_decided`

表示用户已经批准或拒绝。

```json
{
  "type": "approval_decided",
  "run_id": 7,
  "step_id": 20,
  "node_id": "approval-1",
  "approved": true,
  "comment": "同意发布"
}
```

批准后前端使用上一次 `approval_required` 的 Redis Stream ID 重新订阅，只读取其后的事件。

### 11.13 `rejected`

表示人工审批拒绝，工作流终止。

```json
{
  "type": "rejected",
  "run_id": 7,
  "status": "rejected",
  "output": "已拒绝：内容不合规"
}
```

前端：设置 Run 为 `rejected` 并结束运行状态。

### 11.14 `done`

表示整个工作流成功完成。

```json
{
  "type": "done",
  "run_id": 7,
  "status": "success",
  "output": "工作流最终结果"
}
```

前端：

- Run 状态设为 `success`。
- 清空活动节点。
- 加载数据库中的最终 Run 和步骤详情。
- 关闭 SSE。

### 11.15 `error`

表示工作流执行失败。

```json
{
  "type": "error",
  "run_id": 7,
  "detail": "错误原因"
}
```

前端：

- Run 状态设为 `error`。
- 显示错误信息。
- 清空活动节点。
- 关闭 SSE。

---

## 12. 工作流事件对照总表

| 事件 | 产生位置 | 前端作用 | 是否关闭当前 SSE |
|---|---|---|---:|
| `start` | Run 执行入口 | 初始化运行日志 | 否 |
| `node_start` | Agent 节点执行前 | 节点设为运行中 | 否 |
| `token` | LLM 流式输出 | 展示节点实时文本 | 否 |
| `tool_start` | Tool 调用前 | 展示工具开始 | 否 |
| `tool_end` | Tool 调用后 | 展示工具完成 | 否 |
| `structured_result` | Schema 校验成功 | 展示结构化 JSON | 否 |
| `node_done` | Agent 节点完成 | 节点设为成功 | 否 |
| `branch` | 条件分支选择 | 展示命中分支 | 否 |
| `parallel_start` | 并行节点开始 | 展示分支数量 | 否 |
| `parallel_done` | 并行分支汇合 | 展示合并完成 | 否 |
| `approval_required` | 人工确认节点 | 显示审批操作 | 是 |
| `approval_decided` | 审批接口 | 更新审批步骤状态 | 否 |
| `rejected` | 审批拒绝 | 终止工作流 | 是 |
| `done` | Run 成功 | 展示最终结果 | 是 |
| `error` | Run 异常 | 展示错误 | 是 |

---

## 13. Trace 与 SSE 的区别

SSE 和 Trace 使用相同的执行事件来源，但用途不同。

| 能力 | SSE | Trace |
|---|---|---|
| 目的 | 实时反馈页面 | 审计、排障、统计 |
| 生命周期 | 当前连接或 Redis Stream TTL | 按 Trace 数据保留策略 |
| Token | 实时发送 | 不建议逐 Token 保存 |
| LLM 输入输出 | 页面只显示必要内容 | Span 保存调用详情 |
| Tool 输入输出 | 页面显示摘要 | Span 保存更完整数据 |
| 存储 | 直接传输或 Redis Stream | MySQL Run + MongoDB Span |

推荐原则：

```text
SSE 负责“现在发生了什么”
Trace 负责“之前完整发生过什么”
```

---

## 14. 安全与脱敏要求

发送事件前应检查：

- Tool 参数是否包含 API Key、Cookie、Authorization Header。
- MCP 返回是否包含账号、手机号、身份证或内部地址。
- LLM 输入是否包含系统 Prompt 和用户敏感数据。
- 错误堆栈是否包含数据库连接串或宿主机路径。
- 输出长度是否超过前端和 Redis 限制。

推荐不同展示级别：

```text
普通用户
  ├── 节点状态
  ├── Tool 名称
  └── 业务友好的执行摘要

开发者/管理员
  ├── Trace Span
  ├── 脱敏后的输入输出
  ├── Token、耗时和错误
  └── workflow/run/node 关联
```

---

## 15. 当前实现的限制

1. 单 Agent 的 `thinking/chunk` 是启发式分类，不保证所有模型行为一致。
2. 工作流当前只有统一 `token`，还没有节点级 `thinking/reclassify`。
3. Tool 面板使用最后一个 Tool 项更新状态，并行 Tool 调用时需要使用 Tool Call ID 精确关联。
4. 单 Agent SSE 没有事件 ID，浏览器断开后不能恢复到指定位置。
5. 工作流 Redis EventPublisher 在执行恢复时会重新创建，业务 `sequence` 可能重新计数，应以 Redis Stream ID 作为恢复游标。
6. Tool 输入输出只做了长度截断，仍需统一敏感字段脱敏。
7. 当前页面名称“思考过程”容易让用户误解为隐藏 CoT。

---

## 16. 推荐升级方案

### 16.1 统一事件协议

建议单 Agent 和工作流统一为：

```json
{
  "event_id": "...",
  "event_type": "tool.started",
  "run_id": "...",
  "node_id": "...",
  "span_id": "...",
  "timestamp": "...",
  "data": {}
}
```

### 16.2 使用 Tool Call ID 关联

```text
tool.started(call_id=abc)
tool.completed(call_id=abc)
```

避免并行 Tool 调用时把完成状态更新到错误的工具。

### 16.3 用安全执行摘要替代原始推理文本

推荐事件：

```json
{
  "event_type": "agent.progress",
  "data": {
    "stage": "data_analysis",
    "message": "正在分析上传的销售文件"
  }
}
```

该摘要由平台根据节点和 Tool 状态生成，不依赖暴露模型内部推理。

### 16.4 增加统一脱敏层

```text
LangChain 原始事件
  ↓
Event Normalizer
  ↓
Secret / PII Redactor
  ↓
SSE Publisher + Trace Writer
```

### 16.5 前端产品文案调整

建议将：

```text
思考过程
```

改为：

```text
执行过程
```

并展示确定性的步骤、工具和节点状态。

---

## 17. 总结

当前实现的核心不是读取模型隐藏思维链，而是：

```text
监听 LangChain/LangGraph 事件
  ↓
将原始事件转换为平台业务事件
  ↓
使用 SSE 实时传输
  ↓
前端按 thinking、Tool、节点和结果分类展示
  ↓
同时将 LLM/Tool 调用写入 Trace
```

单 Agent 侧使用 `thinking + reclassify + chunk` 解决流式文本阶段判断；工作流侧使用 Redis Stream 保存 `node/token/tool/branch/approval/done/error` 等确定性事件。两者后续应统一成一套可恢复、可脱敏、可审计的事件协议。
