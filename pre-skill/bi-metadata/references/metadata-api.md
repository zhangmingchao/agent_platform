# metadata 接口参考

自动对照前后端源码生成。目录状态不等于线上验证；调用前使用 `SolarCatalog` 的 describe 获取完整契约。

| 接口 ID | 方法与路径 | 用途 | 状态 / 操作 |
|---|---|---|---|
| `bi.post.analysisBody_add.e1f3afc5` | POST /analysisBody/add | 新增主体 | matched / write |
| `bi.get.analysisBody_bodyList.38b1ff99` | GET /analysisBody/bodyList | 产品的主体列表 | matched / read |
| `bi.get.analysisBody_delete.e5011670` | GET /analysisBody/delete | 删除主体 | matched / write |
| `bi.get.analysisBody_detail.74d90094` | GET /analysisBody/detail | 详情 | backend_only / read |
| `bi.get.analysisBody_refReport.f4222dde` | GET /analysisBody/refReport | 刷新老报表的分析主题 | backend_only / read |
| `bi.get.analysisBody_refreshProduct.4a4e433f` | GET /analysisBody/refreshProduct | 刷新老的产品新增默认分析主体 | backend_only / write |
| `bi.post.analysisBody_update.a15adf07` | POST /analysisBody/update | 编辑主体 | matched / write |
| `bi.get.analysisBody_updateDefaultBody.fffa14fc` | GET /analysisBody/updateDefaultBody | 设置默认主体 | matched / write |
| `bi.get.arith_findListByType.8fe9b4e3` | GET /arith/findListByType | 根据分析类型获取数据 | backend_only / read |
| `bi.post.buriedData_addErrorConfig.7bfbcab5` | POST /buriedData/addErrorConfig | 新增错误配置 | backend_only / write |
| `bi.post.buriedData_buriedDataList.cfe46a5d` | POST /buriedData/buriedDataList | 埋点数据列表查询 | matched / read |
| `bi.post.buriedData_buriedDataListV.fb3c536e` | POST /buriedData/buriedDataListV | 埋点数据列表查询V | backend_only / write |
| `bi.post.buriedData_buriedErrData.44b5037c` | POST /buriedData/buriedErrData | 埋点数据 错误/失败 接口下钻 | matched / write |
| `bi.get.buriedData_deleteErrorConfig.a23ce394` | GET /buriedData/deleteErrorConfig | 删除错误配置 | matched / write |
| `bi.post.buriedData_errDataVals.b36c9a5d` | POST /buriedData/errDataVals | 埋点数据 错误/失败 接口下钻的批量数据 | matched / write |
| `bi.post.buriedData_errorDataInfo.6edbd919` | POST /buriedData/errorDataInfo | 错误-下钻 | frontend_only / unverified |
| `bi.post.buriedData_errorDataTenSummary.b37ba5d4` | POST /buriedData/errorDataTenSummary | 错误数据 | frontend_only / unverified |
| `bi.get.buriedData_findRuleEventApp.c61f833f` | GET /buriedData/findRuleEventApp | 数据埋点 - 已创建该规则事件的应用列表 | frontend_only / unverified |
| `bi.post.buriedData_getEventStartPerm.c15178a7` | POST /buriedData/getEventStartPerm | 设置启用禁用状态V | matched / read |
| `bi.get.buriedData_listErrorConfig.fb26cae4` | GET /buriedData/listErrorConfig | 错误配置列表 | matched / read |
| `bi.get.buriedData_logStream.883e6627` | GET /buriedData/logStream | #endregion 日志流 | frontend_only / unverified |
| `bi.post.buriedData_setEnableStatusV.ebfbf56d` | POST /buriedData/setEnableStatusV | 设置启用禁用状态V | matched / read |
| `bi.post.collect_add.b6d6fa90` | POST /collect/add | 增加 | matched / write |
| `bi.post.collect_delete.050da9a9` | POST /collect/delete | 取消 | matched / write |
| `bi.post.debug_addDevice.ca85946a` | POST /debug/addDevice | 新增设备 | matched / write |
| `bi.post.debug_delById.75602b06` | POST /debug/delById | 删除设备 | matched / write |
| `bi.get.debug_deviceList.11087475` | GET /debug/deviceList | 设备列表 | matched / read |
| `bi.get.debug_findDebugDataList.b4a4bfbc` | GET /debug/findDebugDataList | 获取调试设备数据接口 | matched / read |
| `bi.post.debug_updDevice.33e919ca` | POST /debug/updDevice | 修改设备的名称或者标识 | matched / write |
| `bi.get.dimension_value_clear.5faeeddb` | GET /dimension/value/clear | 删除纬度值 | matched / write |
| `bi.post.dimension_value_create.d22f76aa` | POST /dimension/value/create | 表单创建维度值 | matched / write |
| `bi.post.dimension_value_createByFile.b24ec74e` | POST /dimension/value/createByFile | 新增维度值 | matched / write |
| `bi.post.dimension_value_delete.17a47eca` | POST /dimension/value/delete | 删除维度值 | matched / write |
| `bi.post.dimension_value_download.e47f99c9` | POST /dimension/value/download | 获取纬度值列表 | backend_only / special |
| `bi.post.dimension_value_list.2e8fb747` | POST /dimension/value/list | 维度属性列表 | matched / read |
| `bi.post.dimension_value_update.eb7c0236` | POST /dimension/value/update | 编辑维度值 | matched / write |
| `bi.post.eventConfig_add.4b8fa87c` | POST /eventConfig/add | 添加虚拟事件/自定义事件 | matched / write |
| `bi.get.eventConfig_checkEventName.7f98a0d0` | GET /eventConfig/checkEventName | 检查虚拟事件/自定义事件 | matched / read |
| `bi.get.eventConfig_copyEvent.29f1ff66` | GET /eventConfig/copyEvent | 关联已有事件 | matched / write |
| `bi.get.eventConfig_delete.9e8487b2` | GET /eventConfig/delete | 删除虚拟事件 | matched / write |
| `bi.get.eventConfig_detail.1026ad58` | GET /eventConfig/detail | 查询事件信息 | matched / read |
| `bi.post.eventConfig_edit.6b7a43d5` | POST /eventConfig/edit | 编辑虚拟事件 | matched / write |
| `bi.post.eventConfig_findAllEventList.8b032473` | POST /eventConfig/findAllEventList | 全量事件-分析面包屑使用 | matched / read |
| `bi.get.eventConfig_findByProductKey.44438962` | GET /eventConfig/findByProductKey | 事件管理列表 | matched / read |
| `bi.get.eventConfig_findEventList.dc2e9309` | GET /eventConfig/findEventList | 获取全量事件 | backend_only / read |
| `bi.get.eventConfig_findProfileTypeByEvent.3230d60c` | GET /eventConfig/findProfileTypeByEvent | 事件下钻 | matched / read |
| `bi.get.eventConfig_setShow.a4fde79b` | GET /eventConfig/setShow | 事件操作 | backend_only / write |
| `bi.get.eventConfig_updateName.699ebd60` | GET /eventConfig/updateName | 事件名修改 | backend_only / write |
| `bi.post.eventConfig_v2_findAllEventList.eecda189` | POST /eventConfig/v2/findAllEventList | 全量事件-分析面包屑使用 | matched / read |
| `bi.get.eventConfig_v2_setShow.f896d2f5` | GET /eventConfig/v2/setShow | 事件操作 | matched / write |
| `bi.get.eventConfig_v2_updateName.8953cbe7` | GET /eventConfig/v2/updateName | 事件名修改 | matched / write |
| `bi.get.eventGroup_detail.0b6bf4f6` | GET /eventGroup/detail | 详情 | matched / read |
| `bi.post.eventGroup_save.a8c36d4d` | POST /eventGroup/save | 保存 | matched / write |
| `bi.post.eventMetric_add.bb23a6d0` | POST /eventMetric/add | 新增 | matched / write |
| `bi.get.eventMetric_checkReport.d8911f5a` | GET /eventMetric/checkReport | 检查是否有报表引用 | matched / read |
| `bi.get.eventMetric_delete.88619fb9` | GET /eventMetric/delete | 删除 | matched / write |
| `bi.get.eventMetric_detail.42f248c9` | GET /eventMetric/detail | 详情 | backend_only / read |
| `bi.get.eventMetric_metricList.b3542ce6` | GET /eventMetric/metricList | 指标列表 | matched / read |
| `bi.get.eventMetric_updateNameById.42b51632` | GET /eventMetric/updateNameById | 新增 | matched / write |
| `bi.get.eventMetric_updateRemarkById.4b65e1a3` | GET /eventMetric/updateRemarkById | 修改名称 | matched / write |
| `bi.get.health_testProfile.fce6cab3` | GET /health/testProfile | testProfile | backend_only / internal |
| `bi.post.hotProfile_addHotProfile.2c777e12` | POST /hotProfile/addHotProfile | 新增 | matched / write |
| `bi.get.hotProfile_getHotSelectSwitch.f33fff40` | GET /hotProfile/getHotSelectSwitch | 获取收藏开关 | matched / read |
| `bi.get.hotProfile_hotProfileList.9ab90440` | GET /hotProfile/hotProfileList | 列表 | matched / read |
| `bi.post.hotProfile_removeHotProfile.d1356964` | POST /hotProfile/removeHotProfile | 取消 | matched / write |
| `bi.get.hotProfile_updateSelectSwitch.0428ba7f` | GET /hotProfile/updateSelectSwitch | 修改开关 | matched / write |
| `bi.post.profileRecort_saveRecord.f93c464d` | POST /profileRecort/saveRecord | 保存记录 | matched / write |
| `bi.post.profileType_add.48901867` | POST /profileType/add | 新增虚拟属性 | matched / write |
| `bi.post.profileType_addDimension.b1d1be76` | POST /profileType/addDimension | 新增维度属性 | matched / write |
| `bi.post.profileType_addForexRate.04ad89b2` | POST /profileType/addForexRate | 新增汇率属性 | matched / write |
| `bi.post.profileType_checkExpression.af4caf67` | POST /profileType/checkExpression | 检查属性表达式 | matched / read |
| `bi.get.profileType_checkProfileName.466e4827` | GET /profileType/checkProfileName | 检查属性标识 | matched / read |
| `bi.get.profileType_copyEventProfile.06fc77ba` | GET /profileType/copyEventProfile | 虚拟/汇率属性做关联 | matched / write |
| `bi.get.profileType_copyProfile.df317a05` | GET /profileType/copyProfile | 关联已有属性 | backend_only / write |
| `bi.get.profileType_delete.ce540084` | GET /profileType/delete | 删除虚拟属性 | matched / write |
| `bi.get.profileType_detail.535ea427` | GET /profileType/detail | 查询属性信息 | matched / read |
| `bi.post.profileType_edit.135c9110` | POST /profileType/edit | 编辑虚拟属性 | matched / write |
| `bi.post.profileType_editForexRate.b7c4a2e3` | POST /profileType/editForexRate | 编辑汇率属性 | matched / write |
| `bi.get.profileType_findAllEventProfList.9735f841` | GET /profileType/findAllEventProfList | 用户属性列表全量 | backend_only / read |
| `bi.post.profileType_findByEvent.1cc5f948` | POST /profileType/findByEvent | 获取指定事件的属性交集 | matched / read |
| `bi.post.profileType_findByProductKey.eec68c38` | POST /profileType/findByProductKey | 事件属性列表 | backend_only / read |
| `bi.get.profileType_findDimension.2760aa3c` | GET /profileType/findDimension | 维度属性列表 | matched / read |
| `bi.get.profileType_findEventConfigByEvent.3b6a9b9d` | GET /profileType/findEventConfigByEvent | 属性下钻 | matched / read |
| `bi.post.profileType_findProfileArithListByEvent.f17b1acc` | POST /profileType/findProfileArithListByEvent | 获取属性&计算方式列表 | matched / read |
| `bi.get.profileType_setShow.bd58ba86` | GET /profileType/setShow | 属性操作 | backend_only / write |
| `bi.get.profileType_updateName.ec175e3e` | GET /profileType/updateName | 属性名修改 | backend_only / write |
| `bi.post.profileType_v2_findProfileArithListByEvent.bdb685a1` | POST /profileType/v2/findProfileArithListByEvent | 用户标签 - 根据事件，获取对应的属性列表 | matched / read |
| `bi.get.profileType_v2_setShow.8a1d0255` | GET /profileType/v2/setShow | 属性操作 | matched / write |
| `bi.get.profileType_v2_updateName.d53729ba` | GET /profileType/v2/updateName | 属性名修改 | matched / write |
| `bi.post.profileUser_add.115fd38c` | POST /profileUser/add | 新增虚拟属性 | matched / write |
| `bi.post.profileUser_checkExpression.9d5a01e3` | POST /profileUser/checkExpression | 检查属性表达式 | matched / read |
| `bi.get.profileUser_checkProfileName.1883568d` | GET /profileUser/checkProfileName | 检查属性标识 | matched / read |
| `bi.get.profileUser_delete.5a5f9b4b` | GET /profileUser/delete | 删除虚拟属性 | matched / write |
| `bi.get.profileUser_detail.204f7556` | GET /profileUser/detail | 查询属性信息 | matched / read |
| `bi.post.profileUser_edit.71fcd9ca` | POST /profileUser/edit | 编辑虚拟属性 | matched / write |
| `bi.get.profileUser_findAllMeta.47042e98` | GET /profileUser/findAllMeta | 用户元属性 | matched / read |
| `bi.get.profileUser_findAllUserProfList.830220de` | GET /profileUser/findAllUserProfList | 用户属性列表全量 | backend_only / read |
| `bi.get.profileUser_findByProductKey.80d69ddd` | GET /profileUser/findByProductKey | 用户属性列表(废弃) | matched / read |
| `bi.post.profileUser_findUserProfileArithList.504b8f9a` | POST /profileUser/findUserProfileArithList | 用户分析 获取属性&计算方式列表 | matched / read |
| `bi.get.profileUser_setShow.a0c578e3` | GET /profileUser/setShow | 事件操作 | matched / write |
| `bi.get.profileUser_updateName.f5a35c95` | GET /profileUser/updateName | 属性名修改 | matched / write |
| `bi.get.refreshData_eventAndProfileClassify.8c4911e8` | GET /refreshData/eventAndProfileClassify | eventAndProfileClassify | backend_only / internal |
| `bi.get.refreshData_groupEventProfClassify.d16654c4` | GET /refreshData/groupEventProfClassify | groupEventAndGroup | backend_only / internal |

## 使用方式

每个接口的参数、返回声明及源码位置见 `references/api/<接口ID>.md`，或调用 SolarCatalog.describe。先检索再读取单个契约，不应一次读取所有接口。
