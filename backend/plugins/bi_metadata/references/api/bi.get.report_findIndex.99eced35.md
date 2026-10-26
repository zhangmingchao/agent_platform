# bi.get.report_findIndex.99eced35

事件分析选择框

- 服务：bi；后端相对路径：`/report/findIndex`；方法：GET。
- 前端路径：/bi-docker/api/report/findIndex。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/BehaviorAnalysisReportController.java:507。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:46；方法 findIndex；参数类型 `TGetFindIndex`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "productKey": {
        "type": "string"
      },
      "analysisType": {
        "type": "integer"
      },
      "eventList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string"
            },
            "eventName": {
              "type": "string"
            },
            "eventClassify": {
              "type": "number"
            }
          },
          "required": [
            "eventName",
            "eventClassify"
          ]
        }
      },
      "eventNameList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "eventMetricList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "metricName": {
              "type": "string"
            },
            "category": {
              "type": "number"
            }
          },
          "required": [
            "metricName",
            "category"
          ]
        }
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
          "type": "number"
        }
      },
      "businessModule": {
        "type": "string"
      },
      "showSpec": {
        "anyOf": [
          {
            "type": "boolean",
            "const": false
          },
          {
            "type": "boolean",
            "const": true
          }
        ]
      },
      "eventNameDataType": {
        "type": "number",
        "description": "事件数据类型"
      },
      "immediate": {
        "anyOf": [
          {
            "type": "boolean",
            "const": false
          },
          {
            "type": "boolean",
            "const": true
          }
        ]
      },
      "profileTkio": {
        "anyOf": [
          {
            "type": "boolean",
            "const": false
          },
          {
            "type": "boolean",
            "const": true
          }
        ]
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
