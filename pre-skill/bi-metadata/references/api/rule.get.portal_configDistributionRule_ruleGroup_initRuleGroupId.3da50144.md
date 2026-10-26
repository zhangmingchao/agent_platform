# rule.get.portal_configDistributionRule_ruleGroup_initRuleGroupId.3da50144

分组id生成

- 服务：rule；后端相对路径：`/portal/configDistributionRule/ruleGroup/initRuleGroupId`；方法：GET。
- 前端路径：/portal/configDistributionRule/ruleGroup/initRuleGroupId。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：rule/router/portal.go:101。
- 后端源码：rule/router/config_distribution/audience_config.go:10。
- 前端源码：solar-engine-fe/src/api/modules/onlineParameter/index.ts:33；方法 initRuleGroupId；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {},
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
