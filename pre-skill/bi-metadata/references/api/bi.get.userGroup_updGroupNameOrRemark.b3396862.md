# bi.get.userGroup_updGroupNameOrRemark.b3396862

分群详情

- 服务：bi；后端相对路径：`/userGroup/updGroupNameOrRemark`；方法：GET。
- 前端路径：/bi-docker/api/userGroup/updGroupNameOrRemark。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usergroup/UserGroupController.java:74。
- 前端源码：solar-engine-fe/src/api/modules/userGroup/index.ts:42；方法 updGroupNameOrRemark；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "updFieldName": {
        "type": "string",
        "description": "需要修改的字段名称"
      },
      "updContent": {
        "type": "string",
        "description": "需要修改的内容"
      },
      "id": {
        "type": "integer",
        "description": "需要修改的分群ID"
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
  "backend_type": "ResultModel<String>",
  "backend_schema": {
    "x-source-type": "ResultModel<String>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
