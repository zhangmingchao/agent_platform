# bi.get.eventConfig_delete.9e8487b2

删除虚拟事件

- 服务：bi；后端相对路径：`/eventConfig/delete`；方法：GET。
- 前端路径：/bi-docker/api/eventConfig/delete。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/EventConfigController.java:317。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:135；方法 manageDelete；参数类型 `Idelete`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "description": "事件id"
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
