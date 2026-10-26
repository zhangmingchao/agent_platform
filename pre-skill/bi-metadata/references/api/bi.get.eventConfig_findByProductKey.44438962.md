# bi.get.eventConfig_findByProductKey.44438962

事件管理列表

- 服务：bi；后端相对路径：`/eventConfig/findByProductKey`；方法：GET。
- 前端路径：/bi-docker/api/eventConfig/findByProductKey。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/EventConfigController.java:80。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:123；方法 manageList；参数类型 `selectType`。

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
      "searchText": {
        "type": "string",
        "description": "搜索内容"
      },
      "eventClassifyArr": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "事件类型"
      },
      "eventName": {
        "type": "string"
      },
      "profileClassifyList": {
        "type": "array",
        "items": {
          "type": "number"
        }
      },
      "profileTypeList": {
        "type": "array",
        "items": {
          "type": "string"
        }
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
