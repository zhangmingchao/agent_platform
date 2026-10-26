# bi.post.eventGroup_save.a8c36d4d

保存

- 服务：bi；后端相对路径：`/eventGroup/save`；方法：POST。
- 前端路径：/bi-docker/api/eventGroup/save。
- 状态：matched；操作：write；Schema：partial。
- 后端源码：bi-docker/da-web/src/main/java/com/reyun/da/web/controller/datamanage/EventGroupController.java:28。
- 前端源码：solar-engine-fe/src/api/modules/analysis/index.ts:183；方法 eventGroupSave；参数类型 `any`。

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
      "productKey": {
        "type": "string"
      },
      "publicGroup": {
        "type": "object",
        "properties": {
          "groupList": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "type": "integer"
                },
                "productKey": {
                  "type": "string"
                },
                "category": {
                  "type": "integer"
                },
                "groupName": {
                  "type": "string"
                },
                "location": {
                  "type": "integer"
                },
                "eventList": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "string",
                        "description": "/"
                      },
                      "productKey": {
                        "type": "string",
                        "description": "appkey所属的产品id /"
                      },
                      "appKey": {
                        "type": "string",
                        "description": "应用key /"
                      },
                      "eventName": {
                        "type": "string",
                        "description": "虚拟事件标识 /"
                      },
                      "name": {
                        "type": "string",
                        "description": "虚拟事件自定义名称 /"
                      },
                      "eventRemark": {
                        "type": "string",
                        "description": "事件备注 /"
                      },
                      "isShow": {
                        "type": "integer",
                        "description": "是否显示 /"
                      },
                      "conditions": {
                        "type": "string",
                        "description": "条件 /"
                      },
                      "conditionsDto": {
                        "x-source-type": "EventConfigConditionsDto",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                        "description": "条件 /"
                      },
                      "eventClassify": {
                        "type": "integer",
                        "description": "事件类型。1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 /"
                      },
                      "eventClassifyText": {
                        "type": "string",
                        "description": "事件类型。1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 /"
                      },
                      "metaEventName": {
                        "type": "string",
                        "description": "事件类型。1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 /"
                      },
                      "status": {
                        "type": "integer",
                        "description": "是否接收 /"
                      },
                      "createTime": {
                        "type": "string",
                        "description": "/"
                      },
                      "updateTime": {
                        "type": "string",
                        "description": "/"
                      },
                      "location": {
                        "type": "integer",
                        "description": "在事件分组中的排序 /"
                      },
                      "isCollect": {
                        "type": "integer",
                        "description": "是否收藏 /"
                      }
                    },
                    "x-source-type": "EventConfigDto",
                    "x-source": {
                      "project": "bi-docker",
                      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/event/EventConfigDto.java",
                      "line": 1
                    }
                  }
                },
                "isDefault": {
                  "type": "integer"
                },
                "mapList": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "integer",
                        "description": "@TableName event_group_event_map /"
                      },
                      "groupId": {
                        "type": "integer",
                        "description": "@TableName event_group_event_map /"
                      },
                      "eventId": {
                        "type": "string",
                        "description": "@TableName event_group_event_map /"
                      },
                      "location": {
                        "type": "integer",
                        "description": "@TableName event_group_event_map /"
                      },
                      "createAt": {
                        "type": "string",
                        "description": "@TableName event_group_event_map /"
                      }
                    },
                    "x-source-type": "EventGroupEventMap",
                    "x-source": {
                      "project": "bi-docker",
                      "file": "da-dao/src/main/java/com/reyun/da/dao/model/EventGroupEventMap.java",
                      "line": 1
                    }
                  }
                },
                "createBy": {
                  "type": "integer"
                },
                "removeStatus": {
                  "type": "integer"
                },
                "isGetAll": {
                  "type": "boolean",
                  "description": "是否查询所有可见分组 /"
                }
              },
              "x-source-type": "EventGroupDto",
              "x-source": {
                "project": "bi-docker",
                "file": "da-dao/src/main/java/com/reyun/da/dao/dto/datamanage/EventGroupDto.java",
                "line": 1
              }
            }
          },
          "isActive": {
            "type": "integer"
          }
        },
        "x-source-type": "EventGroupCollection",
        "x-source": {
          "project": "bi-docker",
          "file": "da-dao/src/main/java/com/reyun/da/dao/dto/datamanage/EventGroupCollection.java",
          "line": 1
        }
      },
      "privateGroup": {
        "type": "object",
        "properties": {
          "groupList": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": {
                  "type": "integer"
                },
                "productKey": {
                  "type": "string"
                },
                "category": {
                  "type": "integer"
                },
                "groupName": {
                  "type": "string"
                },
                "location": {
                  "type": "integer"
                },
                "eventList": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "string",
                        "description": "/"
                      },
                      "productKey": {
                        "type": "string",
                        "description": "appkey所属的产品id /"
                      },
                      "appKey": {
                        "type": "string",
                        "description": "应用key /"
                      },
                      "eventName": {
                        "type": "string",
                        "description": "虚拟事件标识 /"
                      },
                      "name": {
                        "type": "string",
                        "description": "虚拟事件自定义名称 /"
                      },
                      "eventRemark": {
                        "type": "string",
                        "description": "事件备注 /"
                      },
                      "isShow": {
                        "type": "integer",
                        "description": "是否显示 /"
                      },
                      "conditions": {
                        "type": "string",
                        "description": "条件 /"
                      },
                      "conditionsDto": {
                        "x-source-type": "EventConfigConditionsDto",
                        "x-unresolved": "类型未解析或递归；按源码位置查完整定义",
                        "description": "条件 /"
                      },
                      "eventClassify": {
                        "type": "integer",
                        "description": "事件类型。1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 /"
                      },
                      "eventClassifyText": {
                        "type": "string",
                        "description": "事件类型。1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 /"
                      },
                      "metaEventName": {
                        "type": "string",
                        "description": "事件类型。1:预置事件;2:预定义事件;3:自定义事件;4:虚拟事件 /"
                      },
                      "status": {
                        "type": "integer",
                        "description": "是否接收 /"
                      },
                      "createTime": {
                        "type": "string",
                        "description": "/"
                      },
                      "updateTime": {
                        "type": "string",
                        "description": "/"
                      },
                      "location": {
                        "type": "integer",
                        "description": "在事件分组中的排序 /"
                      },
                      "isCollect": {
                        "type": "integer",
                        "description": "是否收藏 /"
                      }
                    },
                    "x-source-type": "EventConfigDto",
                    "x-source": {
                      "project": "bi-docker",
                      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/event/EventConfigDto.java",
                      "line": 1
                    }
                  }
                },
                "isDefault": {
                  "type": "integer"
                },
                "mapList": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": {
                        "type": "integer",
                        "description": "@TableName event_group_event_map /"
                      },
                      "groupId": {
                        "type": "integer",
                        "description": "@TableName event_group_event_map /"
                      },
                      "eventId": {
                        "type": "string",
                        "description": "@TableName event_group_event_map /"
                      },
                      "location": {
                        "type": "integer",
                        "description": "@TableName event_group_event_map /"
                      },
                      "createAt": {
                        "type": "string",
                        "description": "@TableName event_group_event_map /"
                      }
                    },
                    "x-source-type": "EventGroupEventMap",
                    "x-source": {
                      "project": "bi-docker",
                      "file": "da-dao/src/main/java/com/reyun/da/dao/model/EventGroupEventMap.java",
                      "line": 1
                    }
                  }
                },
                "createBy": {
                  "type": "integer"
                },
                "removeStatus": {
                  "type": "integer"
                },
                "isGetAll": {
                  "type": "boolean",
                  "description": "是否查询所有可见分组 /"
                }
              },
              "x-source-type": "EventGroupDto",
              "x-source": {
                "project": "bi-docker",
                "file": "da-dao/src/main/java/com/reyun/da/dao/dto/datamanage/EventGroupDto.java",
                "line": 1
              }
            }
          },
          "isActive": {
            "type": "integer"
          }
        },
        "x-source-type": "EventGroupCollection",
        "x-source": {
          "project": "bi-docker",
          "file": "da-dao/src/main/java/com/reyun/da/dao/dto/datamanage/EventGroupCollection.java",
          "line": 1
        }
      }
    },
    "x-source-type": "EventGroupWrapper",
    "x-source": {
      "project": "bi-docker",
      "file": "da-dao/src/main/java/com/reyun/da/dao/dto/datamanage/EventGroupWrapper.java",
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
