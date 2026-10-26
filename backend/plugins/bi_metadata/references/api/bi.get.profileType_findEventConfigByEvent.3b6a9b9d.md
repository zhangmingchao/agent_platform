# bi.get.profileType_findEventConfigByEvent.3b6a9b9d

属性下钻

- 服务：bi；后端相对路径：`/profileType/findEventConfigByEvent`；方法：GET。
- 前端路径：/bi-docker/api/profileType/findEventConfigByEvent。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileTypeController.java:118。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:27；方法 eventSec；参数类型 `attributeType`。

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
      "profileName": {
        "type": "string",
        "description": "属性名称"
      },
      "profileClassify": {
        "type": "integer",
        "description": "属性类型"
      },
      "searchText": {
        "type": "string",
        "description": "搜索内容"
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
      "eventName": {
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
