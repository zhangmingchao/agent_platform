# bi.get.boardMenu_updateDefault.1f1fd4c2

设置/删除默认看板

- 服务：bi；后端相对路径：`/boardMenu/updateDefault`；方法：GET。
- 前端路径：/bi-docker/api/boardMenu/updateDefault。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:322。
- 前端源码：solar-engine-fe/src/api/modules/panel/index.ts:88；方法 updateDefault；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string"
      },
      "boardId": {
        "type": "integer"
      },
      "type": {
        "type": "integer"
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
