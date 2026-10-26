# bi.post.profileType_addDimension.b1d1be76

新增维度属性

- 服务：bi；后端相对路径：`/profileType/addDimension`；方法：POST。
- 前端路径：/bi-docker/api/profileType/addDimension。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/ProfileTypeController.java:467。
- 前端源码：solar-engine-fe/src/api/modules/dataManage/index.ts:327；方法 addDimension；参数类型 `any`。

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
      "sourceProfile": {
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
      "dimensionProfiles": {
        "type": "array",
        "items": {
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
        }
      }
    },
    "x-source-type": "DimensionProfileDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/DimensionProfileDto.java",
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
