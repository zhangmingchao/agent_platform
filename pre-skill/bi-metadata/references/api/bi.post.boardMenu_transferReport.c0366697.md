# bi.post.boardMenu_transferReport.c0366697

transferReport

- 服务：bi；后端相对路径：`/boardMenu/transferReport`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:300。

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
      "ids": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "model": {
        "type": "string"
      },
      "transferFromUserId": {
        "type": "integer",
        "description": "被转移人 /"
      },
      "transferToUserId": {
        "type": "integer",
        "description": "资源接收人 /"
      },
      "transferToUserRoleId": {
        "type": "integer",
        "description": "资源接收人 /"
      },
      "userTenant": {
        "type": "string",
        "description": "租户id /"
      },
      "denies": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "resourceId": {
              "type": "integer"
            },
            "resourceType": {
              "type": "integer"
            },
            "resourceIndex": {
              "type": "string"
            },
            "resourceTenant": {
              "type": "string"
            },
            "resourceName": {
              "type": "string"
            },
            "resourceDesc": {
              "type": "string"
            },
            "resourceExt": {
              "type": "string"
            },
            "parentResourceId": {
              "type": "integer"
            },
            "resourceUpdater": {
              "type": "string"
            },
            "allowActionType": {
              "type": "integer"
            }
          },
          "x-source-type": "ResSaveDto",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/sso/dto/ResSaveDto.java",
            "line": 1
          }
        },
        "description": "不允许转移的资源 /"
      },
      "allows": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "resourceId": {
              "type": "integer"
            },
            "resourceType": {
              "type": "integer"
            },
            "resourceIndex": {
              "type": "string"
            },
            "resourceTenant": {
              "type": "string"
            },
            "resourceName": {
              "type": "string"
            },
            "resourceDesc": {
              "type": "string"
            },
            "resourceExt": {
              "type": "string"
            },
            "parentResourceId": {
              "type": "integer"
            },
            "resourceUpdater": {
              "type": "string"
            },
            "allowActionType": {
              "type": "integer"
            }
          },
          "x-source-type": "ResSaveDto",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/sso/dto/ResSaveDto.java",
            "line": 1
          }
        },
        "description": "仅允许转移的资源 /"
      },
      "userUpdater": {
        "type": "string",
        "description": "操作者 /"
      },
      "transferIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "操作者 /"
      },
      "loginUserId": {
        "type": "integer",
        "description": "操作者 /"
      },
      "isDepriveUser": {
        "type": "boolean",
        "description": "操作者 /"
      }
    },
    "x-source-type": "PropertyTransferVo",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/PropertyTransferVo.java",
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
  "frontend_schemas": []
}
```
