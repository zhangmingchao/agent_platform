# bi.get.eventConfig_v2_setShow.f896d2f5

事件操作

- 服务：bi；后端相对路径：`/eventConfig/v2/setShow`；方法：GET。
- 前端路径：/bi-docker/api/eventConfig/v2/setShow。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/EventConfigController.java:172。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:127；方法 manageSwitch；参数类型 `Ishow`。

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
        "description": "事件标识"
      },
      "eventClassify": {
        "type": "integer",
        "description": "事件类型"
      },
      "isShow": {
        "type": "integer",
        "description": "是否显示"
      },
      "id": {
        "type": "number"
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
