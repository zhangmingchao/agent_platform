---
name: BI 元数据查询
description: 使用受控 BiCli 查询指定产品的分析主体、事件、用户属性、事件属性和指标列表。
---

# BI 元数据查询

## 适用场景

用户需要了解 BI 产品中可用的分析主体、事件、用户属性、事件属性或指标时使用本技能。
本技能第一期只支持列表查询，不支持新增、编辑、删除、导出和执行分析。

## 使用工具

使用 `BiCli` 工具。工具参数 `arguments` 必须是字符串数组，不要拼接成一段 Shell 文本。

正确示例：

```json
{
  "arguments": [
    "metadata",
    "events",
    "list",
    "--product-key",
    "app_001",
    "--page-num",
    "1",
    "--page-size",
    "50"
  ]
}
```

不要传入 `bi`、`python`、管道、重定向或其他 Shell 命令。

## 执行规则

1. `product_key` 是所有查询的必填参数。用户没有提供且上下文中也无法确定时，先询问用户，不得猜测。
2. 列表命令默认查询第 1 页、每页 50 条；需要继续查询时再增加页码，单页不得超过 200 条。
3. 用户给出搜索词时使用对应的 `--search-text` 参数，不要先拉取全量数据再由模型过滤。
4. 不得猜测事件、属性、指标或分析主体是否存在，必须以 CLI 返回数据为准。
5. 工具返回 `ok=false` 时先读取 `error.code`：
   - `UNAUTHENTICATED`：说明 BI Token 已过期或未配置，停止重试。
   - `PERMISSION_DENIED`：说明当前 BI 身份没有产品或接口权限，停止重试。
   - `TIMEOUT`、`NETWORK_ERROR`、`RATE_LIMITED`：仅在 `retryable=true` 时最多重试一次。
   - `OUTPUT_TOO_LARGE`：缩小搜索范围或分页大小后重新查询。
6. 回答用户时使用业务名称和标识，不输出 Token、请求头或服务端地址。

## 命令选择

| 用户意图 | CLI 命令 |
| --- | --- |
| 有哪些分析主体、默认分析主体是什么 | `metadata analysis-bodies list` |
| 有哪些事件、查找某个事件 | `metadata events list` |
| 有哪些用户属性 | `metadata user-properties list` |
| 有哪些事件属性 | `metadata event-properties list` |
| 有哪些事件指标 | `metadata metrics list` |

完整参数和示例见 [references/commands.md](references/commands.md)。仅在需要可选筛选参数时读取该参考文件。

## 返回结果

工具统一返回 JSON：

```json
{
  "ok": true,
  "command": "metadata.events.list",
  "requestId": "trace-100",
  "data": {},
  "message": "操作成功",
  "error": null,
  "metadata": {
    "httpStatus": 200,
    "upstreamCode": 200,
    "timeZone": "Asia/Shanghai"
  }
}
```

只使用 `data` 生成业务回答；`metadata` 用于解释时区和排查调用问题。
