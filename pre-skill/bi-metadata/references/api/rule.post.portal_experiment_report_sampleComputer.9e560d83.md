# rule.post.portal_experiment_report_sampleComputer.9e560d83

样本计算器计算指标均值和指标标准差
/

- 服务：rule；后端相对路径：`/portal/experiment/report/sampleComputer`；方法：POST。
- 前端路径：/portal/ab/experiment/report/sampleComputer。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：rule/router/portal.go:166。
- 后端源码：rule/router/experiment/experiment_report.go:181。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:127；方法 experimentSampleComputer；参数类型 `any`。

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
      "behaviorContent": {
        "type": "object",
        "additionalProperties": {
          "x-source-type": "any",
          "x-unresolved": "动态 JSON，参数形状需查调用页面"
        }
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
      "productKey": {
        "type": "string"
      },
      "appkey": {
        "type": "string"
      },
      "appId": {
        "type": "integer"
      },
      "showSql": {
        "type": "boolean"
      },
      "experimentId": {
        "type": "integer"
      }
    },
    "x-source-type": "dto_experiment.SampleComputerReqDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/dto_experiment/experiment_report_dto.go",
      "line": 1
    },
    "required": [
      "appId"
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
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
