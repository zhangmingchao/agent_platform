# bi.get.boardLog_list.b6e9ef19

日志列表

- 服务：bi；后端相对路径：`/boardLog/list`；方法：GET。
- 前端路径：/bi-docker/api/boardLog/list。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardLogController.java:34。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:187；方法 getBoardLog；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "boardId": {
        "type": "integer"
      },
      "0": {
        "type": "integer",
        "default": 0
      },
      "20": {
        "type": "integer",
        "default": 20
      }
    },
    "additionalProperties": false
  },
  "body_schema": null,
  "path_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

返回声明：

```json
{
  "backend_type": "ResultModel<PageResultModel<LogInfo>>",
  "backend_schema": {
    "x-source-type": "ResultModel<PageResultModel<LogInfo>>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
