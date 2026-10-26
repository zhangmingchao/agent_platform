# bi.get.profileType_findAllEventProfList.9735f841

用户属性列表全量

- 服务：bi；后端相对路径：`/profileType/findAllEventProfList`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileTypeController.java:437。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string",
        "description": "产品Key"
      },
      "profileClassifyList": {
        "type": "string",
        "description": "属性类型"
      },
      "entityType": {
        "type": "string",
        "description": "entityType"
      },
      "eventName": {
        "type": "string"
      },
      "eventClassify": {
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
  "backend_type": "ResultModel<Map<String, Object>>",
  "backend_schema": {
    "x-source-type": "ResultModel<Map<String, Object>>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": []
}
```
