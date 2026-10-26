# bi.get.profileUser_detail.204f7556

查询属性信息

- 服务：bi；后端相对路径：`/profileUser/detail`；方法：GET。
- 前端路径：/bi-docker/api/profileUser/detail。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileUserController.java:243。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:106；方法 userVirtualPropertyDetail；参数类型 `DetailRequest`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "description": "属性ID"
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
