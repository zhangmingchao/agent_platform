# bi.post.profileType_addForexRate.04ad89b2

新增汇率属性

- 服务：bi；后端相对路径：`/profileType/addForexRate`；方法：POST。
- 前端路径：/bi-docker/api/profileType/addForexRate。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileTypeController.java:385。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:68；方法 addForexRate；参数类型 `any`。

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
      "id": {
        "type": "string",
        "description": "@TableName forex_rate_profile_map /"
      },
      "productKey": {
        "type": "string",
        "description": "@TableName forex_rate_profile_map /"
      },
      "appKey": {
        "type": "string",
        "description": "@TableName forex_rate_profile_map /"
      },
      "name": {
        "type": "string",
        "description": "@TableName forex_rate_profile_map /"
      },
      "profileId": {
        "type": "integer",
        "description": "@TableName forex_rate_profile_map /"
      },
      "profileName": {
        "type": "string",
        "description": "@TableName forex_rate_profile_map /"
      },
      "tableType": {
        "type": "integer",
        "description": "@TableName forex_rate_profile_map /"
      },
      "metaProfileName": {
        "type": "string"
      },
      "metaProfileNameText": {
        "type": "string"
      },
      "metaProfileId": {
        "type": "string"
      },
      "calculationMethod": {
        "type": "integer"
      },
      "dynamicCurrencyProfile": {
        "type": "string"
      },
      "dynamicCurrencyProfileText": {
        "type": "string"
      },
      "dynamicCurrencyProfileId": {
        "type": "string"
      },
      "fixedCurrencyType": {
        "type": "string"
      },
      "targetCurrencyType": {
        "type": "string"
      },
      "profileClassify": {
        "type": "integer"
      },
      "createAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "eventList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "eventName": {
              "type": "string"
            },
            "eventClassify": {
              "type": "integer",
              "description": "事件类型。1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 /"
            }
          },
          "x-source-type": "EventSimpleDto",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/dto/event/EventSimpleDto.java",
            "line": 1
          }
        }
      }
    },
    "x-source-type": "ForexRateProfileDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/profile/ForexRateProfileDto.java",
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
