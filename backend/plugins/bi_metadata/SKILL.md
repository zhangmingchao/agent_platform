---
name: bi-metadata
description: 查询指定 BI 产品的分析主体、事件、用户属性、事件属性和指标。
---

# BI 元数据查询

使用 `{{tool:BiCli}}`，工具参数 `arguments` 为字符串数组。调用前确认产品 `product_key`；用户未提供且上下文不能确定时先询问，不得猜测。

```json
{"arguments":["metadata","events","list","--product-key","app_001","--page-num","1","--page-size","50"]}
```

支持 `analysis-bodies`、`events`、`user-properties`、`event-properties`、`metrics` 的 `list` 命令。不要传可执行文件名、Python、Shell、管道或重定向。参数详情见 `references/commands.md`。

优先使用搜索和分页，单页最多 200 条。业务事实必须以实际工具结果为准；不得猜测事件或属性存在。工具结果外层 `ok` 表示调用是否成功，外层 `data` 为 BI CLI 结构化结果，业务数据位于 `data.data`。

失败时读取外层 `error.code`；认证或权限失败停止重试，超时/网络错误需谨慎重试。回答使用业务名称和标识，禁止输出 Token、请求头或服务地址。
