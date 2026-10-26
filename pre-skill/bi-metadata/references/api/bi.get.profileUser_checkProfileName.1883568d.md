# bi.get.profileUser_checkProfileName.1883568d

检查属性标识

- 服务：bi；后端相对路径：`/profileUser/checkProfileName`；方法：GET。
- 前端路径：/bi-docker/api/profileUser/checkProfileName。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileUserController.java:260。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:110；方法 checkUserVirtualProperty；参数类型 `CheckRequest`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string",
        "description": "产品code"
      },
      "profileName": {
        "type": "string",
        "description": "属性标志"
      },
      "profileClassify": {
        "type": "integer",
        "description": "事件类型"
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
  "backend_type": "ResultModel<Boolean>",
  "backend_schema": {
    "x-source-type": "ResultModel<Boolean>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
