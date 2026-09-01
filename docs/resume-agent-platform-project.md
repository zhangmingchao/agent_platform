# Agent Platform 项目简历说明

## 项目名称

Agent Platform——企业级 AI Agent 开发与工作流编排平台

## 项目简介

基于 LangChain、LangGraph、FastAPI 和 Vue 3 构建的 AI Agent 开发平台，支持 Agent 配置、动态工具接入、多模态对话、结构化输出、Python 隔离执行、多 Agent 工作流编排、人工审批及全链路追踪。平台通过 MySQL、MongoDB、Redis Stream 和容器化 Sandbox 实现业务数据持久化、运行事件分发、代码安全执行及调用链观测。

## 1. 技术栈

### 后端与 Agent 框架

- Python、FastAPI、Uvicorn、Pydantic
- LangChain、LangGraph、OpenAI-compatible API
- ReAct Agent、Tool Calling、StructuredTool
- SSE 流式响应、异步编程、后台任务

### 数据与消息组件

- MySQL：用户、Agent、会话、工作流及运行结果持久化
- MongoDB：Trace Span 和调用链明细存储
- Redis：登录状态、运行锁、Runtime 任务队列和工作流事件流
- Redis Stream：工作流事件持久化、SSE 订阅及断线续读

### 工具与代码执行

- MCP Streamable HTTP、JSON-RPC 2.0
- Skill 插件体系、`SKILL.md`、HTTP Action
- Python Runtime Worker、Sandbox Service
- Docker 用户隔离容器、受限代码执行
- pandas、NumPy、openpyxl、Matplotlib、python-docx、pypdf

### 前端

- Vue 3、Vue Router、Pinia
- Element Plus、Axios
- Vue Flow：DAG 工作流可视化编排
- Markdown-It、DOMPurify

## 2. 功能描述

### Agent 配置与运行

- 支持 Agent 创建、编辑和删除，可配置系统提示词、模型、温度、最大工具迭代次数、Skill 和 MCP 工具。
- 支持自定义提示词模板，在运行时注入用户输入、用户名、用户 ID、会话 ID、日期及工作流上下文变量。
- 支持 Python/Pydantic 风格结构定义与 JSON Schema 双向转换，对模型输出进行解析、校验和结构化持久化。
- 基于 LangGraph ReAct Agent 实现多轮模型推理、工具选择、工具执行和结果回传。

### 会话、记忆与多模态

- 基于 MySQL 持久化多轮会话历史，服务重启后仍可恢复聊天上下文。
- 使用 LangGraph `InMemorySaver` 保存单轮 Graph 执行状态，并通过独立 `thread_id` 隔离每次运行。
- 支持图片 Base64 多模态输入，以及 Excel、CSV、Word、PDF、JSON、Markdown 等文件上传。
- 支持生成文件 Artifact 的登记、鉴权下载和历史消息展示。

### Skill 与 MCP 工具体系

- 支持上传包含 `SKILL.md`、参考资料和脚本的 Skill ZIP 包，并提供在线编辑和预览能力。
- 支持通过 `skill.json` 声明 HTTP Action，动态转换成 LangChain 结构化工具。
- 支持 MCP Server 配置、工具动态发现、参数 Schema 转换、在线调试及 Agent 自动调用。

### Python Runtime

- 为 Agent 提供 `ExecutePython` 和 `RunSkillScript` 工具，支持动态代码及固定 Skill 脚本执行。
- 采用 API、Redis Queue、Runtime Worker、Sandbox Service 和 Docker 用户容器分层架构。
- 支持代码静态策略校验、用户文件隔离、资源限制、执行超时、网络限制和只读文件系统。
- 支持 Excel 数据分析、文档解析、图表生成和结果文件导出。

### 多 Agent 工作流

- 基于 Vue Flow 提供可视化 DAG 编排，支持 Agent、条件、并行、人工确认和输出节点。
- 支持节点输入输出传递、条件路由、并行分支执行及结果合并。
- 支持人工审批暂停，审批状态和恢复位置持久化到 MySQL；批准后继续执行，拒绝后终止工作流。
- 使用 Redis Stream 发布工作流事件，支持 SSE 实时展示和按事件游标恢复订阅。

### 可观测性

- 建立覆盖聊天和工作流的 Trace 体系，记录 LLM、Tool、Runtime 和工作流步骤之间的关联关系。
- 记录模型输入输出、工具参数、执行结果、错误、Token 数量及耗时信息。
- 设计按 LLM 轮次分类的流式事件协议，将执行说明、正式回答和工具事件分离展示和持久化。

## 3. 主要职责

- 负责 AI Agent 平台的整体架构设计与核心模块开发，完成从 Agent 配置、模型调用、工具执行到结果持久化的完整链路。
- 基于 LangChain StructuredTool 和 LangGraph ReAct Agent 设计统一工具调用机制，整合 Skill、MCP、HTTP Action 和 Python Runtime。
- 设计自定义提示词模板系统，实现运行时变量渲染，并兼容单 Agent 会话与多 Agent 工作流上下文。
- 设计结构化输出能力，支持 Python/Pydantic 风格描述转换为 JSON Schema，并对模型结果进行安全解析和校验。
- 设计 MySQL 长期会话记忆与 LangGraph Checkpoint 相结合的状态管理方案，避免历史消息和内存状态重复叠加。
- 负责 Python Runtime 执行架构，实现 Redis 任务队列、独立 Worker、Sandbox Service 和用户级 Docker 容器隔离。
- 设计 Runtime 文件与 Artifact 生命周期，实现文件上传、权限校验、沙箱输入映射、结果登记和鉴权下载。
- 负责多 Agent DAG 工作流引擎，完成顺序执行、条件分支、并行分支、人工审批、恢复执行和输出汇总。
- 设计 Redis Stream 工作流事件协议，实现后台执行与浏览器连接解耦、SSE 实时推送和断线续读。
- 建设 Trace 可观测体系，打通会话、工作流、LLM、Tool 和 Runtime 执行链路，提升问题定位和运行审计能力。
- 负责 Vue 3 管理端和工作流可视化界面开发，实现 Agent 管理、聊天、文件上传、运行状态展示及审批操作。
- 编写核心模块测试和技术文档，覆盖结构化输出、流式事件、Runtime 队列、Sandbox 调用及人工审批等关键流程。

## 简历精简版

**Agent Platform｜AI Agent 平台开发**

技术栈：Python、FastAPI、LangChain、LangGraph、Vue 3、MySQL、MongoDB、Redis、Docker、MCP、SSE。

- 负责企业级 AI Agent 平台设计与开发，支持自定义提示词模板、结构化输出、多轮 Tool Calling、多模态输入和持久化会话记忆。
- 构建 Skill、MCP、HTTP Action 统一工具生态，实现工具动态发现、参数 Schema 转换和 Agent 自动调用。
- 设计隔离式 Python Runtime，通过 Redis Queue、独立 Worker、Sandbox Service 和用户级 Docker 容器安全执行模型生成代码，支持 Excel/PDF/Word 数据处理及 Artifact 输出。
- 实现多 Agent DAG 工作流，支持条件分支、并行执行、人工审批、恢复运行和 Redis Stream 实时事件订阅。
- 建设覆盖 LLM、Tool、Runtime 和工作流节点的 Trace 体系，实现输入输出、异常、Token 和耗时的全链路观测。

