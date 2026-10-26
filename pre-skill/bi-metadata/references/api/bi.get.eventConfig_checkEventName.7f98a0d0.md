# bi.get.eventConfig_checkEventName.7f98a0d0

检查虚拟事件/自定义事件

- 服务：bi；后端相对路径：`/eventConfig/checkEventName`；方法：GET。
- 前端路径：/bi-docker/api/eventConfig/checkEventName。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/EventConfigController.java:363。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:143；方法 checkEventName；参数类型 `CheckVirtualEventNameRequest`。

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
      "eventName": {
        "type": "string",
        "description": "事件名称"
      },
      "eventClassify": {
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
  "backend_type": "ResultModel<CheckResult>",
  "backend_schema": {
    "x-source-type": "ResultModel<CheckResult>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
