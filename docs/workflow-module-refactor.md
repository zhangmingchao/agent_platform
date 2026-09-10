# 工作流模块拆分与实体化

## 实现方案

原 `workflow_service.py` 同时承担配置解析、图查询、数据库转换、定义 CRUD 和执行编排。
本次按职责拆分为：

```text
backend/
├── core/workflow_graph.py
│   └── 配置解析、步骤校验、节点/边查询、条件路由、并行汇合点
├── models/workflow.py
│   └── WorkflowDefinition、WorkflowRun、WorkflowResumeContext
├── repositories/workflow_repository.py
│   └── 数据库 Mapping 到领域实体的转换
├── services/workflow_definition_service.py
│   └── 工作流定义的校验和 CRUD
└── services/workflow_service.py
    └── Agent/审批业务回调、运行状态落库和旧执行器隔离
```

原生动态编译器位于 `core/workflow_native_engine.py`，当前工作流运行主链已经使用该编译器；
`_walk_graph()` 不再被 `resume_workflow_graph()` 调用。

## 实体边界

- Repository 必须返回工作流实体，数据库字典不得直接进入执行主链。
- `WorkflowRun.workflow_config` 保存创建运行时冻结的配置快照。
- `WorkflowResumeContext` 使用属性表达审批暂停和恢复现场。
- 仅在 HTTP 服务边界使用 `to_dict()` 保持现有前端协议兼容。

## Checkpointer 约束

工作流人工审批依赖持久化 Checkpoint。`AsyncRedisSaver` 初始化失败时应用直接启动失败，
任何环境都不会回退到内存 Checkpointer。
