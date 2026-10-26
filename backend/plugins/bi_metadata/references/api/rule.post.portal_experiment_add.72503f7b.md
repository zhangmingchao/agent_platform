# rule.post.portal_experiment_add.72503f7b

Add 添加试验

- 服务：rule；后端相对路径：`/portal/experiment/add`；方法：POST。
- 前端路径：/portal/ab/experiment/add。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：rule/router/portal.go:184。
- 后端源码：rule/router/experiment/experiment.go:20。
- 前端源码：solar-engine-fe/src/api/modules/abtesting/index.ts:59；方法 addTest；参数类型 `any`。

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
      "experimentType": {
        "type": "integer",
        "description": "试验类型。1：编程试验"
      },
      "name": {
        "type": "string",
        "description": "试验名称"
      },
      "desc": {
        "type": "string",
        "description": "试验名称"
      },
      "experimentLayerId": {
        "type": "integer",
        "description": "试验层id"
      },
      "experimentLayerName": {
        "type": "string",
        "description": "试验层名称"
      },
      "experimentLayerFlowValue": {
        "type": "integer",
        "description": "分层流量。最大100"
      },
      "status": {
        "type": "integer",
        "description": "状态。1:暂存;2:调试中;3:运行中;4:已结束;5:删除;"
      },
      "tagResultId": {
        "type": "integer",
        "description": "标签值ID"
      },
      "isKeepGroup": {
        "type": "integer",
        "description": "是否保组。1保组，2 不保组"
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
      "diversionBodyId": {
        "type": "integer",
        "description": "分流主体类型id"
      },
      "diversionBodyType": {
        "type": "integer",
        "description": "分流主体类型。1: _account_id；2: _distinct_id；3: custom_sys 自定义 系统配置；4: custom_user 自定义 用户设置"
      },
      "diversionBodyTableType": {
        "type": "integer",
        "description": "分流主体对应属性表.-1:无;0:事件表;1:用户表;2:分群表;3:设备表"
      },
      "diversionBody": {
        "type": "string",
        "description": "分流主体"
      },
      "diversionPercentValue": {
        "type": "integer",
        "description": "分流比例"
      },
      "conditionType": {
        "type": "integer",
        "description": "条件配置.1:条件筛选;2:文件导入"
      },
      "fileName": {
        "type": "string",
        "description": "文件名称"
      },
      "fileUuid": {
        "type": "string",
        "description": "文件uuid。文件导入时，需要保持唯一"
      },
      "FileUuidDb": {
        "type": "string"
      },
      "ossPath": {
        "type": "string"
      },
      "fileUrl": {
        "type": "string"
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
      },
      "condition": {
        "type": "string"
      },
      "OssPathLoadDb": {
        "type": "string"
      },
      "distributionType": {
        "type": "integer",
        "description": "分配方式。1平均分配;2手动分配"
      },
      "configIndicatorFiltrate": {
        "x-source-type": "any",
        "x-unresolved": "动态 JSON，参数形状需查调用页面"
      },
      "usedRelationConfigIndicator": {
        "type": "boolean"
      },
      "relationFiltrate": {
        "x-source-type": "any",
        "x-unresolved": "动态 JSON，参数形状需查调用页面"
      },
      "configIndicator": {
        "type": "string",
        "description": "配置指标"
      },
      "timeOnline": {
        "type": "string",
        "description": "上线时间"
      },
      "timeOffline": {
        "type": "string",
        "description": "下线时间"
      },
      "createBy": {
        "type": "integer",
        "description": "创建人id"
      },
      "createByName": {
        "type": "string"
      },
      "createAt": {
        "type": "string",
        "description": "创建时间"
      },
      "createAtText": {
        "type": "string"
      },
      "updateBy": {
        "type": "integer",
        "description": "修改人id"
      },
      "updateAt": {
        "type": "string",
        "description": "修改时间"
      },
      "autoLineSwitch": {
        "type": "integer",
        "description": "DEFAULT 2 NULL COMMENT '自动上下线开关。1开启；2:关闭';"
      },
      "autoOnlineTime": {
        "type": "string",
        "description": "自动上线时间"
      },
      "autoOfflineTime": {
        "type": "string",
        "description": "自动下线时间"
      },
      "audienceCondition": {
        "type": "string",
        "description": "人群筛选条件"
      },
      "experimentGroupList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer"
            },
            "name": {
              "type": "string",
              "description": "试验分组名称"
            },
            "desc": {
              "type": "string",
              "description": "规则描述"
            },
            "descFileUuid": {
              "type": "string",
              "description": "描述文件uuid"
            },
            "descFileName": {
              "type": "string",
              "description": "文件名称"
            },
            "descOssPath": {
              "type": "string",
              "description": "前端上传oss地址"
            },
            "fileUrl": {
              "type": "string",
              "description": "返回前端临时文件地址"
            },
            "experimentId": {
              "type": "integer",
              "description": "试验id"
            },
            "type": {
              "type": "integer",
              "description": "试验组类型。1:对照组;2:实验组"
            },
            "diversionPercentValue": {
              "type": "integer",
              "description": "分流比例"
            },
            "index": {
              "type": "integer",
              "description": "下标"
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
            "deviceDebugList": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "paramData": {
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
          "x-source-type": "ExperimentGroupInfoDto",
          "x-source": {
            "project": "rule",
            "file": "pkg/dto/dto_experiment/experiment_group_dto.go",
            "line": 1
          }
        }
      },
      "experimentParamInfoList": {
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
      "experimentUrl": {
        "type": "string",
        "description": "试验url"
      },
      "matchType": {
        "type": "integer"
      },
      "middlePageType": {
        "type": "integer"
      },
      "paramProcessMode": {
        "type": "integer"
      }
    },
    "x-source-type": "dto_experiment.ExperimentInfoDto",
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
