# bi.get.boardMenu_saveLog.dee0330d

记录看板操作

- 服务：bi；后端相对路径：`/boardMenu/saveLog`；方法：GET。
- 前端路径：/bi-docker/api/boardMenu/saveLog。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:314。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:78；方法 saveLog；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "boardId": {
        "type": "integer"
      },
      "operateType": {
        "type": "string"
      }
    },
    "required": [
      "boardId",
      "operateType"
    ],
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
  "backend_type": "ResultModel<Object>",
  "backend_schema": {
    "x-source-type": "ResultModel<Object>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
