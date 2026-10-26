# bi.get.userGroup_list.3a33380c

分群列表

- 服务：bi；后端相对路径：`/userGroup/list`；方法：GET。
- 前端路径：/bi-docker/api/userGroup/list。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usergroup/UserGroupController.java:50。
- 前端源码：solar-engine-fe/src/api/modules/userGroup/index.ts:34；方法 list；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string"
      },
      "searchText": {
        "type": "string"
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
      },
      "groupType": {
        "type": "integer"
      },
      "updateType": {
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
  "backend_type": "ResultModel<PageResult<UserGroup>>",
  "backend_schema": {
    "x-source-type": "ResultModel<PageResult<UserGroup>>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
