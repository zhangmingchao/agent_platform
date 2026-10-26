# bi.post.reportForm_findList.f46424f3

列表查询接口

- 服务：bi；后端相对路径：`/reportForm/findList`；方法：POST。
- 前端路径：/bi-docker/api/reportForm/findList。
- 状态：matched；操作：read；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/ReportFormMenuController.java:132。
- 前端源码：solar-engine-fe/src/api/modules/anasysisReport/index.ts:55；方法 list；参数类型 `List`。

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
        "type": "integer",
        "description": "@JsonInclude(JsonInclude.Include.NON_NULL)"
      },
      "searchConditionId": {
        "type": "integer"
      },
      "menuName": {
        "type": "string",
        "description": "@JsonInclude(JsonInclude.Include.NON_NULL)"
      },
      "orderNum": {
        "type": "integer",
        "description": "@JsonInclude(JsonInclude.Include.NON_NULL)"
      },
      "isDel": {
        "type": "integer",
        "description": "@JsonInclude(JsonInclude.Include.NON_NULL)"
      },
      "createAt": {
        "type": "string",
        "description": "@JsonInclude(JsonInclude.Include.NON_NULL)"
      },
      "updateAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "userId": {
        "type": "integer"
      },
      "userIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "createBy": {
        "type": "integer"
      },
      "updateBy": {
        "type": "integer"
      },
      "parentId": {
        "type": "integer"
      },
      "menuType": {
        "type": "integer"
      },
      "productKey": {
        "type": "string"
      },
      "appIds": {
        "type": "string"
      },
      "isAllApp": {
        "type": "integer"
      },
      "reportCreateType": {
        "type": "integer"
      },
      "authViewType": {
        "type": "integer"
      },
      "reportSourceId": {
        "type": "integer"
      },
      "isShow": {
        "type": "boolean"
      },
      "analysisBodyId": {
        "type": "integer"
      },
      "analyseType": {
        "type": "integer"
      },
      "moduleType": {
        "type": "integer"
      },
      "createUser": {
        "type": "string"
      },
      "reportIds": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "status": {
        "type": "integer"
      },
      "childMenuList": {
        "type": "array",
        "items": {
          "x-source-type": "ReportFormMenuVo",
          "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
        }
      },
      "searchCondition": {
        "type": "string"
      },
      "appCode": {
        "type": "string"
      },
      "searchContent": {
        "type": "string"
      },
      "userInfoList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer"
            },
            "userName": {
              "type": "string"
            },
            "createByNameList": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "createEmailList": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "globalDeploySwitch": {
              "type": "integer"
            },
            "email": {
              "type": "string"
            },
            "mobile": {
              "type": "string"
            },
            "companyName": {
              "type": "string"
            },
            "currency": {
              "type": "string"
            },
            "timeZone": {
              "type": "string"
            },
            "type": {
              "type": "integer"
            },
            "status": {
              "type": "integer"
            },
            "createdAt": {
              "type": "string",
              "description": "日期格式按调用页面/后端约定，不能推测时区"
            },
            "updatedAt": {
              "type": "string",
              "description": "日期格式按调用页面/后端约定，不能推测时区"
            },
            "effectiveAt": {
              "type": "string",
              "description": "日期格式按调用页面/后端约定，不能推测时区"
            },
            "lastLoginAt": {
              "type": "string",
              "description": "日期格式按调用页面/后端约定，不能推测时区"
            },
            "firstLoginAt": {
              "type": "string",
              "description": "日期格式按调用页面/后端约定，不能推测时区"
            },
            "apiKey": {
              "type": "string"
            },
            "userCode": {
              "type": "string"
            },
            "currencySymbol": {
              "type": "string"
            },
            "loginUserId": {
              "type": "integer"
            },
            "password": {
              "type": "string"
            },
            "fullName": {
              "type": "string"
            },
            "headImg": {
              "type": "string"
            },
            "parentId": {
              "type": "integer"
            },
            "departName": {
              "type": "string"
            },
            "departId": {
              "type": "integer"
            },
            "isDel": {
              "type": "integer"
            },
            "isShow": {
              "type": "integer"
            },
            "createAt": {
              "type": "string",
              "description": "日期格式按调用页面/后端约定，不能推测时区"
            },
            "updateAt": {
              "type": "string",
              "description": "日期格式按调用页面/后端约定，不能推测时区"
            },
            "code": {
              "type": "string"
            },
            "adminPwd": {
              "type": "string"
            },
            "productIds": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "appList": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "id": {
                    "type": "integer",
                    "description": "/"
                  },
                  "appkey": {
                    "type": "string",
                    "description": "/"
                  },
                  "name": {
                    "type": "string",
                    "description": "/"
                  },
                  "createrEmail": {
                    "type": "string",
                    "description": "/"
                  },
                  "createrAccount": {
                    "type": "integer",
                    "description": "/"
                  },
                  "authViewType": {
                    "type": "integer",
                    "description": "/"
                  },
                  "updateBy": {
                    "type": "integer",
                    "description": "/"
                  },
                  "roleId": {
                    "type": "integer"
                  },
                  "roleIdList": {
                    "type": "array",
                    "items": {
                      "type": "integer"
                    }
                  },
                  "isDel": {
                    "type": "integer"
                  },
                  "isDebug": {
                    "type": "integer"
                  },
                  "debugTime": {
                    "type": "string",
                    "description": "日期格式按调用页面/后端约定，不能推测时区"
                  },
                  "updateAt": {
                    "type": "string",
                    "description": "日期格式按调用页面/后端约定，不能推测时区"
                  },
                  "createAt": {
                    "type": "string",
                    "description": "日期格式按调用页面/后端约定，不能推测时区"
                  },
                  "delPermission": {
                    "type": "boolean"
                  },
                  "editPermission": {
                    "type": "boolean"
                  },
                  "orgId": {
                    "type": "integer"
                  },
                  "accountList": {
                    "type": "array",
                    "items": {
                      "type": "integer"
                    }
                  },
                  "userInfoInfoList": {
                    "type": "array",
                    "items": {
                      "x-source-type": "UserInfo",
                      "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
                    }
                  }
                },
                "x-source-type": "App",
                "x-source": {
                  "project": "bi-docker",
                  "file": "da-dao/src/main/java/com/reyun/da/dao/model/App.java",
                  "line": 1
                }
              }
            },
            "createBy": {
              "type": "integer"
            },
            "disablePermission": {
              "type": "boolean"
            },
            "editPermission": {
              "type": "boolean"
            },
            "updateBy": {
              "type": "integer"
            },
            "reportKey": {
              "type": "string"
            },
            "orgId": {
              "type": "integer"
            },
            "userIds": {
              "type": "array",
              "items": {
                "type": "integer"
              },
              "description": "后端查询使用"
            },
            "calcDays": {
              "type": "integer",
              "description": "后端查询使用"
            },
            "groupAdminId": {
              "type": "integer",
              "description": "后端查询使用"
            },
            "city": {
              "type": "string",
              "description": "后端查询使用"
            },
            "tenantId": {
              "type": "integer",
              "description": "后端查询使用"
            },
            "tenantCode": {
              "type": "string",
              "description": "后端查询使用"
            },
            "tenantEmail": {
              "type": "string",
              "description": "后端查询使用"
            },
            "parentList": {
              "type": "array",
              "items": {
                "type": "integer"
              },
              "description": "后端查询使用"
            },
            "selfEventsUploadLimit": {
              "type": "integer",
              "description": "后端查询使用"
            },
            "roleIds": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "后端查询使用"
            }
          },
          "x-source-type": "UserInfo",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/model/UserInfo.java",
            "line": 1
          }
        }
      },
      "roleIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "createByStr": {
        "type": "string"
      },
      "copyPermission": {
        "type": "boolean"
      },
      "editPermission": {
        "type": "boolean"
      },
      "delPermission": {
        "type": "boolean"
      },
      "newMenuName": {
        "type": "string"
      },
      "isAdmin": {
        "type": "boolean"
      },
      "showStyle": {
        "type": "integer"
      },
      "analyseTypeList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "moduleTypeList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "saveColumns": {
        "type": "string"
      },
      "entityType": {
        "type": "string"
      },
      "removeIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "productKeyList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "createByNameList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "createEmailList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "productIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "appIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "createByList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "analysisType": {
        "type": "integer"
      },
      "pageNum": {
        "type": "integer"
      },
      "pageSize": {
        "type": "integer"
      },
      "startDate": {
        "type": "string"
      },
      "endDate": {
        "type": "string"
      },
      "searchText": {
        "type": "string"
      },
      "isApi": {
        "type": "boolean"
      },
      "analysisTypeList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "createAtStart": {
        "type": "string"
      },
      "createAtEnd": {
        "type": "string"
      },
      "orderBy": {
        "type": "string"
      },
      "orderType": {
        "type": "string"
      },
      "createdEmailList": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "currentTimeZoneOffset": {
        "type": "string"
      },
      "systemType": {
        "type": "string"
      }
    },
    "x-source-type": "ReportFormMenuVo",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/ReportFormMenuVo.java",
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
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "analyseType": {
            "type": "number",
            "description": "分析类型"
          },
          "analyseName": {
            "type": "string",
            "description": "分析名称"
          },
          "list": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "searchConditionId": {
                  "type": "number",
                  "description": "报表对应的搜索条件id"
                },
                "menuName": {
                  "type": "string",
                  "description": "报表名称"
                },
                "userId": {
                  "type": "number",
                  "description": "创建人"
                },
                "productKey": {
                  "type": "string",
                  "description": "产品key"
                },
                "analyseType": {
                  "type": "number",
                  "description": "分析类型"
                },
                "appIds": {
                  "type": "string",
                  "description": "相关应用"
                },
                "isAllApp": {
                  "type": "number"
                },
                "id": {
                  "anyOf": [
                    {
                      "type": "number"
                    },
                    {
                      "type": "string",
                      "const": ""
                    }
                  ],
                  "description": "报表主键ID"
                }
              }
            },
            "description": "报表信息"
          },
          "analysis": {
            "type": "array",
            "items": {
              "x-unresolved": "any"
            },
            "description": "分析报表信息"
          },
          "roi": {
            "type": "array",
            "items": {
              "x-unresolved": "any"
            },
            "description": "ROI报表信息"
          },
          "attr": {
            "type": "array",
            "items": {
              "x-unresolved": "any"
            },
            "description": "归因报表信息"
          }
        }
      }
    }
  ]
}
```
