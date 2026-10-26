# bi.post.report_v3_findProfilesByEvents.b5904bd7

条件标签筛选属性列表

- 服务：bi；后端相对路径：`/report/v3/findProfilesByEvents`；方法：POST。
- 前端路径：/bi-docker/api/report/v3/findProfilesByEvents。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/BehaviorAnalysisReportController.java:590。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:62；方法 fetchTagPropertyList；参数类型 `any`。

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
      "productKey": {
        "type": "string",
        "description": "desc: date: 2022/6/2 7:42 下午 user: 顾炜[Weier Gu] /"
      },
      "productKeys": {
        "type": "string",
        "description": "desc: date: 2022/6/2 7:42 下午 user: 顾炜[Weier Gu] /"
      },
      "productKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "desc: date: 2022/6/2 7:42 下午 user: 顾炜[Weier Gu] /"
      },
      "appKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "desc: date: 2022/6/2 7:42 下午 user: 顾炜[Weier Gu] /"
      },
      "eventNameList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "desc: date: 2022/6/2 7:42 下午 user: 顾炜[Weier Gu] /"
      },
      "eventNameDataType": {
        "type": "integer",
        "description": "desc: date: 2022/6/2 7:42 下午 user: 顾炜[Weier Gu] /"
      },
      "eventList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "eventName": {
              "type": "string",
              "description": "虚拟事件标识 /"
            },
            "eventClassify": {
              "type": "integer",
              "description": "事件类型。1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 /"
            }
          },
          "x-source-type": "EventConfigQueryVo",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/vo/EventConfigQueryVo.java",
            "line": 1
          }
        }
      },
      "eventMetricList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer"
            },
            "userId": {
              "type": "integer"
            },
            "productKey": {
              "type": "string"
            },
            "category": {
              "type": "integer"
            },
            "metricName": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "remark": {
              "type": "string"
            },
            "metricCondition": {
              "type": "string"
            },
            "status": {
              "type": "integer"
            },
            "createAt": {
              "type": "string",
              "description": "日期格式按调用页面/后端约定，不能推测时区"
            },
            "updateAt": {
              "type": "string",
              "description": "日期格式按调用页面/后端约定，不能推测时区"
            },
            "removeStatus": {
              "type": "integer"
            },
            "searchText": {
              "type": "string"
            },
            "sortFieldName": {
              "type": "string"
            },
            "sortType": {
              "type": "integer"
            },
            "isGetAll": {
              "type": "boolean",
              "description": "是否查询所有可见指标 /"
            },
            "isCollect": {
              "type": "integer",
              "description": "是否收藏 /"
            },
            "productKeyList": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "是否收藏 /"
            },
            "currentTimeZoneOffset": {
              "type": "string",
              "description": "是否收藏 /"
            }
          },
          "x-source-type": "EventMetricDto",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/dto/datamanage/EventMetricDto.java",
            "line": 1
          }
        }
      },
      "profileName": {
        "type": "string"
      },
      "type": {
        "type": "integer"
      },
      "analysisType": {
        "type": "integer"
      },
      "dimension": {
        "type": "integer"
      },
      "id": {
        "type": "string"
      },
      "profileTypes": {
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
      "businessModule": {
        "type": "string"
      },
      "entityType": {
        "type": "string"
      },
      "showSpec": {
        "type": "boolean"
      },
      "computeType": {
        "type": "integer"
      },
      "showAll": {
        "type": "integer"
      },
      "route": {
        "type": "string"
      },
      "boardId": {
        "type": "integer"
      },
      "profileClassify": {
        "type": "integer"
      },
      "profileTkio": {
        "type": "boolean"
      }
    },
    "x-source-type": "ProfileValueVo",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/ProfileValueVo.java",
      "line": 1
    },
    "required": [
      "productKey"
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
