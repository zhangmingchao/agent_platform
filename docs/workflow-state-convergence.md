# 工作流 State 收敛说明

## 改造前

项目同时存在 `WorkflowRuntimeState` 和 `NativeWorkflowState`：

- `WorkflowRuntimeState` 服务于旧的 `execute → approval` 外层生命周期图；
- `NativeWorkflowState` 服务于前端节点动态编译的原生 LangGraph。

两套 State 会导致审批恢复、Checkpoint 字段和节点输出存在重复定义。

## 改造后

当前只保留 `NativeWorkflowState`，位于：

```text
backend/core/workflow_native_engine.py
```

工作流运行统一使用：

```text
NativeWorkflowEngine
    ↓
CompiledStateGraph
    ↓
NativeWorkflowState
```

核心字段：

- `run_id`、`workflow_id`、`user_id`：运行身份；
- `workflow_config`：运行创建时冻结的配置快照；
- `initial_input`：工作流初始输入；
- `node_outputs`：按节点 ID 保存输出，支持并行 reducer 合并；
- `status`、`output`：运行状态和最终输出；
- `approval_status`、`approval_payload`、`approval_input`：人工审批暂停与恢复。

## 兼容边界

旧的 `_walk_graph()`、`_execute_dag()`、`_run_workflow_segment()` 和
`build_workflow_lifecycle_graph()` 已从工作流执行主链及源码中删除，不再兼容旧图的
Checkpoint。工作流使用 `workflow_run_v2_{run_id}` 作为线程 ID，旧运行记录需要重新创建。

## 结果

- 节点执行、条件路由、并行汇合和审批恢复均由原生 LangGraph 调度；
- State 定义唯一，后续新增字段只需修改一个模型；
- `workflow_graph.py` 保留为纯配置解析和校验工具，不负责运行调度。
