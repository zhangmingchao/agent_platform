# bi.get.eventConfig_findProfileTypeByEvent.3230d60c

事件下钻

- 服务：bi；后端相对路径：`/eventConfig/findProfileTypeByEvent`；方法：GET。
- 前端路径：/bi-docker/api/eventConfig/findProfileTypeByEvent。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/EventConfigController.java:113。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:139；方法 manageSec；参数类型 `attributeType`。

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
      },
      "searchText": {
        "type": "string",
        "description": "搜索内容"
      },
      "pageNum": {
        "type": "integer",
        "description": "页码",
        "minimum": 1,
        "default": 1
      },
      "pageSize": {
        "type": "integer",
        "description": "页数",
        "minimum": 1,
        "default": 50,
        "maximum": 200
      },
      "profileName": {
        "type": "string"
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
