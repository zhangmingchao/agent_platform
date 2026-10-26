# bi.get.profileUser_setShow.a0c578e3

事件操作

- 服务：bi；后端相对路径：`/profileUser/setShow`；方法：GET。
- 前端路径：/bi-docker/api/profileUser/setShow。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileUserController.java:178。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:86；方法 userSwitch；参数类型 `Ishow`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "description": "用户属性ID"
      },
      "isShow": {
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
