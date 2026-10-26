# bi.post.external_report_findPermList.2cadb6e8

findReportListApi

- 服务：bi；后端相对路径：`/external/report/findPermList`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：internal；Schema：partial。
- 说明：测试、维护、认证或服务间调用 Controller，非 Agent 业务入口
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/nologin/NoLoginController.java:164。

请求参数（query / body / path）：

```json
{
  "query_schema": {
    "type": "object",
    "properties": {
      "apiKey": {
        "type": "string"
      }
    },
    "required": [
      "apiKey"
    ],
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
  "frontend_schemas": []
}
```
