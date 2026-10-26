# bi.get.groupTemplate_ignoreRelationBoard.247a7523

更新关联看板-忽略

- 服务：bi；后端相对路径：`/groupTemplate/ignoreRelationBoard`；方法：GET。
- 前端路径：/bi-docker/api/groupTemplate/ignoreRelationBoard。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateController.java:224。
- 前端源码：solar-engine-fe/src/api/modules/template/index.ts:39；方法 ignoreRelation；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "boardId": {
        "type": "integer"
      }
    },
    "required": [
      "boardId"
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
