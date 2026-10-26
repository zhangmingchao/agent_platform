# bi.get.profileType_setShow.bd58ba86

属性操作

- 服务：bi；后端相对路径：`/profileType/setShow`；方法：GET。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileTypeController.java:156。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer",
        "description": "属性ID"
      },
      "isShow": {
        "type": "integer",
        "description": "属性是否展示"
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
  "frontend_schemas": []
}
```
