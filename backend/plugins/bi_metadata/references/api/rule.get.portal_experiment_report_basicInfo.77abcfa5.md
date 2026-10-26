# rule.get.portal_experiment_report_basicInfo.77abcfa5

ReportBasicInfo 报告基础信息

- 服务：rule；后端相对路径：`/portal/experiment/report/basicInfo`；方法：GET。
- 前端路径：/portal/ab/experiment/report/basicInfo。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:161。
- 后端源码：rule/router/experiment/experiment_report.go:16。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:145；方法 getBasicInfo；参数类型 `TestId`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "experimentId": {
        "type": "number"
      }
    },
    "required": [
      "experimentId"
    ],
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
  "backend_type": "e.Response {code,msg,data,trace,timeZone}",
  "backend_schema": {
    "type": "object",
    "properties": {
      "code": {
        "type": "integer"
      },
      "msg": {
        "type": "string"
      },
      "data": {},
      "trace": {
        "type": "string"
      },
      "timeZone": {
        "type": "string"
      }
    }
  },
  "frontend_schemas": [
    {
      "type": "object",
      "properties": {
        "experimentId": {
          "type": "number"
        },
        "appId": {
          "anyOf": [
            {
              "type": "number"
            },
            {
              "type": "string",
              "const": ""
            }
          ]
        },
        "startDate": {
          "type": "string",
          "description": "试验运行开始时间"
        },
        "endDate": {
          "type": "string",
          "description": "试验运行截至/截至时间"
        },
        "startDateTz": {
          "type": "string"
        },
        "endDateTz": {
          "type": "string"
        },
        "timeType": {
          "anyOf": [
            {
              "type": "number",
              "const": 1
            },
            {
              "type": "number",
              "const": 2
            }
          ]
        },
        "experimentName": {
          "type": "string",
          "description": "试验名称"
        },
        "refreshDate": {
          "type": "string",
          "description": "试验报告数据刷新时间"
        },
        "status": {
          "type": "number",
          "description": "试验状态"
        },
        "coreInd": {
          "type": "string",
          "description": "核心指标key"
        },
        "coreName": {
          "type": "string",
          "description": "核心指标名称"
        },
        "indicatorList": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "key": {
                "type": "string",
                "description": "指标key"
              },
              "name": {
                "type": "string",
                "description": "指标对应名称"
              },
              "iconfont": {
                "type": "string",
                "description": "可能存在的图标"
              },
              "isPercent": {
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
            "required": [
              "key",
              "name"
            ]
          },
          "description": "指标下拉列表数据"
        },
        "startEvent": {
          "type": "object",
          "properties": {
            "eventName": {
              "type": "string",
              "description": "事件标识名称"
            },
            "name": {
              "type": "string",
              "description": "事件名称"
            }
          },
          "required": [
            "eventName",
            "name"
          ],
          "description": "进组事件"
        },
        "retentionEvent": {
          "type": "object",
          "properties": {
            "eventName": {
              "type": "string",
              "description": "事件标识名称"
            },
            "name": {
              "type": "string",
              "description": "事件名称"
            }
          },
          "required": [
            "eventName",
            "name"
          ],
          "description": "留存事件 - 可选"
        },
        "tableNames": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "key": {
                "type": "string",
                "description": "列 key / dataIndex"
              },
              "name": {
                "type": "string",
                "description": "列名称"
              },
              "isPercent": {
                "type": "boolean"
              }
            },
            "required": [
              "key",
              "name",
              "isPercent"
            ]
          },
          "description": "表头"
        },
        "expGroupInfo": {
          "type": "object",
          "properties": {
            "id": {
              "type": "number",
              "description": "试验分组主键Id"
            },
            "name": {
              "type": "string",
              "description": "试验分组名称"
            }
          },
          "required": [
            "id",
            "name"
          ],
          "description": "试验分组信息"
        }
      },
      "required": [
        "experimentId",
        "appId",
        "startDate",
        "endDate",
        "startDateTz",
        "endDateTz",
        "experimentName",
        "refreshDate",
        "status",
        "coreInd",
        "coreName",
        "indicatorList",
        "startEvent",
        "tableNames",
        "expGroupInfo"
      ]
    }
  ]
}
```
