# LangGraph Checkpoint 机制说明

## 1. Checkpoint 是什么

在 LangGraph 中，Checkpoint 是某个图执行线程在一个执行步骤结束后的状态快照。

它保存的不是大模型权重，也不是普通日志，而是 Graph State，例如：

- 当前消息列表；
- Assistant 产生的工具调用；
- Tool 返回的执行结果；
- 图下一步准备执行的节点；
- Checkpoint ID、父 Checkpoint 和相关元数据。

Checkpoint 主要解决以下问题：

1. 多轮 Agent/Tool 节点之间传递状态；
2. 中断后从已有状态继续执行；
3. Human-in-the-loop 审批后恢复执行；
4. 查看历史状态或从旧状态创建分支；
5. 在多次 Graph 调用之间保留同一线程的状态。

Checkpoint 必须结合 `thread_id` 使用。可以将 `thread_id` 理解成 Checkpoint 的会话主键：

```python
config = {
    "configurable": {
        "thread_id": "session_10_message_98",
    }
}
```

相同 `thread_id` 会访问同一条状态链；不同 `thread_id` 相互隔离。

## 2. 当前项目的 Checkpointer

项目在 `backend/core/agent_factory.py` 中创建了模块级全局实例：

```python
# 全局内存 Checkpointer，供当前 Python 进程创建的 Agent Executor 共享。
_checkpointer = InMemorySaver()
```

创建 ReAct Agent 时将它传给 LangGraph：

```python
agent_executor = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_prompt,
    checkpointer=_checkpointer,
)
```

这意味着：

- 同一 FastAPI Python 进程中的 Agent Executor 共享一个 `InMemorySaver`；
- 不同 `thread_id` 的状态仍然隔离；
- Checkpoint 只存在于当前进程内存中；
- 后端重启后全部丢失；
- 多个 FastAPI Worker 进程之间不共享；
- 当前没有显式的过期或清理机制。

## 3. 单 Agent 聊天机制

### 3.1 长期消息由 MySQL 保存

当前聊天长期记忆的事实来源是 `chat_messages` 表，而不是 LangGraph Checkpoint。

每次用户发送消息时，系统会：

1. 将当前用户消息写入 MySQL；
2. 从 MySQL 查询该会话全部 `user/assistant` 历史消息；
3. 将历史消息转换为 `HumanMessage` 和 `AIMessage`；
4. 把完整消息列表作为 Graph 的初始 State 传入。

因此即使 FastAPI 重启、`InMemorySaver` 清空，聊天历史仍然可以从 MySQL 恢复。

### 3.2 每条用户消息使用新的 thread_id

当前代码生成方式：

```python
# 每条用户消息创建独立线程，避免与已经从 MySQL 恢复的历史重复叠加。
thread_id = f"session_{session_id}_message_{user_message_id}"
```

例如：

```text
会话 20，第 101 条用户消息
thread_id = session_20_message_101

会话 20，第 103 条用户消息
thread_id = session_20_message_103
```

它产生的实际效果是：

- Checkpoint 主要服务于“当前这一轮 Agent 执行”；
- 一轮内的 LLM、Tool、LLM 多步状态会进入同一条 Checkpoint 链；
- 下一条用户消息不会继续使用上一轮 Checkpoint；
- 下一轮上下文由 MySQL 重新组装，而不是从 Checkpoint 读取。

这是一个刻意的防重复设计。假如直接使用固定的：

```python
thread_id = f"session_{session_id}"
```

同时又把 MySQL 全量历史再次传入 Graph，那么 LangGraph 可能把旧 Checkpoint 状态和全量历史叠加，造成消息重复。

### 3.3 当前聊天数据流

```text
MySQL chat_messages
        │
        │ 查询完整历史
        ▼
HumanMessage / AIMessage 列表
        │
        │ 新 thread_id：session_{session}_message_{message}
        ▼
LangGraph ReAct Agent
        │
        ├── Checkpoint 1：用户消息 + Assistant tool_call
        ├── Checkpoint 2：追加 ToolMessage
        └── Checkpoint 3：追加最终 AIMessage
                 │
                 ▼
        最终回答写回 MySQL
```

## 4. 多 Agent 工作流机制

工作流中的每个步骤使用独立 `thread_id`：

```python
thread_id = f"workflow_{workflow_id}_run_{run_id}_step_{step_order}"
```

例如：

```text
workflow_3_run_52_step_1
workflow_3_run_52_step_2
```

所以：

- 同一次工作流运行中的不同步骤互不共享 Checkpoint；
- 每个步骤内部的 LLM/Tool 多轮执行共享自己的状态链；
- 不同工作流运行通过 `run_id` 隔离；
- 工作流业务状态由 MySQL 的 workflow run/step 表保存；
- 事件流由 Redis Stream 保存；
- LangGraph Checkpoint 仍然只是当前进程内存状态。

当前代码没有在服务重启后读取旧 Checkpoint 并恢复某个执行步骤，因此它尚未形成真正的“持久化断点续跑”。

## 5. Checkpoint、MySQL、Redis 和 Trace 的区别

| 存储 | 当前用途 | 是否是 LangGraph Checkpoint | 重启后是否保留 |
|---|---|---:|---:|
| `InMemorySaver` | Graph 执行状态快照 | 是 | 否 |
| MySQL `chat_messages` | 聊天长期历史 | 否 | 是 |
| MySQL workflow run/step | 工作流状态和步骤结果 | 否 | 是 |
| MySQL trace 表 | LLM/Tool 调用观测与排障 | 否 | 是 |
| Redis Stream | 工作流实时事件和 SSE 回放 | 否 | 按 TTL 保留 |
| Redis Runtime Queue | Python 任务排队和结果等待 | 否 | 按队列/TTL 策略 |

需要特别注意：Trace 可以告诉开发者“发生了什么”，但不能直接作为 LangGraph 的可恢复 State 使用。

## 6. 当前方案的优点

1. 实现简单，不需要额外 Checkpoint 数据库；
2. MySQL 会话历史能够跨进程重启恢复；
3. 每条消息使用独立 `thread_id`，避免全量历史重复；
4. 单轮 ReAct 工具调用仍具有完整的 Graph State；
5. 聊天业务数据、Trace 和 Graph 内部状态职责相对清晰。

## 7. 当前方案的限制和风险

### 7.1 不支持真正断点续跑

后端重启后，正在执行的 Agent Checkpoint 会丢失。虽然历史消息还在 MySQL，但无法精确恢复到某个 Tool 节点或审批节点。

### 7.2 多进程不共享

如果启动多个 Uvicorn Worker，每个进程都有独立 `InMemorySaver`。同一个 `thread_id` 被不同进程处理时，无法访问同一状态链。

当前每条消息使用唯一 `thread_id`，降低了这个问题对普通聊天的影响，但仍无法用于跨请求恢复。

### 7.3 内存可能持续增长

每条聊天消息和每个工作流步骤都会产生新的 `thread_id`，而全局 `InMemorySaver` 没有显式清理逻辑。长时间运行后，历史 Checkpoint 可能持续占用内存。

### 7.4 Checkpoint 没有成为业务事实来源

当前真正的会话历史和工作流结果保存在 MySQL。即使改为持久化 Checkpointer，也必须明确 MySQL 与 Checkpoint 谁是权威来源，避免双写状态不一致。

## 8. 后续实现方案

### 方案 A：保持 MySQL 为长期记忆，Checkpoint 只服务单次执行

适用场景：普通聊天和短时工具调用，不要求 Human-in-the-loop 或节点级恢复。

实现步骤：

1. 保留每条消息独立 `thread_id`；
2. 继续从 MySQL 恢复完整聊天历史；
3. 为 `InMemorySaver` 增加执行完成后的删除或 TTL 清理；
4. 增加 Checkpoint 数量和内存占用监控；
5. 明确 Checkpoint 不承担长期记忆职责。

优点是改造风险小，符合当前项目架构。当前阶段推荐此方案。

### 方案 B：改用持久化 Checkpointer

适用场景：要求断点续跑、人工审批、跨请求继续 Graph 或多实例部署。

可以选择 LangGraph 支持的持久化 Saver，例如 PostgreSQL Saver。若继续使用 MySQL，需要实现并充分测试自定义 Saver，维护成本更高。

建议的线程标识：

```text
聊天：user:{user_id}:session:{session_id}
工作流：user:{user_id}:workflow:{workflow_id}:run:{run_id}:node:{node_id}
```

实施时必须同步调整消息策略：

1. 使用稳定 `thread_id`；
2. 不再每次把 MySQL 全量历史直接追加到已有 Graph State；
3. 定义新会话、重试、重新生成和分支的 Checkpoint 规则；
4. 定义 Checkpoint 与 MySQL 消息的事务或最终一致性策略；
5. 为 Checkpoint 设置用户隔离、保留周期和删除接口；
6. 对 Tool 结果、上传文件引用和敏感数据进行清理；
7. 验证多 Worker 下并发写入和幂等恢复。

### 方案选择建议

```text
只需要聊天历史和普通 Tool Calling
    -> 方案 A

需要服务重启后从工具节点继续
    -> 方案 B

需要人工审批后继续执行
    -> 方案 B

需要查看或回退 Graph 历史状态
    -> 方案 B
```

## 9. 总结

当前项目不是完全依赖 LangGraph Checkpoint 保存记忆，而是采用混合机制：

```text
MySQL = 长期聊天和业务状态
InMemorySaver = 单轮 Graph 执行状态
Trace = 可观测记录
Redis = 事件流和运行时任务通信
```

当前设计能够支持普通聊天和多轮 Tool Calling，但不支持跨进程、跨重启的 LangGraph 节点级恢复。若后续增加审批、暂停/恢复或真正的工作流断点续跑，应升级为持久化 Checkpointer，并重新设计消息历史的唯一事实来源。

## 10. 自定义 State 增量实现（2026-09-02）

项目已新增 `AgentPlatformState`，继承 LangGraph 预置 `AgentState`，因此原有
`messages` Reducer 和 `remaining_steps` 管理逻辑保持不变。

当前扩展字段包括：

- `runtime_file_ids`：本轮允许 Runtime 使用的逻辑文件 ID；
- `available_skills`：当前 Agent 绑定的 Skill 名称；
- `loaded_skills`：为 State-aware Skill Tool 预留的已加载标记；
- `current_input`：当前聊天或工作流节点输入；
- `current_node_id`：当前业务节点；
- `structured_result`：模型输出校验后的结构化对象；
- `approval_status`、`error`：为后续原生工作流状态迁移预留。

聊天和工作流仍使用原有 MySQL 持久化逻辑；Checkpoint 写入失败只记录警告，
不会阻断现有响应。当前仍为 `InMemorySaver`，因此本次改造提供的是显式业务 State
基础，而不是跨进程持久化恢复。
