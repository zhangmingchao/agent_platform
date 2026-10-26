# bi.get.groupTemplate_checkTemplateUpdate.df1c8bf5

检查模板是否需要更新.true:需要;false:不需要

- 服务：bi；后端相对路径：`/groupTemplate/checkTemplateUpdate`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateController.java:211。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "templateId": {
        "type": "integer"
      }
    },
    "required": [
      "templateId"
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
