# bi.get.eventConfig_copyEvent.29f1ff66

关联已有事件

- 服务：bi；后端相对路径：`/eventConfig/copyEvent`；方法：GET。
- 前端路径：/bi-docker/api/eventConfig/copyEvent。
- 状态：matched；操作：write；Schema：declared。
- 说明：源码未明确证明只读，使用修改入口；需核实业务意图
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/EventConfigController.java:382。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:159；方法 copyEvent；参数类型 `any`。

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
