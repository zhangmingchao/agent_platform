# bi.post.eventConfig_v2_findAllEventList.eecda189

全量事件-分析面包屑使用

- 服务：bi；后端相对路径：`/eventConfig/v2/findAllEventList`；方法：POST。
- 前端路径：/bi-docker/api/eventConfig/v2/findAllEventList。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/EventConfigController.java:231。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:51；方法 fetchTagEventList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  },
  "body_schema": {
    "type": "object",
    "properties": {
      "eventNameList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "profileClassifyList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "id": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "productKeys": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "productKey": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "productKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "appKey": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "appKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "analysisType": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "eventClassify": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2022/11/3 14:18 /"
      },
      "conditions": {
        "type": "string"
      },
      "entityType": {
        "type": "string"
      },
      "eventClassifyList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "profileTypeList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "eventTypeList": {
        "type": "integer"
      },
      "eventName": {
        "type": "string"
      },
      "name": {
        "type": "string"
      },
      "eventRemark": {
        "type": "string"
      },
      "isShow": {
        "type": "integer"
      },
      "status": {
        "type": "integer"
      },
      "searchText": {
        "type": "string"
      },
      "nameNotNull": {
        "type": "boolean"
      },
      "profileName": {
        "type": "string"
      },
      "profileClassify": {
        "type": "integer"
      },
      "computeType": {
        "type": "integer"
      },
      "showAll": {
        "type": "integer"
      },
      "language": {
        "type": "string"
      },
      "isAppField": {
        "type": "string"
      },
      "fieldName": {
        "type": "string"
      },
      "profileNameAsList": {
        "type": "string"
      },
      "ignoreRule": {
        "type": "integer"
      }
    },
    "x-source-type": "EventBodyDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/event/EventBodyDto.java",
      "line": 1
    }
  },
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
