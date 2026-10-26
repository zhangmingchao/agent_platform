# bi.post.profileType_findByProductKey.eec68c38

事件属性列表

- 服务：bi；后端相对路径：`/profileType/findByProductKey`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileTypeController.java:81。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
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
      }
    },
    "additionalProperties": false
  },
  "body_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "string"
      },
      "productKey": {
        "type": "string"
      },
      "appKey": {
        "type": "string"
      },
      "profileName": {
        "type": "string"
      },
      "name": {
        "type": "string"
      },
      "profileType": {
        "type": "string"
      },
      "profileClassify": {
        "type": "integer"
      },
      "propertiesName": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
      },
      "expression": {
        "type": "string"
      },
      "relateType": {
        "type": "integer"
      },
      "eventList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "sample": {
        "type": "integer"
      },
      "isShow": {
        "type": "integer"
      },
      "productKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "appKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "profileNameList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "profileTypeList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "profileClassifyList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "expressSql": {
        "type": "string"
      },
      "searchText": {
        "type": "string"
      },
      "eventNameList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "nameNotNull": {
        "type": "boolean",
        "description": "name 为 null 的时候，是否需要填充name /"
      },
      "tableType": {
        "type": "integer"
      },
      "tableName": {
        "type": "string"
      },
      "language": {
        "type": "string",
        "description": "name 为 null 的时候，是否需要填充name /"
      },
      "idList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      }
    },
    "x-source-type": "ProfileTypeDTO",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/profile/ProfileTypeDTO.java",
      "line": 1
    },
    "required": [
      "eventList",
      "expression",
      "id",
      "name",
      "productKey",
      "profileName",
      "profileType",
      "relateType"
    ]
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
  "frontend_schemas": []
}
```
