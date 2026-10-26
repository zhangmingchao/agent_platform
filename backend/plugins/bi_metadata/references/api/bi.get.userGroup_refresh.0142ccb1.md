# bi.get.userGroup_refresh.0142ccb1

刷新条件分群

- 服务：bi；后端相对路径：`/userGroup/refresh`；方法：GET。
- 前端路径：/bi-docker/api/userGroup/refresh。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usergroup/UserGroupController.java:146。
- 前端源码：solar-engine-fe/src/api/modules/userGroup/index.ts:38；方法 refreshConditionGroup；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
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
