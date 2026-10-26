# bi.post.userTag_createPresetTag.80ba757b

获取预置模板列表

- 服务：bi；后端相对路径：`/userTag/createPresetTag`；方法：POST。
- 前端路径：/bi-docker/api/userTag/createPresetTag。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/usertag/UserTagController.java:169。
- 前端源码：solar-engine-fe/src/api/modules/userTag/index.ts:74；方法 createPresetTag；参数类型 `any`。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "false": {
        "type": "boolean",
        "default": false
      }
    },
    "additionalProperties": false
  },
  "body_schema": {
    "type": "object",
    "properties": {
      "id": {
        "type": "integer",
        "description": "id /"
      },
      "userId": {
        "type": "integer",
        "description": "租户id /"
      },
      "category": {
        "type": "integer",
        "description": "标签类别。1：租户级别，2:产品级别 /"
      },
      "name": {
        "type": "string",
        "description": "名称 /"
      },
      "tag": {
        "type": "string",
        "description": "唯一标识 /"
      },
      "remark": {
        "type": "string",
        "description": "备注 /"
      },
      "tagType": {
        "type": "integer",
        "description": "标签类型：1.条件标签， 2.预置标签， 3.上传标签 /"
      },
      "tagValueType": {
        "type": "integer",
        "description": "标签值类型。1:string;2:number;3:date;4:array;5:boolean; /"
      },
      "productKeys": {
        "type": "string",
        "description": "生效产品key列表 /"
      },
      "productRegion": {
        "type": "string",
        "description": "产品所属地区 /"
      },
      "appKey": {
        "type": "string",
        "description": "应用key /"
      },
      "computeType": {
        "type": "integer",
        "description": "计算类型：1.全部产品满足，2.任意产品满足 /"
      },
      "timeZone": {
        "type": "string",
        "description": "时区 /"
      },
      "updateType": {
        "type": "integer",
        "description": "更新方式：1.自动更新，2.手动更新 /"
      },
      "status": {
        "type": "integer",
        "description": "状态：1.QUEUED，2.RUNNING，3.FAILED，4.SUCCESS，5.DELETED /"
      },
      "tagResultDtoList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer",
              "description": "@author bi /"
            },
            "userId": {
              "type": "integer",
              "description": "@author bi /"
            },
            "tagId": {
              "type": "integer",
              "description": "@author bi /"
            },
            "tagValue": {
              "type": "string",
              "description": "@author bi /"
            },
            "templateId": {
              "type": "integer",
              "description": "@author bi /"
            },
            "tagCondition": {
              "type": "string",
              "description": "@author bi /"
            },
            "location": {
              "type": "integer",
              "description": "@author bi /"
            },
            "num": {
              "type": "integer",
              "description": "@author bi /"
            },
            "status": {
              "type": "integer",
              "description": "@author bi /"
            },
            "createBy": {
              "type": "integer",
              "description": "@author bi /"
            },
            "createAt": {
              "type": "string",
              "description": "@author bi /"
            },
            "updateBy": {
              "type": "integer",
              "description": "@author bi /"
            },
            "updateAt": {
              "type": "string",
              "description": "@author bi /"
            },
            "templateCode": {
              "type": "string",
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            },
            "extend": {
              "type": "string"
            },
            "module": {
              "type": "integer",
              "description": "1:自定义分析;2:在线参数;3:ab试验;4:open_api接口;5:ab-shunt /"
            },
            "moduleId": {
              "type": "integer",
              "description": "业务模块枚举值对应的Id /"
            },
            "filtrate": {
              "type": "object",
              "properties": {
                "profeName": {
                  "type": "string",
                  "description": "前端回传 属性名称 /"
                },
                "profileName": {
                  "type": "string",
                  "description": "前端回传 属性名称 /"
                },
                "condition": {
                  "type": "string",
                  "description": "前端回传 属性名称 /"
                },
                "value": {
                  "x-source-type": "Object",
                  "x-unresolved": "动态 JSON，参数形状需查调用页面",
                  "description": "前端回传 属性名称 /"
                },
                "profileType": {
                  "type": "string",
                  "description": "前端回传 属性名称 /"
                },
                "tableType": {
                  "type": "integer",
                  "description": "过滤来源 0:事件，1：用户 /"
                },
                "dimension": {
                  "type": "integer",
                  "description": "过滤来源 0:事件，1：用户 /"
                },
                "id": {
                  "type": "string",
                  "description": "属性id"
                },
                "relativeValue": {
                  "type": "string",
                  "description": "属性id"
                },
                "relativeEventValue": {
                  "type": "string",
                  "description": "属性id"
                },
                "relativeMinuteValue": {
                  "type": "string",
                  "description": "属性id"
                },
                "timeType": {
                  "type": "integer",
                  "description": "属性id"
                },
                "metaProfList": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "productKey": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "appKey": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "profileName": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "name": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "profileType": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "profileClassify": {
                        "type": "integer",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "propertiesName": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "expression": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "relateType": {
                        "type": "integer",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "eventList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "sample": {
                        "type": "integer"
                      },
                      "isShow": {
                        "type": "integer"
                      },
                      "productKeyList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "appKeyList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "profileNameList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "profileTypeList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "profileClassifyList": {
                        "type": "array",
                        "items": {
                          "type": "integer"
                        }
                      },
                      "expressSql": {
                        "type": "string"
                      },
                      "searchText": {
                        "type": "string"
                      },
                      "eventNameList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "nameNotNull": {
                        "type": "boolean"
                      },
                      "tableType": {
                        "type": "integer"
                      },
                      "tableName": {
                        "type": "string"
                      },
                      "language": {
                        "type": "string"
                      },
                      "idList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "x-source-type": "ProfileDto",
                    "x-source": {
                      "project": "bi-docker",
                      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/profile/ProfileDto.java",
                      "line": 1
                    }
                  },
                  "description": "*************************虚拟属性********************************"
                },
                "expressSql": {
                  "type": "string",
                  "description": "*************************虚拟属性********************************"
                },
                "eventConfCondDto": {
                  "type": "object",
                  "properties": {
                    "behaviorContents": {
                      "type": "array",
                      "items": {
                        "x-source-type": "BehaviorContent",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                      },
                      "description": "行为分析，查询 /"
                    },
                    "filtrate": {
                      "type": "array",
                      "items": {
                        "x-source-type": "Filtrate",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                      },
                      "description": "过滤条件 /"
                    }
                  },
                  "x-source-type": "EventConfigConditionsDto",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/dto/event/EventConfigConditionsDto.java",
                    "line": 1
                  },
                  "description": "*************************虚拟属性********************************"
                },
                "forexRateProfileMap": {
                  "type": "object",
                  "properties": {
                    "id": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "prokey": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "appkey": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "profileId": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "profileName": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "tableType": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "metaProfileName": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "metaProfileClassify": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "metaProfilePropertiesName": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "calculationMethod": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "dynamicCurrencyProfile": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "dynamicCurrencyProfileClassify": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "dynamicCurrencyProfilePropertiesName": {
                      "type": "string"
                    },
                    "fixedCurrencyType": {
                      "type": "string"
                    },
                    "targetCurrencyType": {
                      "type": "string"
                    },
                    "createAt": {
                      "type": "string",
                      "description": "日期格式按调用页面/后端约定，不能推测时区"
                    }
                  },
                  "x-source-type": "ForexRateProfileMapDto",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/dto/profile/ForexRateProfileMapDto.java",
                    "line": 1
                  },
                  "description": "*************************虚拟属性********************************"
                },
                "eventClassify": {
                  "type": "integer",
                  "description": "*************************虚拟属性********************************"
                },
                "profileClassify": {
                  "type": "integer",
                  "description": "*************************虚拟属性********************************"
                },
                "dateType": {
                  "type": "integer",
                  "description": "1 动态、2 静态"
                },
                "featureType": {
                  "type": "string",
                  "description": "1 动态、2 静态"
                },
                "endDate": {
                  "type": "string",
                  "description": "1 动态、2 静态"
                },
                "endDayFromToday": {
                  "type": "integer",
                  "description": "1 动态、2 静态"
                },
                "startDate": {
                  "type": "string",
                  "description": "1 动态、2 静态"
                },
                "startDayFromToday": {
                  "type": "integer",
                  "description": "1 动态、2 静态"
                },
                "eventName": {
                  "type": "string",
                  "description": "1 动态、2 静态"
                },
                "name": {
                  "type": "string",
                  "description": "1 动态、2 静态"
                },
                "idxColumn": {
                  "type": "string",
                  "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                },
                "analysisBodyVo": {
                  "type": "object",
                  "properties": {
                    "id": {
                      "type": "integer",
                      "description": "Created by Mybatis Generator 2022/07/12 /"
                    },
                    "profileName": {
                      "type": "string",
                      "description": "Created by Mybatis Generator 2022/07/12 /"
                    },
                    "name": {
                      "type": "string",
                      "description": "Created by Mybatis Generator 2022/07/12 /"
                    },
                    "profileType": {
                      "type": "string",
                      "description": "Created by Mybatis Generator 2022/07/12 /"
                    },
                    "tableType": {
                      "type": "integer",
                      "description": "Created by Mybatis Generator 2022/07/12 /"
                    },
                    "createBy": {
                      "type": "integer"
                    },
                    "createAt": {
                      "type": "string",
                      "description": "日期格式按调用页面/后端约定，不能推测时区"
                    },
                    "updateBy": {
                      "type": "integer"
                    },
                    "updateAt": {
                      "type": "string",
                      "description": "日期格式按调用页面/后端约定，不能推测时区"
                    },
                    "isDefault": {
                      "type": "integer"
                    },
                    "isDel": {
                      "type": "integer"
                    },
                    "productKey": {
                      "type": "string"
                    },
                    "isPreset": {
                      "type": "integer"
                    },
                    "isPredef": {
                      "type": "boolean"
                    },
                    "userId": {
                      "type": "integer"
                    },
                    "currentTimeZoneOffset": {
                      "type": "string"
                    },
                    "isOpenAnalysisBody": {
                      "type": "integer"
                    },
                    "createByName": {
                      "type": "string"
                    },
                    "dataConcatName": {
                      "type": "string"
                    },
                    "propertiesName": {
                      "type": "string"
                    },
                    "profileClassify": {
                      "type": "integer"
                    },
                    "abReportConcatName": {
                      "type": "string"
                    },
                    "parentProfileName": {
                      "type": "string"
                    },
                    "isCustomId": {
                      "type": "boolean"
                    },
                    "dataSource": {
                      "type": "string"
                    }
                  },
                  "x-source-type": "AnalysisBodyVo",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/vo/body/AnalysisBodyVo.java",
                    "line": 1
                  },
                  "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                },
                "arithId": {
                  "type": "string",
                  "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                },
                "funcSqls": {
                  "type": "string",
                  "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                },
                "profileNameList": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                },
                "entitySource": {
                  "type": "string",
                  "description": "events,users,device -> 0,1,2映射 /"
                },
                "entityType": {
                  "type": "string",
                  "description": "分析主体的属性 /"
                },
                "firstDayOfWeek": {
                  "type": "integer",
                  "description": "当日所在周 1，2，3，4，5，6，7(周一到周日) /"
                },
                "timeParticle": {
                  "type": "integer",
                  "description": "1(天) 2（小时）3（周）4（按月）5（合计） particle size /"
                },
                "isAssumeNotNull": {
                  "type": "boolean",
                  "description": "********************聚合函数 为空的时候解决方法***********************"
                },
                "groupFilList": {
                  "type": "array",
                  "items": {
                    "x-source-type": "Filtrate",
                    "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                  },
                  "description": "********************聚合函数 为空的时候解决方法***********************"
                },
                "propertiesName": {
                  "type": "string",
                  "description": "********************聚合函数 为空的时候解决方法***********************"
                },
                "hasSubgroup": {
                  "type": "boolean",
                  "description": "********************聚合函数 为空的时候解决方法***********************"
                },
                "subgroupIdList": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "********************聚合函数 为空的时候解决方法***********************"
                },
                "category": {
                  "type": "integer",
                  "description": "默认值为1 /"
                },
                "parentId": {
                  "type": "integer",
                  "description": "默认值为1 /"
                },
                "relateBehaviorGroup": {
                  "type": "boolean",
                  "description": "过滤条件是否关联父分群分组 /"
                },
                "arithShowName": {
                  "type": "string",
                  "description": "过滤条件是否关联父分群分组 /"
                },
                "profileShowName": {
                  "type": "string",
                  "description": "过滤条件是否关联父分群分组 /"
                },
                "isIndustryTag": {
                  "type": "boolean",
                  "description": "是否是行业标签 /"
                },
                "isCustom": {
                  "type": "boolean",
                  "description": "是否是行业标签 /"
                },
                "relation": {
                  "type": "string",
                  "description": "***********一二级条件联动****************"
                },
                "filtrate": {
                  "type": "array",
                  "items": {
                    "x-source-type": "Filtrate",
                    "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                  },
                  "description": "***********一二级条件联动****************"
                },
                "fromEventMetric": {
                  "type": "boolean",
                  "description": "***********一二级条件联动****************"
                },
                "eventRelation": {
                  "type": "integer",
                  "description": "***********一二级条件联动****************"
                },
                "relationProfileConfig": {
                  "type": "object",
                  "properties": {
                    "isRelation": {
                      "type": "boolean"
                    },
                    "relationList": {
                      "type": "array",
                      "items": {
                        "x-source-type": "Filtrate",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                      }
                    }
                  },
                  "x-source-type": "RelationConfig",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/vo/analysis/RelationConfig.java",
                    "line": 1
                  },
                  "description": "关联属性 /"
                },
                "window": {
                  "type": "integer",
                  "description": "关联属性 /"
                },
                "windowType": {
                  "type": "integer",
                  "description": "关联属性 /"
                },
                "eventList": {
                  "type": "array",
                  "items": {
                    "x-source-type": "Filtrate",
                    "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                  },
                  "description": "事件序列 /"
                },
                "excludeEvent": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "eventName": {
                        "type": "string",
                        "description": "虚拟事件标识 /"
                      },
                      "eventClassify": {
                        "type": "integer",
                        "description": "事件类型。1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 /"
                      }
                    },
                    "x-source-type": "EventConfigQueryVo",
                    "x-source": {
                      "project": "bi-docker",
                      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/EventConfigQueryVo.java",
                      "line": 1
                    }
                  },
                  "description": "事件序列之间没做过事件 /"
                },
                "sheetTab": {
                  "type": "integer",
                  "description": "事件序列之间没做过事件 /"
                }
              },
              "x-source-type": "Filtrate",
              "x-source": {
                "project": "bi-docker",
                "file": "da-dao/src/main/java/com/reyun/da/dao/vo/Filtrate.java",
                "line": 1
              },
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            },
            "conditionStr": {
              "type": "string",
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            },
            "behaviorContent": {
              "type": "object",
              "properties": {
                "eventNames": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "@author zc /"
                },
                "customList": {
                  "type": "array",
                  "items": {
                    "x-source-type": "BehaviorContent",
                    "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                  },
                  "description": "自定义指标 /"
                },
                "customExp": {
                  "type": "string",
                  "description": "自定义指标 /"
                },
                "eventName": {
                  "type": "string",
                  "description": "自定义指标 /"
                },
                "analysisType": {
                  "type": "integer",
                  "description": "自定义指标 /"
                },
                "coefficient": {
                  "type": "number",
                  "description": "系数 /"
                },
                "eventClassify": {
                  "type": "integer",
                  "description": "1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 1.预制 2:预定义 3：自定义 在历史报表中不纯在这个值或者是null /"
                },
                "profileName": {
                  "type": "string",
                  "description": "1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 1.预制 2:预定义 3：自定义 在历史报表中不纯在这个值或者是null /"
                },
                "profileClassify": {
                  "type": "integer",
                  "description": "1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 1.预制 2:预定义 3：自定义 在历史报表中不纯在这个值或者是null /"
                },
                "expressSql": {
                  "type": "string",
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "profileType": {
                  "type": "string",
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "arithId": {
                  "type": "string",
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "arithCode": {
                  "type": "string",
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "funcSqls": {
                  "type": "string",
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "subFuncSql": {
                  "type": "string",
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "name": {
                  "type": "string",
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "aliasName": {
                  "type": "string",
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "gong": {
                  "type": "string",
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "filtrate": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "profeName": {
                        "type": "string",
                        "description": "前端回传 属性名称 /"
                      },
                      "profileName": {
                        "type": "string",
                        "description": "前端回传 属性名称 /"
                      },
                      "condition": {
                        "type": "string",
                        "description": "前端回传 属性名称 /"
                      },
                      "value": {
                        "x-source-type": "Object",
                        "x-unresolved": "动态 JSON，参数形状需查调用页面",
                        "description": "前端回传 属性名称 /"
                      },
                      "profileType": {
                        "type": "string",
                        "description": "前端回传 属性名称 /"
                      },
                      "tableType": {
                        "type": "integer",
                        "description": "过滤来源 0:事件，1：用户 /"
                      },
                      "dimension": {
                        "type": "integer",
                        "description": "过滤来源 0:事件，1：用户 /"
                      },
                      "id": {
                        "type": "string",
                        "description": "属性id"
                      },
                      "relativeValue": {
                        "type": "string",
                        "description": "属性id"
                      },
                      "relativeEventValue": {
                        "type": "string",
                        "description": "属性id"
                      },
                      "relativeMinuteValue": {
                        "type": "string",
                        "description": "属性id"
                      },
                      "timeType": {
                        "type": "integer",
                        "description": "属性id"
                      },
                      "metaProfList": {
                        "type": "array",
                        "items": {
                          "x-source-type": "ProfileDto",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                        },
                        "description": "*************************虚拟属性********************************"
                      },
                      "expressSql": {
                        "type": "string",
                        "description": "*************************虚拟属性********************************"
                      },
                      "eventConfCondDto": {
                        "x-source-type": "EventConfigConditionsDto",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                        "description": "*************************虚拟属性********************************"
                      },
                      "forexRateProfileMap": {
                        "x-source-type": "ForexRateProfileMapDto",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                        "description": "*************************虚拟属性********************************"
                      },
                      "eventClassify": {
                        "type": "integer",
                        "description": "*************************虚拟属性********************************"
                      },
                      "profileClassify": {
                        "type": "integer",
                        "description": "*************************虚拟属性********************************"
                      },
                      "dateType": {
                        "type": "integer",
                        "description": "1 动态、2 静态"
                      },
                      "featureType": {
                        "type": "string",
                        "description": "1 动态、2 静态"
                      },
                      "endDate": {
                        "type": "string",
                        "description": "1 动态、2 静态"
                      },
                      "endDayFromToday": {
                        "type": "integer",
                        "description": "1 动态、2 静态"
                      },
                      "startDate": {
                        "type": "string",
                        "description": "1 动态、2 静态"
                      },
                      "startDayFromToday": {
                        "type": "integer",
                        "description": "1 动态、2 静态"
                      },
                      "eventName": {
                        "type": "string",
                        "description": "1 动态、2 静态"
                      },
                      "name": {
                        "type": "string",
                        "description": "1 动态、2 静态"
                      },
                      "idxColumn": {
                        "type": "string",
                        "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                      },
                      "analysisBodyVo": {
                        "x-source-type": "AnalysisBodyVo",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                        "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                      },
                      "arithId": {
                        "type": "string",
                        "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                      },
                      "funcSqls": {
                        "type": "string",
                        "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                      },
                      "profileNameList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "description": "表名称.主体名称 正对分群，标签使用，eg: d_events._distinct_index /"
                      },
                      "entitySource": {
                        "type": "string",
                        "description": "events,users,device -> 0,1,2映射 /"
                      },
                      "entityType": {
                        "type": "string",
                        "description": "分析主体的属性 /"
                      },
                      "firstDayOfWeek": {
                        "type": "integer",
                        "description": "当日所在周 1，2，3，4，5，6，7(周一到周日) /"
                      },
                      "timeParticle": {
                        "type": "integer",
                        "description": "1(天) 2（小时）3（周）4（按月）5（合计） particle size /"
                      },
                      "isAssumeNotNull": {
                        "type": "boolean",
                        "description": "********************聚合函数 为空的时候解决方法***********************"
                      },
                      "groupFilList": {
                        "type": "array",
                        "items": {
                          "x-source-type": "Filtrate",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                        },
                        "description": "********************聚合函数 为空的时候解决方法***********************"
                      },
                      "propertiesName": {
                        "type": "string",
                        "description": "********************聚合函数 为空的时候解决方法***********************"
                      },
                      "hasSubgroup": {
                        "type": "boolean",
                        "description": "********************聚合函数 为空的时候解决方法***********************"
                      },
                      "subgroupIdList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        },
                        "description": "********************聚合函数 为空的时候解决方法***********************"
                      },
                      "category": {
                        "type": "integer",
                        "description": "默认值为1 /"
                      },
                      "parentId": {
                        "type": "integer",
                        "description": "默认值为1 /"
                      },
                      "relateBehaviorGroup": {
                        "type": "boolean",
                        "description": "过滤条件是否关联父分群分组 /"
                      },
                      "arithShowName": {
                        "type": "string",
                        "description": "过滤条件是否关联父分群分组 /"
                      },
                      "profileShowName": {
                        "type": "string",
                        "description": "过滤条件是否关联父分群分组 /"
                      },
                      "isIndustryTag": {
                        "type": "boolean",
                        "description": "是否是行业标签 /"
                      },
                      "isCustom": {
                        "type": "boolean",
                        "description": "是否是行业标签 /"
                      },
                      "relation": {
                        "type": "string",
                        "description": "***********一二级条件联动****************"
                      },
                      "filtrate": {
                        "type": "array",
                        "items": {
                          "x-source-type": "Filtrate",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                        },
                        "description": "***********一二级条件联动****************"
                      },
                      "fromEventMetric": {
                        "type": "boolean",
                        "description": "***********一二级条件联动****************"
                      },
                      "eventRelation": {
                        "type": "integer",
                        "description": "***********一二级条件联动****************"
                      },
                      "relationProfileConfig": {
                        "x-source-type": "RelationConfig",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                        "description": "关联属性 /"
                      },
                      "window": {
                        "type": "integer",
                        "description": "关联属性 /"
                      },
                      "windowType": {
                        "type": "integer",
                        "description": "关联属性 /"
                      },
                      "eventList": {
                        "type": "array",
                        "items": {
                          "x-source-type": "Filtrate",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                        },
                        "description": "事件序列 /"
                      },
                      "excludeEvent": {
                        "type": "array",
                        "items": {
                          "x-source-type": "EventConfigQueryVo",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                        },
                        "description": "事件序列之间没做过事件 /"
                      },
                      "sheetTab": {
                        "type": "integer",
                        "description": "事件序列之间没做过事件 /"
                      }
                    },
                    "x-source-type": "Filtrate",
                    "x-source": {
                      "project": "bi-docker",
                      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/Filtrate.java",
                      "line": 1
                    }
                  },
                  "description": "虚拟属性涉及到的表达式sql /"
                },
                "unitValue": {
                  "type": "integer",
                  "description": "1两位小数 2百分比 3取整 /"
                },
                "type": {
                  "type": "integer",
                  "description": "1默认，2自定义 1:默认 /"
                },
                "group": {
                  "type": "object",
                  "properties": {
                    "type": {
                      "type": "integer",
                      "description": "/"
                    },
                    "groups": {
                      "type": "array",
                      "items": {
                        "type": "number"
                      },
                      "description": "/"
                    },
                    "profileName": {
                      "type": "string",
                      "description": "/"
                    },
                    "profileClassify": {
                      "type": "integer",
                      "description": "/"
                    },
                    "expressSql": {
                      "type": "string",
                      "description": "/"
                    },
                    "metaProfList": {
                      "type": "array",
                      "items": {
                        "x-source-type": "ProfileDto",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                      },
                      "description": "/"
                    },
                    "forexRateProfileMap": {
                      "type": "object",
                      "properties": {
                        "id": {
                          "type": "integer",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "prokey": {
                          "type": "string",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "appkey": {
                          "type": "string",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "profileId": {
                          "type": "integer",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "profileName": {
                          "type": "string",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "tableType": {
                          "type": "integer",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "metaProfileName": {
                          "type": "string",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "metaProfileClassify": {
                          "type": "integer",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "metaProfilePropertiesName": {
                          "type": "string",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "calculationMethod": {
                          "type": "integer",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "dynamicCurrencyProfile": {
                          "type": "string",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "dynamicCurrencyProfileClassify": {
                          "type": "integer",
                          "description": "@TableName forex_rate_profile_map /"
                        },
                        "dynamicCurrencyProfilePropertiesName": {
                          "type": "string"
                        },
                        "fixedCurrencyType": {
                          "type": "string"
                        },
                        "targetCurrencyType": {
                          "type": "string"
                        },
                        "createAt": {
                          "type": "string",
                          "description": "日期格式按调用页面/后端约定，不能推测时区"
                        }
                      },
                      "x-source-type": "ForexRateProfileMapDto",
                      "x-source": {
                        "project": "bi-docker",
                        "file": "da-dao/src/main/java/com/reyun/da/dao/dto/profile/ForexRateProfileMapDto.java",
                        "line": 1
                      },
                      "description": "/"
                    },
                    "profileType": {
                      "type": "string",
                      "description": "属性类型 /"
                    },
                    "name": {
                      "type": "string",
                      "description": "属性类型 /"
                    },
                    "tableType": {
                      "type": "integer",
                      "description": "属性类型 /"
                    },
                    "entityType": {
                      "type": "string",
                      "description": "属性类型 /"
                    },
                    "propertiesName": {
                      "type": "string",
                      "description": "属性类型 /"
                    },
                    "entitySource": {
                      "type": "string",
                      "description": "属性类型 /"
                    },
                    "id": {
                      "type": "string",
                      "description": "属性id /"
                    },
                    "groupTimeParticle": {
                      "type": "integer",
                      "description": "1(天) 2（小时）3（周）4（按月） /"
                    },
                    "firstDayOfWeek": {
                      "type": "integer",
                      "description": "当日所在周 1，2，3，4，5，6，7(周一到周日) /"
                    },
                    "arithId": {
                      "type": "string",
                      "description": "计算方法id 分布分析使用 /"
                    },
                    "idxColumn": {
                      "type": "string",
                      "description": "bitmap索引列 /"
                    },
                    "analysisBodyVo": {
                      "type": "object",
                      "properties": {
                        "isOpenAnalysisBody": {
                          "type": "integer"
                        },
                        "createByName": {
                          "type": "string"
                        },
                        "dataConcatName": {
                          "type": "string"
                        },
                        "propertiesName": {
                          "type": "string"
                        },
                        "profileClassify": {
                          "type": "integer"
                        },
                        "abReportConcatName": {
                          "type": "string"
                        },
                        "parentProfileName": {
                          "type": "string"
                        },
                        "isCustomId": {
                          "type": "boolean"
                        },
                        "dataSource": {
                          "type": "string"
                        }
                      },
                      "x-source-type": "AnalysisBodyVo",
                      "x-source": {
                        "project": "bi-docker",
                        "file": "da-dao/src/main/java/com/reyun/da/dao/vo/body/AnalysisBodyVo.java",
                        "line": 1
                      },
                      "description": "bitmap索引列 /"
                    },
                    "parentProfileName": {
                      "type": "string",
                      "description": "bitmap索引列 /"
                    },
                    "hasSubgroup": {
                      "type": "boolean",
                      "description": "bitmap索引列 /"
                    },
                    "subgroupList": {
                      "type": "array",
                      "items": {
                        "x-source-type": "CdpAudienceTagResult",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                      },
                      "description": "bitmap索引列 /"
                    },
                    "relateFiltrate": {
                      "type": "boolean",
                      "description": "父分群分组时是否关联过滤条件 /"
                    },
                    "isIndustryTag": {
                      "type": "boolean",
                      "description": "父分群分组时是否关联过滤条件 /"
                    },
                    "isCustom": {
                      "type": "boolean",
                      "description": "父分群分组时是否关联过滤条件 /"
                    },
                    "arrayType": {
                      "type": "integer",
                      "description": "1 离散 2 元素 3 集合 /"
                    }
                  },
                  "x-source-type": "BehaviorGroup",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/vo/BehaviorGroup.java",
                    "line": 1
                  },
                  "description": "1默认，2自定义 1:默认 /"
                },
                "tableType": {
                  "type": "integer",
                  "description": "1默认，2自定义 1:默认 /"
                },
                "isPredef": {
                  "type": "boolean",
                  "description": "1默认，2自定义 1:默认 /"
                },
                "dateType": {
                  "type": "integer",
                  "description": "1 动态、2 静态"
                },
                "endDate": {
                  "type": "string",
                  "description": "1 动态、2 静态"
                },
                "endDayFromToday": {
                  "type": "integer",
                  "description": "1 动态、2 静态"
                },
                "startDate": {
                  "type": "string",
                  "description": "1 动态、2 静态"
                },
                "startDayFromToday": {
                  "type": "integer",
                  "description": "1 动态、2 静态"
                },
                "profileNameList": {
                  "type": "array",
                  "items": {
                    "type": "string"
                  },
                  "description": "1 动态、2 静态"
                },
                "eventConfCondDto": {
                  "type": "object",
                  "properties": {
                    "behaviorContents": {
                      "type": "array",
                      "items": {
                        "x-source-type": "BehaviorContent",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                      },
                      "description": "行为分析，查询 /"
                    },
                    "filtrate": {
                      "type": "array",
                      "items": {
                        "x-source-type": "Filtrate",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                      },
                      "description": "过滤条件 /"
                    }
                  },
                  "x-source-type": "EventConfigConditionsDto",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/dto/event/EventConfigConditionsDto.java",
                    "line": 1
                  },
                  "description": "***************** 虚拟事件/属性 开始 ****************************"
                },
                "metaProfList": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "productKey": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "appKey": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "profileName": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "name": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "profileType": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "profileClassify": {
                        "type": "integer",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "propertiesName": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "expression": {
                        "type": "string",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "relateType": {
                        "type": "integer",
                        "description": "@Author zc @Description TODO @Date 2022/11/11 19:56 /"
                      },
                      "eventList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "sample": {
                        "type": "integer"
                      },
                      "isShow": {
                        "type": "integer"
                      },
                      "productKeyList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "appKeyList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "profileNameList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "profileTypeList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "profileClassifyList": {
                        "type": "array",
                        "items": {
                          "type": "integer"
                        }
                      },
                      "expressSql": {
                        "type": "string"
                      },
                      "searchText": {
                        "type": "string"
                      },
                      "eventNameList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      },
                      "nameNotNull": {
                        "type": "boolean"
                      },
                      "tableType": {
                        "type": "integer"
                      },
                      "tableName": {
                        "type": "string"
                      },
                      "language": {
                        "type": "string"
                      },
                      "idList": {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    },
                    "x-source-type": "ProfileDto",
                    "x-source": {
                      "project": "bi-docker",
                      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/profile/ProfileDto.java",
                      "line": 1
                    }
                  },
                  "description": "***************** 虚拟事件/属性 开始 ****************************"
                },
                "forexRateProfileMap": {
                  "type": "object",
                  "properties": {
                    "id": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "prokey": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "appkey": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "profileId": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "profileName": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "tableType": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "metaProfileName": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "metaProfileClassify": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "metaProfilePropertiesName": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "calculationMethod": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "dynamicCurrencyProfile": {
                      "type": "string",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "dynamicCurrencyProfileClassify": {
                      "type": "integer",
                      "description": "@TableName forex_rate_profile_map /"
                    },
                    "dynamicCurrencyProfilePropertiesName": {
                      "type": "string"
                    },
                    "fixedCurrencyType": {
                      "type": "string"
                    },
                    "targetCurrencyType": {
                      "type": "string"
                    },
                    "createAt": {
                      "type": "string",
                      "description": "日期格式按调用页面/后端约定，不能推测时区"
                    }
                  },
                  "x-source-type": "ForexRateProfileMapDto",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/dto/profile/ForexRateProfileMapDto.java",
                    "line": 1
                  },
                  "description": "***************** 汇率事件/属性 ****************************"
                },
                "isCoreConfigIndicator": {
                  "type": "boolean",
                  "description": "***********************ab 核心指标所需参数*********************************"
                },
                "propertiesName": {
                  "type": "string",
                  "description": "***********************ab 核心指标所需参数*********************************"
                },
                "relation": {
                  "type": "string",
                  "description": "***********************ab 核心指标所需参数*********************************"
                },
                "indFormat": {
                  "type": "integer",
                  "description": "***********************ab 核心指标所需参数*********************************"
                },
                "summaryConfig": {
                  "type": "object",
                  "properties": {
                    "summaryType": {
                      "type": "integer"
                    },
                    "isFullTime": {
                      "type": "boolean"
                    }
                  },
                  "x-source-type": "SummaryConfig",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/vo/analysis/SummaryConfig.java",
                    "line": 1
                  },
                  "description": "阶段汇总配置类 /"
                },
                "userType": {
                  "type": "integer",
                  "description": "阶段汇总配置类 /"
                },
                "metricCategory": {
                  "type": "integer",
                  "description": "指标级别， 1是集团指标，2是产品指标，不传就默认是事件 /"
                },
                "metricFiltrate": {
                  "type": "object",
                  "properties": {
                    "filtrateList": {
                      "type": "array",
                      "items": {
                        "x-source-type": "Filtrate",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                      }
                    },
                    "logicRelation": {
                      "type": "string"
                    },
                    "relation": {
                      "type": "string"
                    }
                  },
                  "x-source-type": "FiltrateCondition",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/vo/FiltrateCondition.java",
                    "line": 1
                  },
                  "description": "指标的过滤条件 /"
                },
                "fromEventMetric": {
                  "type": "boolean",
                  "description": "指标的过滤条件 /"
                },
                "timeType": {
                  "type": "integer",
                  "description": "指标的过滤条件 /"
                }
              },
              "x-source-type": "BehaviorContent",
              "x-source": {
                "project": "bi-docker",
                "file": "da-dao/src/main/java/com/reyun/da/dao/vo/BehaviorContent.java",
                "line": 1
              },
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            },
            "endTime": {
              "type": "string",
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            },
            "timeType": {
              "type": "integer",
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            },
            "startTime": {
              "type": "string",
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            },
            "dateType": {
              "type": "integer",
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            },
            "endDayFromToday": {
              "type": "integer",
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            },
            "startDayFromToday": {
              "type": "integer",
              "description": "@Author zc @Description TODO @Date 2023/8/21 19:17 /"
            }
          },
          "x-source-type": "CdpAudienceTagResultDto",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/dto/usertag/CdpAudienceTagResultDto.java",
            "line": 1
          }
        },
        "description": "状态：1.QUEUED，2.RUNNING，3.FAILED，4.SUCCESS，5.DELETED /"
      },
      "productKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "状态：1.QUEUED，2.RUNNING，3.FAILED，4.SUCCESS，5.DELETED /"
      },
      "entity": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "主体名称 对应 entityType /"
          },
          "type": {
            "type": "integer",
            "description": "0.预置主体 1.自定义主体 【标签场景】 /"
          },
          "tableType": {
            "type": "integer",
            "description": "0.事件 1.用户 /"
          },
          "profileType": {
            "type": "string",
            "description": "string,decimal,boolean,array,date /"
          },
          "profileClassify": {
            "type": "integer",
            "description": "0.自定义属性 1.预置属性 2.虚拟属性 /"
          },
          "parentProfileName": {
            "type": "string",
            "description": "0.自定义属性 1.预置属性 2.虚拟属性 /"
          },
          "propertiesName": {
            "type": "string",
            "description": "0.自定义属性 1.预置属性 2.虚拟属性 /"
          },
          "isCustomId": {
            "type": "boolean",
            "description": "0.自定义属性 1.预置属性 2.虚拟属性 /"
          }
        },
        "x-source-type": "UserTagEntity",
        "x-source": {
          "project": "bi-docker",
          "file": "da-dao/src/main/java/com/reyun/da/dao/dto/usertag/UserTagEntity.java",
          "line": 1
        },
        "description": "状态：1.QUEUED，2.RUNNING，3.FAILED，4.SUCCESS，5.DELETED /"
      },
      "timeType": {
        "type": "integer",
        "description": "状态：1.QUEUED，2.RUNNING，3.FAILED，4.SUCCESS，5.DELETED /"
      },
      "endTime": {
        "type": "string",
        "description": "状态：1.QUEUED，2.RUNNING，3.FAILED，4.SUCCESS，5.DELETED /"
      },
      "startTime": {
        "type": "string",
        "description": "状态：1.QUEUED，2.RUNNING，3.FAILED，4.SUCCESS，5.DELETED /"
      },
      "distinctNum": {
        "type": "integer",
        "description": "去重总数 /"
      },
      "module": {
        "type": "integer",
        "description": "1:自定义分析;2:在线参数;3:ab试验;4:open_api接口;5:ab-shunt /"
      },
      "moduleId": {
        "type": "integer",
        "description": "业务模块枚举值对应的Id /"
      },
      "createByName": {
        "type": "string",
        "description": "/"
      },
      "createAt": {
        "type": "string",
        "description": "/"
      },
      "updateAt": {
        "type": "string",
        "description": "/"
      },
      "entityType": {
        "type": "string",
        "description": "/"
      },
      "entitySource": {
        "type": "string",
        "description": "/"
      },
      "currentTimeZone": {
        "type": "string",
        "description": "/"
      },
      "currentTimeZoneHour": {
        "type": "string",
        "description": "/"
      }
    },
    "x-source-type": "CdpAudienceTagDetailDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/usertag/CdpAudienceTagDetailDto.java",
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
  "backend_type": "ResultModel",
  "backend_schema": {
    "type": "object",
    "properties": {
      "code": {
        "type": "integer",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "msg": {
        "type": "string",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "timeZone": {
        "type": "string",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "data": {
        "x-source-type": "T",
        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      },
      "msgType": {
        "type": "integer",
        "description": "通用返回对象 Created by macro on 2019/4/19. /"
      }
    },
    "x-source-type": "ResultModel",
    "x-source": {
      "project": "bi-docker",
      "file": "da-common/src/main/java/com/reyun/da/common/api/ResultModel.java",
      "line": 1
    }
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
