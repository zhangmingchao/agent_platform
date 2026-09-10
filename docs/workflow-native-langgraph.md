# 动态工作流原生 LangGraph 升级

## 最终方向

工作流执行主链采用“前端配置动态编译为原生 LangGraph”的方案，不再由外层单一
`execute` 节点代理整张自研 DAG。

```text
前端 nodes / edges
        ↓
NativeWorkflowEngine.compile()
        ↓
StateGraph.add_node / add_edge / add_conditional_edges
        ↓
CompiledStateGraph + Redis Checkpointer
```

## 节点映射

| 前端节点 | LangGraph 实现 |
| --- | --- |
| input/start | 原生透传节点 |
| agent | 原生异步节点，调用 Agent、Skill、MCP，并写入节点输出 State |
| condition | 原生 `add_conditional_edges()` |
| parallel | 多条原生出边并发调度 |
| approval | 幂等准备节点 + 原生 `interrupt()` 节点 |
| output | 原生终态节点，生成最终输出 |

## State 设计

`NativeWorkflowState.node_outputs` 按节点 ID 保存结果，并使用字典合并 reducer：

```python
node_outputs: Annotated[Dict[str, str], operator.or_]
```

并行分支不会同时覆盖同一个 `current_input`。公共汇合点按照配置中的入边顺序读取所有
前驱输出，并使用分隔线合并后传给下一个节点。

## 人工审批

审批节点被编译为两个节点：

```text
approval__prepare → approval(interrupt) → 后续节点 / END
```

- `approval__prepare` 负责写 MySQL 步骤、恢复上下文和 Redis Stream 事件。
- `approval` 只负责 `interrupt()` 和处理 `Command(resume=...)`。
- LangGraph 恢复时从 interrupt 节点重新进入，不会重复插入审批步骤。

## Checkpoint 版本

原生动态图使用：

```text
workflow_run_v2_{run_id}
```

该命名空间与旧版外层生命周期图隔离，防止新图读取不兼容的历史 Checkpoint。旧运行记录
不做恢复兼容，需要重新创建运行。

## 当前执行入口

`resume_workflow_graph()` 会读取运行记录配置快照，创建 `NativeWorkflowEngine`，动态编译图，
然后调用 `graph.ainvoke()`。`_walk_graph()` 不再处于工作流运行主链，仅保留为待删除的旧实现。
