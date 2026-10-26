# bi.get.profileUser_findAllMeta.47042e98

用户元属性

- 服务：bi；后端相对路径：`/profileUser/findAllMeta`；方法：GET。
- 前端路径：/bi-docker/api/profileUser/findAllMeta。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileUserController.java:285。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:118；方法 getAllUserProperty；参数类型 `GetAllUserPropertyRequest`。

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
      "profileClassify": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "number"
          }
        ]
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
