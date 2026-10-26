# bi.post.groupTemplate_templateCreateBoardBatch.7b56608e

模板创建看板-批量

- 服务：bi；后端相对路径：`/groupTemplate/templateCreateBoardBatch`；方法：POST。
- 前端路径：/bi-docker/api/groupTemplate/templateCreateBoardBatch。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/grouptemplate/GroupTemplateController.java:184。
- 前端源码：solar-engine-fe/src/api/modules/panel/index.ts:82；方法 templateCreateBoardBatch；参数类型 `any`。

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
      "productIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      },
      "boardTempIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
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
          "productList": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "productId": {
                  "type": "integer",
                  "description": "@Author zc @Description 产品 -> 报告 @Date 2023/6/14 10:56 /"
                },
                "productName": {
                  "type": "string",
                  "description": "@Author zc @Description 产品 -> 报告 @Date 2023/6/14 10:56 /"
                },
                "productKey": {
                  "type": "string",
                  "description": "@Author zc @Description 产品 -> 报告 @Date 2023/6/14 10:56 /"
                },
                "verifyResult": {
                  "type": "integer",
                  "description": "@Author zc @Description 产品 -> 报告 @Date 2023/6/14 10:56 /"
                },
                "tempList": {
                  "type": "array",
                  "items": {
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
                          "x-source-type": "GroupTempReportDto",
                          "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                        },
                        "description": "模板中 报告 /"
                      }
                    },
                    "x-source-type": "GroupTempRepDto",
                    "x-source": {
                      "project": "bi-docker",
                      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempRepDto.java",
                      "line": 1
                    }
                  },
                  "description": "模板校验封装 /"
                }
              },
              "x-source-type": "GroupTempProductDto",
              "x-source": {
                "project": "bi-docker",
                "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempProductDto.java",
                "line": 1
              }
            },
            "description": "@Author zc @Description 创建集团模板-校验响应 @Date 2023/6/14 16:33 /"
          },
          "tempReport": {
            "type": "array",
            "items": {
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
                        "x-source-type": "BehaviorViewModelSimplify",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
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
              }
            },
            "description": "@Author zc @Description 创建集团模板-校验响应 @Date 2023/6/14 16:33 /"
          },
          "verifyResult": {
            "type": "integer",
            "description": "@Author zc @Description 创建集团模板-校验响应 @Date 2023/6/14 16:33 /"
          }
        },
        "x-source-type": "GroupTempResultBatchDto",
        "x-source": {
          "project": "bi-docker",
          "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempResultBatchDto.java",
          "line": 1
        },
        "description": "@Author zc @Description TODO @Date 2023/6/15 11:06 /"
      }
    },
    "x-source-type": "GroupTempSaveBoardBatchDto",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/board/GroupTempSaveBoardBatchDto.java",
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
