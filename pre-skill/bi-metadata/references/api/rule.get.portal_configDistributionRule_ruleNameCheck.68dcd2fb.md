# rule.get.portal_configDistributionRule_ruleNameCheck.68dcd2fb

RuleNameCheck 获取规则状态信息

- 服务：rule；后端相对路径：`/portal/configDistributionRule/ruleNameCheck`；方法：GET。
- 前端路径：/portal/configDistributionRule/ruleNameCheck。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：rule/router/portal.go:77。
- 后端源码：rule/router/config_distribution/rule.go:127。
- 前端源码：solar-engine-fe/src/api/modules/onlineParameter/index.ts:29；方法 ruleNameCheck；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "ruleId": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "ruleName": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "appId": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      }
    },
    "required": [
      "appId",
      "ruleName"
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
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
