# rule.post.portal_experiment_pushOut.315c354f

PushOut 试验推全

- 服务：rule；后端相对路径：`/portal/experiment/pushOut`；方法：POST。
- 前端路径：/portal/ab/experiment/pushOut。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：rule/router/portal.go:190。
- 后端源码：rule/router/experiment/experiment.go:256。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:42；方法 pushOut；参数类型 `any`。

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
      "experimentGroupId": {
        "type": "integer"
      },
      "paramList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer"
            },
            "experimentGroupId": {
              "type": "integer",
              "description": "试验分组id"
            },
            "paramId": {
              "type": "integer",
              "description": "试验参数id"
            },
            "paramName": {
              "type": "string",
              "description": "参数名称"
            },
            "paramValueId": {
              "type": "integer",
              "description": "试验参数值id"
            },
            "paramValueText": {
              "type": "string",
              "description": "试验参数值文本"
            }
          },
          "x-source-type": "ExperimentGroupParamsDto",
          "x-source": {
            "project": "rule",
            "file": "pkg/dto/dto_experiment/experiment_group_params_dto.go",
            "line": 1
          }
        }
      },
      "ruleGroupId": {
        "type": "integer"
      },
      "conflictRuleGroupIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "diversionConditionType": {
        "type": "integer",
        "description": "1使用受众用户;2:通过条件筛选;3:文件导入"
      },
      "diversionPercentValue": {
        "type": "integer",
        "description": "分流比例"
      },
      "fileName": {
        "type": "string"
      },
      "ossPath": {
        "type": "string"
      },
      "fileUuid": {
        "type": "string",
        "description": "文件uuid。文件导入时，需要保持唯一"
      },
      "filtrate": {
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
            "customList": {
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
            "filtrate": {
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
          "x-source-type": "dto.Filtrate",
          "x-source": {
            "project": "rule",
            "file": "pkg/dto/bi_filtrate_dto.go",
            "line": 1
          }
        }
      }
    },
    "x-source-type": "dto_experiment.ExperimentPushOutDto",
    "x-source": {
      "project": "rule",
      "file": "pkg/dto/dto_experiment/experiment_dto.go",
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
