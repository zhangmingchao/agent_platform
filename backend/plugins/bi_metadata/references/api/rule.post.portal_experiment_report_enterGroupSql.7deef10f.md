# rule.post.portal_experiment_report_enterGroupSql.7deef10f

EnterGroupSql 获取进组sql

- 服务：rule；后端相对路径：`/portal/experiment/report/enterGroupSql`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：read；Schema：partial。
- 后端源码：rule/router/portal.go:165。
- 后端源码：rule/router/experiment/experiment_report.go:154。

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
  "frontend_schemas": []
}
```
