# bi.get.profileType_checkProfileName.466e4827

检查属性标识

- 服务：bi；后端相对路径：`/profileType/checkProfileName`；方法：GET。
- 前端路径：/bi-docker/api/profileType/checkProfileName。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileTypeController.java:320。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:55；方法 checkEventVirtualProperty；参数类型 `CheckRequest`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string",
        "description": "产品key"
      },
      "profileName": {
        "type": "string",
        "description": "属性标识"
      },
      "profileClassify": {
        "type": "integer",
        "description": "属性类型"
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
  "backend_type": "ResultModel<CheckResult>",
  "backend_schema": {
    "x-source-type": "ResultModel<CheckResult>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
