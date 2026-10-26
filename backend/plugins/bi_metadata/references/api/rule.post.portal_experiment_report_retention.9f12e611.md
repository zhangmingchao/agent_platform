# rule.post.portal_experiment_report_retention.9f12e611

ReportRetention 试验报告 留存指标

- 服务：rule；后端相对路径：`/portal/experiment/report/retention`；方法：POST。
- 前端路径：/portal/ab/experiment/report/retention。
- 状态：matched；操作：read；Schema：declared。
- 后端源码：rule/router/portal.go:164。
- 后端源码：rule/router/experiment/experiment_report.go:118。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:171；方法 getRetentionChart；参数类型 `Pick<TestId & SearchDate, "experimentId" | "startDate" | "endDate" | "startDateTz" | "endDateTz" | "timeType">`。

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
      "dataList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "value": {
              "type": "string",
              "description": "ck中返回的有可能是∞ float64 解析会报错"
            },
            "dt": {
              "type": "string"
            },
            "name": {
              "type": "string"
            },
            "experimentGroupId": {
              "type": "string"
            }
          },
          "x-source-type": "model_ck.ReportIndPo",
          "x-source": {
            "project": "rule",
            "file": "model/model_ck/ab_report.go",
            "line": 1
          }
        }
      },
      "experimentId": {
        "type": "integer"
      },
      "startDate": {
        "type": "string"
      },
      "endDate": {
        "type": "string"
      },
      "timeType": {
        "type": "integer",
        "description": "时间类型 1:server_time  2:event_time"
      },
      "indKey": {
        "type": "string"
      },
      "showSql": {
        "type": "boolean"
      }
    },
    "x-source-type": "dto_experiment.ReportIndicatorsTreeDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/dto_experiment/experiment_report_dto.go",
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
        "dataList": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "dt": {
                "type": "string"
              }
            },
            "required": [
              "dt"
            ],
            "additionalProperties": {
              "type": "string"
            }
          }
        },
        "columns": {
          "type": "object",
          "properties": {},
          "additionalProperties": {
            "type": "string"
          }
        }
      },
      "required": [
        "dataList",
        "columns"
      ]
    }
  ]
}
```
