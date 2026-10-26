# bi.get.groupTemplateRelation_checkRelationBoardUpdate.2a47c1fe

检查关联看板是否需要更新.true:需要;false:不需要

- 服务：bi；后端相对路径：`/groupTemplateRelation/checkRelationBoardUpdate`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateRelationController.java:44。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "board": {
        "type": "integer"
      }
    },
    "required": [
      "board"
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
  "frontend_schemas": []
}
```
