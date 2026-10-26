# bi.get.userGroup_getGroupUserList.040f21f0

回调分群执行

- 服务：bi；后端相对路径：`/userGroup/getGroupUserList`；方法：GET。
- 前端路径：/bi-docker/api/userGroup/getGroupUserList。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usergroup/UserGroupController.java:173。
- 前端源码：solar-engine-fe/src/api/modules/userGroup/index.ts:10；方法 getGroupUserList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer",
        "description": "分群ID"
      },
      "pageNum": {
        "type": "integer",
        "minimum": 1,
        "default": 1
      },
      "pageSize": {
        "type": "integer",
        "minimum": 1,
        "default": 50,
        "maximum": 200
      }
    },
    "required": [
      "id",
      "pageNum",
      "pageSize"
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
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
