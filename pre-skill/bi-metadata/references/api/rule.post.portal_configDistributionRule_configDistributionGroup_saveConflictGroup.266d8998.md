# rule.post.portal_configDistributionRule_configDistributionGroup_saveConflictGroup.266d8998

SaveConflictGroup 保存冲突分组列表

- 服务：rule；后端相对路径：`/portal/configDistributionRule/configDistributionGroup/saveConflictGroup`；方法：POST。
- 前端路径：/portal/configDistributionRule/configDistributionGroup/saveConflictGroup。
- 状态：matched；操作：write；Schema：declared。
- 后端源码：rule/router/portal.go:107。
- 后端源码：rule/router/config_distribution/conflict_group.go:65。
- 前端源码：solar-engine-fe/src/api/modules/onlineParameter/index.ts:76；方法 updateConflictRuleGroupList；参数类型 `any`。

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
      "ruleId": {
        "type": "integer"
      },
      "conflictRuleGroupIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "createBy": {
        "type": "integer"
      }
    },
    "x-source-type": "dto.SaveConflictGroupDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/conflict_group_dto.go",
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
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
