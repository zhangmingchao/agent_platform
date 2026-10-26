# rule.post.portal_experiment_report_indSummary.189819d3

ReportSummaryInd 指标汇总

- 服务：rule；后端相对路径：`/portal/experiment/report/indSummary`；方法：POST。
- 前端路径：/portal/ab/experiment/report/indSummary。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：rule/router/portal.go:163。
- 后端源码：rule/router/experiment/experiment_report.go:36。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:152；方法 getIndSummaryTable；参数类型 `Pick<TestId & SearchDate, "experimentId" | "startDate" | "endDate" | "startDateTz" | "endDateTz" | "timeType">`。

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
          "additionalProperties": {
            "x-source-type": "any",
            "x-unresolved": "动态 JSON，参数形状需查调用页面"
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
      "indKey": {
        "type": "string"
      },
      "timeType": {
        "type": "integer",
        "description": "时间类型 1:server_time  2:event_time"
      },
      "IndsqlList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "reportSqlV": {
        "type": "array",
        "items": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "ciSql": {
        "type": "string"
      },
      "showSql": {
        "type": "boolean"
      },
      "enterGroupSql": {
        "type": "string"
      }
    },
    "x-source-type": "dto_experiment.ReportIndicatorsTableDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/dto_experiment/experiment_report_dto.go",
      "line": 1
    },
    "required": [
      "experimentId"
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
              "0": {
                "type": "string",
                "description": "核心指标"
              },
              "id": {
                "type": "number",
                "description": "对照组 / 试验组 Id"
              },
              "name": {
                "type": "string",
                "description": "对照组 / 试验组 名称"
              },
              "-1": {
                "type": "string",
                "description": "进组人数"
              },
              "ci": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "置信区间"
              },
              "pValue": {
                "type": "string",
                "description": "p-value"
              }
            },
            "required": [
              "id",
              "name",
              "-1",
              "ci",
              "pValue"
            ],
            "additionalProperties": {
              "x-unresolved": "any"
            }
          }
        }
      },
      "required": [
        "dataList"
      ]
    }
  ]
}
```
