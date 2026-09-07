# 工作流生命周期方法类型说明

## 实现方案

`build_workflow_lifecycle_graph` 负责装配工作流执行节点、人工审批节点、条件路由和 Checkpointer。方法签名统一使用明确类型：

```python
def build_workflow_lifecycle_graph(
    checkpointer: BaseCheckpointSaver[str],
    run_segment: WorkflowSegmentRunner,
) -> CompiledStateGraph:
```

## 类型含义

| 名称 | 类型 | 作用 |
| --- | --- | --- |
| `checkpointer` | `BaseCheckpointSaver[str]` | LangGraph Checkpointer 的公共基类，支持内存、Redis、PostgreSQL 等实现 |
| `run_segment` | `WorkflowSegmentRunner` | 接收工作流 State，异步执行一个工作流片段 |
| 返回值 | `CompiledStateGraph` | 编译完成、可以调用 `ainvoke` 或恢复执行的 LangGraph 图 |

`WorkflowSegmentRunner` 是以下函数类型别名：

```python
WorkflowSegmentRunner = Callable[
    [WorkflowRuntimeState],
    Awaitable[Dict[str, Any]],
]
```

它表示：传入一个 `WorkflowRuntimeState`，异步返回需要合并回 State 的字段。

## 内部方法类型

| 方法 | 参数类型 | 返回类型 |
| --- | --- | --- |
| `execute_node` | `WorkflowRuntimeState` | `Dict[str, Any]`（异步） |
| `route_after_execute` | `WorkflowRuntimeState` | `str` |
| `approval_node` | `WorkflowRuntimeState` | `Dict[str, Any]` |
| `route_after_approval` | `WorkflowRuntimeState` | `str` |

这些 `Dict[str, Any]` 是 LangGraph 节点规定的 State 局部更新数据，并非普通业务查询返回值；业务实体仍应优先使用 dataclass 等强类型对象。

## resume_workflow_graph 调用链类型

| 接收变量或调用 | 类型 | 说明 |
| --- | --- | --- |
| `run` / `get_workflow_run()` | `Optional[Dict[str, Any]]` | 数据库中的工作流运行记录；查不到时为 `None` |
| `publisher` | `RedisStreamEventPublisher` | 当前运行的 Redis Stream 事件发布器 |
| `checkpointer` / `get_workflow_checkpointer()` | `BaseCheckpointSaver[str]` | 当前启用的 Redis 或内存 Checkpointer |
| `graph` / `build_workflow_lifecycle_graph()` | `CompiledStateGraph` | 编译完成的工作流生命周期图 |
| `graph_config` / `workflow_graph_config()` | `Dict[str, Any]` | 包含稳定 `thread_id` 的 LangGraph 调用配置 |
| `workflow_config` / `_parse_config()` | `Dict[str, Any]` | 校验并解析完成的工作流配置快照 |
| `graph_input` | `WorkflowRuntimeState \| Command[Any]` | 首次运行 State 或审批恢复命令 |
| `result` / `graph.ainvoke()` | `Dict[str, Any]` | LangGraph 执行后的完整 State |
| `output` | `str` | 审批拒绝或成功后的输出文本 |
| `error_text` | `str` | 捕获异常后持久化的错误文本 |
