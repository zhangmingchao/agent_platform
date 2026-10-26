# rule.post.portal_configDistributionRule_modify.fc9c80d0

ModifyRule 规则修改

- 服务：rule；后端相对路径：`/portal/configDistributionRule/modify`；方法：POST。
- 前端路径：/portal/configDistributionRule/modify。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：rule/router/portal.go:92。
- 后端源码：rule/router/config_distribution/rule.go:65。
- 前端源码：solar-engine-fe/src/api/modules/onlineParameter/index.ts:46；方法 ruleEdit；参数类型 `any`。

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
      "id": {
        "type": "integer"
      },
      "appId": {
        "type": "integer",
        "description": "应用id"
      },
      "name": {
        "type": "string",
        "description": "规则名称"
      },
      "desc": {
        "type": "string",
        "description": "规则描述"
      },
      "status": {
        "type": "integer",
        "description": "状态。0:草稿;1:调试中;2:运行中;3:结束;4:删除"
      },
      "diversionBodyType": {
        "type": "integer",
        "description": "分流主体类型。1: _account_id；2: _distinct_id；3: custom_sys 自定义 系统配置；4: custom_user 自定义 用户设置"
      },
      "diversionBody": {
        "type": "string",
        "description": "分流主体"
      },
      "diversionBodyTableType": {
        "type": "integer"
      },
      "createBy": {
        "type": "integer",
        "description": "创建人id"
      },
      "createAt": {
        "type": "string",
        "description": "创建时间"
      },
      "updateBy": {
        "type": "integer",
        "description": "修改人id"
      },
      "updateAt": {
        "type": "string",
        "description": "修改时间"
      },
      "settingParamList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer"
            },
            "ruleId": {
              "type": "integer",
              "description": "规则id"
            },
            "paramId": {
              "type": "integer",
              "description": "规则id"
            }
          },
          "x-source-type": "ConfigDistributionRuleParamDto",
          "x-source": {
            "project": "rule",
            "file": "pkg/dto/rule_dto.go",
            "line": 1
          }
        }
      },
      "ruleGroupList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer"
            },
            "ruleId": {
              "type": "integer",
              "description": "规则ID"
            },
            "conditionType": {
              "type": "integer",
              "description": "用户分群ID"
            },
            "tagResultId": {
              "type": "integer",
              "description": "条件配置.1:条件筛选;2:随机流量;3:文件导入"
            },
            "condition": {
              "type": "string",
              "description": "条件规则"
            },
            "fileUuid": {
              "type": "string",
              "description": "文件uuid。文件导入时，需要保持唯一"
            },
            "diversionPercentValue": {
              "type": "integer",
              "description": "分流比例"
            },
            "paramsValue": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "id": {
                    "type": "integer"
                  },
                  "ruleGroupId": {
                    "type": "integer",
                    "description": "规则分组id"
                  },
                  "paramId": {
                    "type": "integer",
                    "description": "参数id"
                  },
                  "paramName": {
                    "type": "string"
                  },
                  "paramType": {
                    "type": "integer"
                  },
                  "paramValueId": {
                    "type": "integer",
                    "description": "参数值id"
                  },
                  "paramValue": {
                    "type": "string"
                  }
                },
                "x-source-type": "ConfigDistributionGroupParamsDto",
                "x-source": {
                  "project": "rule",
                  "file": "pkg/dto/rule_dto.go",
                  "line": 1
                }
              },
              "description": "参数设置"
            },
            "fileName": {
              "type": "string"
            },
            "ossPath": {
              "type": "string"
            },
            "fileUrl": {
              "type": "string"
            },
            "filtRate": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "profeName": {
                    "type": "string"
                  },
                  "profileName": {
                    "type": "string"
                  },
                  "propertiesName": {
                    "type": "string"
                  },
                  "condition": {
                    "type": "string"
                  },
                  "conditionIdList": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "value": {
                    "x-source-type": "any",
                    "x-unresolved": "动态 JSON，参数形状需查调用页面"
                  },
                  "profileType": {
                    "type": "string"
                  },
                  "tableType": {
                    "type": "integer"
                  },
                  "dimension": {
                    "type": "integer"
                  },
                  "isCoreConfigIndicator": {
                    "type": "boolean",
                    "description": "是否核心指标"
                  },
                  "id": {
                    "type": "string"
                  },
                  "relativeValue": {
                    "type": "string"
                  },
                  "relativeEventValue": {
                    "type": "string"
                  },
                  "relativeMinuteValue": {
                    "type": "string"
                  },
                  "eventClassify": {
                    "type": "integer"
                  },
                  "profileClassify": {
                    "type": "integer"
                  },
                  "dateType": {
                    "type": "integer"
                  },
                  "endDate": {
                    "type": "string"
                  },
                  "endDayFromToday": {
                    "type": "integer"
                  },
                  "startDate": {
                    "type": "string"
                  },
                  "startDayFromToday": {
                    "type": "integer"
                  },
                  "eventName": {
                    "type": "string"
                  },
                  "name": {
                    "type": "string"
                  },
                  "arithId": {
                    "type": "string"
                  },
                  "arithShowName": {
                    "type": "string"
                  },
                  "funcSqls": {
                    "type": "string"
                  },
                  "profileNameList": {
                    "type": "array",
                    "items": {
                      "type": "string"
                    }
                  },
                  "profileShowName": {
                    "type": "string"
                  },
                  "isAssumeNotNull": {
                    "type": "boolean"
                  },
                  "groupFilList": {
                    "type": "array",
                    "items": {
                      "x-source-type": "Filtrate",
                      "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                    }
                  },
                  "customList": {
                    "type": "array",
                    "items": {
                      "x-source-type": "Filtrate",
                      "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                    }
                  },
                  "filtrate": {
                    "type": "array",
                    "items": {
                      "x-source-type": "Filtrate",
                      "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                    }
                  },
                  "indFormat": {
                    "type": "integer",
                    "description": "自定义指标保留小数位"
                  },
                  "category": {
                    "type": "integer",
                    "description": "分群类别。1：普通分群，2:父分群,3:子分群"
                  },
                  "hasSubgroup": {
                    "type": "boolean"
                  },
                  "parentId": {
                    "type": "integer"
                  },
                  "customOptType": {
                    "type": "string"
                  },
                  "eventRelation": {
                    "type": "integer"
                  },
                  "sheetTab": {
                    "type": [
                      "integer",
                      "null"
                    ]
                  }
                },
                "x-source-type": "Filtrate",
                "x-source": {
                  "project": "rule",
                  "file": "pkg/dto/bi_filtrate_dto.go",
                  "line": 1
                }
              }
            },
            "debugDeviceIdList": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "createBy": {
              "type": "integer",
              "description": "创建人id"
            }
          },
          "x-source-type": "ConfigDistributionRuleGroupDto",
          "x-source": {
            "project": "rule",
            "file": "pkg/dto/rule_dto.go",
            "line": 1
          }
        }
      },
      "conflictRuleGroupIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "appKey": {
        "type": "string"
      },
      "proKey": {
        "type": "string"
      },
      "tenantId": {
        "type": "integer"
      },
      "sourceModule": {
        "type": "integer"
      },
      "sourceModuleId": {
        "type": "integer"
      },
      "OperateUserEmail": {
        "type": "string"
      },
      "TagId": {
        "type": "integer"
      },
      "TagResultId": {
        "type": "integer"
      }
    },
    "x-source-type": "dto.ConfigDistributionRuleDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/rule_dto.go",
      "line": 1
    },
    "required": [
      "id"
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
