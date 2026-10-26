# bi.get.boardMenu_getBoardInfoById.2338436b

修改看板-数据回显接口

- 服务：bi；后端相对路径：`/boardMenu/getBoardInfoById`；方法：GET。
- 前端路径：/bi-docker/api/boardMenu/getBoardInfoById。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:231。
- 前端源码：solar-engine-fe/src/api/modules/panel/index.ts:19；方法 getMenuById；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "boardMenuId": {
        "type": "integer",
        "description": "看板id"
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
