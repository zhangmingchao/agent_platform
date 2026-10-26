# bi.post.groupTemplate_templateCreateBoard.b91b9453

模板创建看板-单个

- 服务：bi；后端相对路径：`/groupTemplate/templateCreateBoard`；方法：POST。
- 前端路径：/bi-docker/api/groupTemplate/templateCreateBoard。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateController.java:194。
- 前端源码：solar-engine-fe/src/api/modules/template/index.ts:32；方法 templateCreate；参数类型 `any`。

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
      "productId": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      },
      "productKey": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      },
      "boardTempId": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      },
      "roleIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      },
      "userIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      },
      "authViewType": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      },
      "menuName": {
        "type": "string",
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      },
      "parentId": {
        "type": "integer",
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      },
      "verifyResultDto": {
        "type": "object",
        "properties": {
          "tempReport": {
            "type": "object",
            "properties": {
              "tempId": {
                "type": "integer",
                "description": "@Author zc @Description 模板报告 @Date 2023/6/14 16:43 /"
              },
              "tempName": {
                "type": "string",
                "description": "@Author zc @Description 模板报告 @Date 2023/6/14 16:43 /"
              },
              "verifyResult": {
                "type": "integer",
                "description": "@Author zc @Description 模板报告 @Date 2023/6/14 16:43 /"
              },
              "reportList": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "reportId": {
                      "type": "integer",
                      "description": "@Author zc @Description 模板中的单个报告校验实体 @Date 2023/6/12 17:27 /"
                    },
                    "menuName": {
                      "type": "string",
                      "description": "@Author zc @Description 模板中的单个报告校验实体 @Date 2023/6/12 17:27 /"
                    },
                    "layout": {
                      "type": "integer",
                      "description": "@Author zc @Description 模板中的单个报告校验实体 @Date 2023/6/12 17:27 /"
                    },
                    "behaviorViewModel": {
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
                        "participationEventList": {
                          "type": "array",
                          "items": {
                            "x-source-type": "BehaviorContent",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "参与事件 /"
                        },
                        "groups": {
                          "type": "array",
                          "items": {
                            "x-source-type": "BehaviorGroup",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "分组条件 /"
                        },
                        "userCrowds": {
                          "type": "array",
                          "items": {
                            "x-source-type": "BehaviorUserCrowd",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "分组条件 /"
                        },
                        "startDate": {
                          "type": "string",
                          "description": "分组条件 /"
                        },
                        "entityType": {
                          "type": "string",
                          "description": "分组条件 /"
                        },
                        "endDate": {
                          "type": "string",
                          "description": "分组条件 /"
                        },
                        "createDate": {
                          "type": "string",
                          "description": "分组条件 /"
                        },
                        "productKey": {
                          "type": "string",
                          "description": "产品对应的key /"
                        },
                        "appkey": {
                          "type": "string",
                          "description": "产品对应的key /"
                        },
                        "timeZone": {
                          "type": "string",
                          "description": "产品对应的key /"
                        },
                        "rdsTimeZone": {
                          "type": "string",
                          "description": "产品对应的key /"
                        },
                        "appKeyList": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": "产品对应的key /"
                        },
                        "filtrate": {
                          "type": "array",
                          "items": {
                            "x-source-type": "Filtrate",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "过滤条件 /"
                        },
                        "tagIdSet": {
                          "type": "object",
                          "additionalProperties": {
                            "x-source-type": "BehaviorFiltrate",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "过滤条件 /"
                        },
                        "window": {
                          "type": "integer",
                          "description": "过滤条件 /"
                        },
                        "retentionInterval": {
                          "type": "integer",
                          "description": "过滤条件 /"
                        },
                        "relationProfileConfig": {
                          "x-source-type": "RelationConfig",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "关联属性 /"
                        },
                        "retColList": {
                          "type": "array",
                          "items": {
                            "type": "integer"
                          },
                          "description": "关联属性 /"
                        },
                        "dateType": {
                          "type": "integer",
                          "description": "关联属性 /"
                        },
                        "startDayFromToday": {
                          "type": "integer",
                          "description": "关联属性 /"
                        },
                        "endDayFromToday": {
                          "type": "integer",
                          "description": "关联属性 /"
                        },
                        "summaryType": {
                          "type": "integer",
                          "description": "阶段汇总类型 1：综合 2阶段均值 3：阶段均值取证 4：加权平均 5:最大值 6：最小值 /"
                        },
                        "firstDayOfWeek": {
                          "type": "integer",
                          "description": "当日所在周 1，2，3，4，5，6，7(周一到周日) /"
                        },
                        "timeParticle": {
                          "type": "integer",
                          "description": "1(天) 2（小时）3（周）4（按月）5（合计） particle size /"
                        },
                        "industryIdMap": {
                          "type": "object",
                          "additionalProperties": {
                            "type": "string"
                          },
                          "description": "模型中选择的行业标签集合 /"
                        },
                        "analysisBodyVo": {
                          "x-source-type": "AnalysisBodyVo",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "分析主体标识 /"
                        },
                        "analysisModeEnum": {
                          "x-source-type": "AnalysisModeEnum",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "分析主体标识 /"
                        },
                        "metricNameMap": {
                          "type": "object",
                          "additionalProperties": {
                            "type": "string"
                          },
                          "description": "分析主体标识 /"
                        },
                        "relation": {
                          "type": "string",
                          "description": "分析主体标识 /"
                        },
                        "comparedDate": {
                          "x-source-type": "BehaviorDate",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "分析主体标识 /"
                        },
                        "compareMode": {
                          "type": "boolean",
                          "description": "分析主体标识 /"
                        },
                        "export": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": "分析主体标识 /"
                        },
                        "modeTab": {
                          "type": "integer",
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "isShowSummary": {
                          "type": "boolean",
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "isFullTime": {
                          "type": "boolean",
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "summaryMap": {
                          "type": "object",
                          "additionalProperties": {
                            "x-source-type": "SummaryConfig",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "tabNum": {
                          "type": "integer",
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "windowType": {
                          "type": "integer",
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "isTrendChart": {
                          "type": "boolean",
                          "description": "/"
                        },
                        "timeType": {
                          "type": "integer",
                          "description": "/"
                        },
                        "sourceType": {
                          "type": "string",
                          "description": "/"
                        },
                        "isApproximate": {
                          "type": "boolean",
                          "description": "是否开启了近似计算 /"
                        },
                        "boardId": {
                          "type": "integer",
                          "description": "看板id /"
                        },
                        "isChange": {
                          "type": "boolean",
                          "description": "页面筛选条件是否发生变化 /"
                        },
                        "reportId": {
                          "type": "integer",
                          "description": "报表id /"
                        },
                        "fixedTimeCompute": {
                          "type": "boolean",
                          "description": "是否开启了定时计算 /"
                        },
                        "cacheData": {
                          "type": "object",
                          "additionalProperties": {
                            "x-source-type": "Object",
                            "x-unresolved": "动态 JSON，参数形状需查调用页面"
                          },
                          "description": "是否开启了定时计算 /"
                        },
                        "boardFiltrate": {
                          "x-source-type": "Filtrate",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "是否开启了定时计算 /"
                        },
                        "validBoardFiltrate": {
                          "x-source-type": "Filtrate",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "是否开启了定时计算 /"
                        },
                        "cacheKey": {
                          "type": "string",
                          "description": "是否开启了定时计算 /"
                        },
                        "collectionName": {
                          "type": "string",
                          "description": "是否开启了定时计算 /"
                        },
                        "primary": {
                          "type": "string",
                          "description": "是否开启了定时计算 /"
                        },
                        "tabConfig": {
                          "x-source-type": "SelectTableConfig",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "是否开启了定时计算 /"
                        },
                        "startEvent": {
                          "x-source-type": "BehaviorContent",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "开始/结束事件 /"
                        },
                        "startMode": {
                          "type": "integer",
                          "description": "0.开始事件 1.结束事件 /"
                        },
                        "stepCount": {
                          "type": "integer",
                          "description": "路径分析步骤数 /"
                        },
                        "nodeCount": {
                          "type": "integer",
                          "description": "路径分析节点数 /"
                        },
                        "chartUserConfig": {
                          "x-source-type": "JSONObject",
                          "x-unresolved": "动态 JSON，参数形状需查调用页面",
                          "description": "路径分析节点数 /"
                        }
                      },
                      "x-source-type": "BehaviorViewModel",
                      "x-source": {
                        "project": "bi-docker",
                        "file": "da-dao/src/main/java/com/reyun/da/dao/vo/BehaviorViewModel.java",
                        "line": 1
                      },
                      "description": "@Author zc @Description 模板中的单个报告校验实体 @Date 2023/6/12 17:27 /"
                    },
                    "productKey": {
                      "type": "string",
                      "description": "@Author zc @Description 模板中的单个报告校验实体 @Date 2023/6/12 17:27 /"
                    },
                    "verifyResult": {
                      "type": "boolean",
                      "description": "@Author zc @Description 模板中的单个报告校验实体 @Date 2023/6/12 17:27 /"
                    },
                    "msgList": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "@Author zc @Description 模板中的单个报告校验实体 @Date 2023/6/12 17:27 /"
                    },
                    "cacheDateDto": {
                      "type": "object",
                      "properties": {
                        "cacheEventMap": {
                          "type": "object",
                          "additionalProperties": {
                            "x-source-type": "EventConfig",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "@Author zc @Description TODO @Date 2023/6/13 11:15 /"
                        },
                        "cacheEventProfileMap": {
                          "type": "object",
                          "additionalProperties": {
                            "type": "object",
                            "additionalProperties": {
                              "x-source-type": "ProfileType",
                              "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                            }
                          },
                          "description": "@Author zc @Description TODO @Date 2023/6/13 11:15 /"
                        },
                        "cacheUserProfileMap": {
                          "type": "object",
                          "additionalProperties": {
                            "x-source-type": "ProfileUser",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "@Author zc @Description TODO @Date 2023/6/13 11:15 /"
                        },
                        "cacheGroupMap": {
                          "type": "object",
                          "additionalProperties": {
                            "type": "string"
                          },
                          "description": "@Author zc @Description TODO @Date 2023/6/13 11:15 /"
                        },
                        "cacheDeviceMap": {
                          "type": "object",
                          "additionalProperties": {
                            "x-source-type": "ProfileDevice",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          }
                        },
                        "cacheMetricProductMap": {
                          "type": "object",
                          "additionalProperties": {
                            "x-source-type": "EventMetricDto",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          }
                        },
                        "cacheMetricTenant": {
                          "type": "object",
                          "additionalProperties": {
                            "x-source-type": "EventMetricDto",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          }
                        }
                      },
                      "x-source-type": "GroupTempCacheDto",
                      "x-source": {
                        "project": "bi-docker",
                        "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempCacheDto.java",
                        "line": 1
                      }
                    }
                  },
                  "x-source-type": "GroupTempReportDto",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempReportDto.java",
                    "line": 1
                  }
                },
                "description": "模板中 报告 /"
              }
            },
            "x-source-type": "GroupTempRepDto",
            "x-source": {
              "project": "bi-docker",
              "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempRepDto.java",
              "line": 1
            },
            "description": "@Author zc @Description TODO @Date 2023/6/16 15:17 /"
          },
          "tempReportCondition": {
            "type": "object",
            "properties": {
              "tempId": {
                "type": "integer",
                "description": "@Author zc @Description 模板、报告 @Date 2023/6/14 16:35 /"
              },
              "reportList": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "id": {
                      "type": "integer",
                      "description": "主键id /"
                    },
                    "templateId": {
                      "type": "integer",
                      "description": "模板id /"
                    },
                    "moduleType": {
                      "type": "integer",
                      "description": "2:ROI;3:分析;4:归因 /"
                    },
                    "reportName": {
                      "type": "string",
                      "description": "报表名称 /"
                    },
                    "analyseType": {
                      "type": "integer",
                      "description": "报表名称 /"
                    },
                    "layout": {
                      "type": "integer",
                      "description": "报表名称 /"
                    },
                    "view": {
                      "type": "integer",
                      "description": "报表名称 /"
                    },
                    "saveColumns": {
                      "type": "array",
                      "items": {
                        "type": "string"
                      },
                      "description": "报表名称 /"
                    },
                    "searchCondition": {
                      "type": "object",
                      "properties": {
                        "behaviorContents": {
                          "type": "array",
                          "items": {
                            "x-source-type": "BehaviorContentSimplify",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "行为分析，查询 /"
                        },
                        "groups": {
                          "type": "array",
                          "items": {
                            "x-source-type": "BehaviorGroupSimplify",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "分组条件 /"
                        },
                        "userCrowds": {
                          "type": "array",
                          "items": {
                            "x-source-type": "BehaviorUserCrowdSimplify",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "分组条件 /"
                        },
                        "startDate": {
                          "type": "string",
                          "description": "分组条件 /"
                        },
                        "entityType": {
                          "type": "string",
                          "description": "分组条件 /"
                        },
                        "endDate": {
                          "type": "string",
                          "description": "分组条件 /"
                        },
                        "createDate": {
                          "type": "string",
                          "description": "分组条件 /"
                        },
                        "productKey": {
                          "type": "string",
                          "description": "产品对应的key /"
                        },
                        "appkey": {
                          "type": "string",
                          "description": "产品对应的key /"
                        },
                        "filtrate": {
                          "type": "array",
                          "items": {
                            "x-source-type": "FiltrateSimplify",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "过滤条件 /"
                        },
                        "window": {
                          "type": "integer",
                          "description": "过滤条件 /"
                        },
                        "retentionInterval": {
                          "type": "integer",
                          "description": "过滤条件 /"
                        },
                        "retColList": {
                          "type": "array",
                          "items": {
                            "type": "integer"
                          },
                          "description": "过滤条件 /"
                        },
                        "dateType": {
                          "type": "integer",
                          "description": "过滤条件 /"
                        },
                        "startDayFromToday": {
                          "type": "integer",
                          "description": "过滤条件 /"
                        },
                        "endDayFromToday": {
                          "type": "integer",
                          "description": "过滤条件 /"
                        },
                        "firstDayOfWeek": {
                          "type": "integer",
                          "description": "当日所在周 1，2，3，4，5，6，7(周一到周日) /"
                        },
                        "timeParticle": {
                          "type": "integer",
                          "description": "1(天) 2（小时）3（周）4（按月）5（合计） particle size /"
                        },
                        "analysisBodyVo": {
                          "x-source-type": "AnalysisBodyVo",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "分析主体标识 /"
                        },
                        "analysisModeEnum": {
                          "x-source-type": "AnalysisModeEnum",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "分析主体标识 /"
                        },
                        "isgroups": {
                          "type": "boolean",
                          "description": "前端透传，用户分析中使用 /"
                        },
                        "relation": {
                          "type": "string",
                          "description": "@JsonProperty(defaultValue = \"and\")"
                        },
                        "comparedDate": {
                          "x-source-type": "BehaviorDate",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "@JsonProperty(defaultValue = \"and\")"
                        },
                        "windowType": {
                          "type": "integer",
                          "description": "@JsonProperty(defaultValue = \"and\")"
                        },
                        "relationProfileConfig": {
                          "x-source-type": "RelationConfig",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "@JsonProperty(defaultValue = \"and\")"
                        },
                        "retentionMode": {
                          "type": "integer",
                          "description": "@JsonProperty(defaultValue = \"and\")"
                        },
                        "modeTab": {
                          "type": "integer",
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "stepList": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          },
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "funnelTab": {
                          "type": "string",
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "timeType": {
                          "type": "integer",
                          "description": "：转化（留存）； 2：流失； /"
                        },
                        "isApproximate": {
                          "type": "boolean",
                          "description": "是否开启了近似计算 /"
                        },
                        "participationEventList": {
                          "type": "array",
                          "items": {
                            "x-source-type": "BehaviorContent",
                            "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                          },
                          "description": "路径分析新增 /"
                        },
                        "startEvent": {
                          "x-source-type": "BehaviorContent",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                          "description": "开始/结束事件 /"
                        },
                        "startMode": {
                          "type": "integer",
                          "description": "开始/结束事件 /"
                        },
                        "stepCount": {
                          "type": "integer",
                          "description": "路径分析步骤数 /"
                        },
                        "nodeCount": {
                          "type": "integer",
                          "description": "路径分析节点数 /"
                        },
                        "chartUserConfig": {
                          "x-source-type": "JSONObject",
                          "x-unresolved": "动态 JSON，参数形状需查调用页面",
                          "description": "路径分析节点数 /"
                        }
                      },
                      "x-source-type": "BehaviorViewModelSimplify",
                      "x-source": {
                        "project": "bi-docker",
                        "file": "da-dao/src/main/java/com/reyun/da/dao/vo/simplify/BehaviorViewModelSimplify.java",
                        "line": 1
                      },
                      "description": "报表名称 /"
                    },
                    "reportId": {
                      "type": "integer",
                      "description": "报表名称 /"
                    }
                  },
                  "x-source-type": "GroupTemplateDetailDto",
                  "x-source": {
                    "project": "bi-docker",
                    "file": "da-dao/src/main/java/com/reyun/da/dao/dto/grouptemplate/GroupTemplateDetailDto.java",
                    "line": 1
                  }
                },
                "description": "@Author zc @Description 模板、报告 @Date 2023/6/14 16:35 /"
              }
            },
            "x-source-type": "TempReportsDto",
            "x-source": {
              "project": "bi-docker",
              "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/TempReportsDto.java",
              "line": 1
            },
            "description": "@Author zc @Description TODO @Date 2023/6/16 15:17 /"
          },
          "verifyResult": {
            "type": "integer",
            "description": "@Author zc @Description TODO @Date 2023/6/16 15:17 /"
          }
        },
        "x-source-type": "GroupTempResultDto",
        "x-source": {
          "project": "bi-docker",
          "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempResultDto.java",
          "line": 1
        },
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      }
    },
    "x-source-type": "GroupTempSaveBoardDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempSaveBoardDto.java",
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
  "backend_type": "ResultModel<Object>",
  "backend_schema": {
    "x-source-type": "ResultModel<Object>",
    "x-unresolved": "泛型包装，查看返回结构说明"
  },
  "frontend_schemas": [
    {
      "x-unresolved": "未声明前端返回泛型"
    }
  ]
}
```
