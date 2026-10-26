# rule.get.portal_configDistributionRule_conflictRule.2158c347

FindConflictRule 获取冲突规则列表

- 服务：rule；后端相对路径：`/portal/configDistributionRule/conflictRule`；方法：GET。
- 前端路径：/portal/configDistributionRule/conflictRule。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：rule/router/portal.go:76。
- 后端源码：rule/router/config_distribution/conflict_group.go:21。
- 前端源码：solar-engine-fe/src/api/modules/onlineParameter/index.ts:66；方法 conflictRuleList；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "pageNum": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "pageSize": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      },
      "appId": {
        "x-unresolved": "Gin 查询字符串，按业务转换为数字/字符串",
        "x-source-type": "query"
      }
    },
    "required": [
      "appId"
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
