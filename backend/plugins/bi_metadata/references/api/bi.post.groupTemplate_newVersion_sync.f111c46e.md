# bi.post.groupTemplate_newVersion_sync.f111c46e

模板同步-更新

- 服务：bi；后端相对路径：`/groupTemplate/newVersion/sync`；方法：POST。
- 前端路径：/bi-docker/api/groupTemplate/newVersion/sync。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateController.java:107。
- 前端源码：solar-engine-fe/src/api/modules/board/index.ts:28；方法 syncTemplate；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  },
  "body_schema": {
    "type": "object",
    "additionalProperties": {
      "x-source-type": "Object",
      "x-unresolved": "动态 JSON，参数形状需查调用页面"
    }
  },
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
