# rule.get.portal_configDistributionRule_detail.89893944

GetRuleDetail 获取规则详情

- 服务：rule；后端相对路径：`/portal/configDistributionRule/detail`；方法：GET。
- 前端路径：/portal/configDistributionRule/detail。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：rule/router/portal.go:75。
- 后端源码：rule/router/config_distribution/conflict_group.go:177。
- 前端源码：solar-engine-fe/src/api/modules/onlineParameter/index.ts:51；方法 ruleDetail；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "id": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "feCopy": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      }
    },
    "required": [
      "id"
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
