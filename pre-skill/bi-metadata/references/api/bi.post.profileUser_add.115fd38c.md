# bi.post.profileUser_add.115fd38c

新增虚拟属性

- 服务：bi；后端相对路径：`/profileUser/add`；方法：POST。
- 前端路径：/bi-docker/api/profileUser/add。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileUserController.java:188。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:98；方法 addUserVirtualProperty；参数类型 `AddRequest`。

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
        "description": "@Min(value = 1, message = \"必须大于0\", groups = {Update.class})"
      },
      "productKey": {
        "type": "string",
        "description": "@Min(value = 1, message = \"必须大于0\", groups = {Update.class})"
      },
      "appKey": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
      },
      "profileName": {
        "type": "string",
        "description": "@Min(value = 1, message = \"必须大于0\", groups = {Update.class})"
      },
      "name": {
        "type": "string",
        "description": "@Min(value = 1, message = \"必须大于0\", groups = {Update.class})"
      },
      "profileType": {
        "type": "string",
        "description": "@Min(value = 1, message = \"必须大于0\", groups = {Update.class})"
      },
      "profileClassify": {
        "type": "integer",
        "description": "@Min(value = 1, message = \"必须大于0\", groups = {Update.class})"
      },
      "propertiesName": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
      },
      "expression": {
        "type": "string",
        "description": "profile_name 是否 映射到 name /"
      },
      "relateType": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
      },
      "eventList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "sample": {
        "type": "integer",
        "description": "profile_name 是否 映射到 name /"
      },
      "isShow": {
        "type": "integer"
      },
      "productKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "@Min(value = 1, message = \"必须大于0\", groups = {Update.class})"
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
        "type": "boolean"
      },
      "tableType": {
        "type": "integer"
      },
      "tableName": {
        "type": "string"
      },
      "language": {
        "type": "string",
        "description": "profile_name 是否 映射到 name /"
      },
      "idList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "nameAs": {
        "type": "boolean",
        "description": "profile_name 是否 映射到 name /"
      }
    },
    "x-source-type": "ProfileUserDTO",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/profile/ProfileUserDTO.java",
      "line": 1
    },
    "required": [
      "expression",
      "id",
      "name",
      "productKey",
      "profileName",
      "profileType"
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
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
