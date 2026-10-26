# bi.post.profileUser_findUserProfileArithList.504b8f9a

用户分析 获取属性&计算方式列表

- 服务：bi；后端相对路径：`/profileUser/findUserProfileArithList`；方法：POST。
- 前端路径：/bi-docker/api/profileUser/findUserProfileArithList。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileUserController.java:67。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:39；方法 fetchUserAnalysisPropertyArithList；参数类型 `Pick<TFetchPropertyArithListParams, "productKey" | "analysisType" | "entityType">`。

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
      "type": "object",
      "properties": {
        "arithList": {
          "type": "object",
          "properties": {},
          "additionalProperties": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "type": "number"
                },
                "name": {
                  "type": "string"
                },
                "profileType": {
                  "type": "string"
                },
                "type": {
                  "type": "number"
                },
                "enName": {
                  "type": "string"
                }
              },
              "required": [
                "id",
                "name",
                "profileType",
                "type"
              ]
            }
          }
        },
        "profileList": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": {
                "type": "string"
              },
              "name": {
                "type": "string"
              },
              "funcSql": {
                "type": "string"
              },
              "profileName": {
                "type": "string"
              },
              "profileClassify": {
                "type": "string"
              },
              "profileType": {
                "type": "string"
              },
              "ariths": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "id": {
                      "type": "number"
                    },
                    "name": {
                      "type": "string"
                    },
                    "profileType": {
                      "type": "string"
                    },
                    "type": {
                      "type": "number"
                    },
                    "enName": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "id",
                    "name",
                    "profileType",
                    "type"
                  ]
                }
              }
            },
            "required": [
              "id",
              "name"
            ]
          }
        }
      },
      "required": [
        "arithList",
        "profileList"
      ]
    }
  ]
}
```
