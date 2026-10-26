# bi.post.boardMenu_findPermList.6ab6ec88

findPermList

- 服务：bi；后端相对路径：`/boardMenu/findPermList`；方法：POST。
- 前端路径：未发现前端调用。
- 状态：backend_only；操作：read；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/boardreport/BoardMenuController.java:290。

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
        "description": "Created by Mybatis Generator 2021/07/13 /"
      },
      "parentId": {
        "type": "integer",
        "description": "Created by Mybatis Generator 2021/07/13 /"
      },
      "menuName": {
        "type": "string",
        "description": "Created by Mybatis Generator 2021/07/13 /"
      },
      "orderNum": {
        "type": "integer",
        "description": "Created by Mybatis Generator 2021/07/13 /"
      },
      "isDel": {
        "type": "integer",
        "description": "Created by Mybatis Generator 2021/07/13 /"
      },
      "createAt": {
        "type": "string",
        "description": "Created by Mybatis Generator 2021/07/13 /"
      },
      "updateAt": {
        "type": "string",
        "description": "日期格式按调用页面/后端约定，不能推测时区"
      },
      "userId": {
        "type": "integer"
      },
      "createBy": {
        "type": "integer"
      },
      "updateBy": {
        "type": "integer"
      },
      "menuType": {
        "type": "integer"
      },
      "productKey": {
        "type": "string",
        "description": "看板下报表数量 /"
      },
      "boardCreateType": {
        "type": "integer"
      },
      "authViewType": {
        "type": "integer"
      },
      "boardSourceId": {
        "type": "integer"
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
      "editButton": {
        "type": "boolean"
      },
      "isShow": {
        "type": "boolean"
      },
      "isAdmin": {
        "type": "boolean"
      },
      "identity": {
        "type": "integer",
        "description": "模板身份：1:默认；2：源看板;3:关联看板 /"
      },
      "version": {
        "type": "integer",
        "description": "当前的版本 /"
      },
      "lastSyncTime": {
        "type": "string",
        "description": "当前的版本 /"
      },
      "childMenuList": {
        "type": "array",
        "items": {
          "x-source-type": "BoardMenuVo",
          "x-unresolved": "类型未解析或递归；按源码位置查完整定义"
        }
      },
      "userIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "roleIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
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
      "boardReportMapList": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "id": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "boardId": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "reportFormId": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "createAt": {
              "type": "string",
              "description": "看报-报表中间表 /"
            },
            "createBy": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "layout": {
              "type": "integer",
              "description": "看报-报表中间表 /"
            },
            "menuName": {
              "type": "string",
              "description": "看报-报表中间表 /"
            },
            "searchCondition": {
              "type": "string",
              "description": "看报-报表中间表 /"
            }
          },
          "x-source-type": "BoardReportMap",
          "x-source": {
            "project": "bi-docker",
            "file": "da-dao/src/main/java/com/reyun/da/dao/model/BoardReportMap.java",
            "line": 1
          }
        }
      },
      "boardIds": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "removeIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "delStatus": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "productKeys": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "identityList": {
        "type": "array",
        "items": {
          "type": "integer"
        }
      },
      "createByName": {
        "type": "string"
      },
      "productName": {
        "type": "string"
      },
      "reportCount": {
        "type": "integer",
        "description": "看板下报表数量 /"
      },
      "boardNameLike": {
        "type": "string",
        "description": "看板下报表数量 /"
      },
      "productIdList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "看板下报表数量 /"
      },
      "createByList": {
        "type": "array",
        "items": {
          "type": "integer"
        },
        "description": "看板下报表数量 /"
      },
      "pageNum": {
        "type": "integer",
        "description": "看板下报表数量 /"
      },
      "pageSize": {
        "type": "integer",
        "description": "看板下报表数量 /"
      },
      "userName": {
        "type": "string",
        "description": "看板下报表数量 /"
      },
      "searchText": {
        "type": "string",
        "description": "看板下报表数量 /"
      },
      "startDate": {
        "type": "string",
        "description": "看板下报表数量 /"
      },
      "endDate": {
        "type": "string",
        "description": "看板下报表数量 /"
      },
      "currentTimeZoneOffset": {
        "type": "string",
        "description": "看板下报表数量 /"
      },
      "updateBefore": {
        "type": "string",
        "description": "看板下报表数量 /"
      }
    },
    "x-source-type": "BoardMenuVo",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/vo/BoardMenuVo.java",
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
  "frontend_schemas": []
}
```
