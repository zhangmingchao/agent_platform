# rule-config 接口参考

自动对照前后端源码生成。目录状态不等于线上验证；调用前使用 `SolarCatalog` 的 describe 获取完整契约。

| 接口 ID | 方法与路径 | 用途 | 状态 / 操作 |
|---|---|---|---|
| `rule.get.api_health_portalDataHandlerCheck.0b19be01` | GET /api/health/portalDataHandlerCheck | HealthCheck | backend_only / internal |
| `rule.post.config_get.ff340c00` | POST /config/get | func | backend_only / internal |
| `rule.post.config_global_disableRecordLog.7a4dc435` | POST /config/global/disableRecordLog | config.GetDisableRecordLogWithPercent | backend_only / internal |
| `rule.post.config_global_info.ca1d81b4` | POST /config/global/info | GlobalConfigInfo 全局配置 | backend_only / internal |
| `rule.post.config_multilink_get.08edb844` | POST /config/multilink/get | func | backend_only / internal |
| `rule.post.config_multilink_v1_get.c7edcef6` | POST /config/multilink/v1/get | func | backend_only / internal |
| `rule.post.config_openEngineLog.523f1102` | POST /config/openEngineLog | OpenEngineLog 打开引擎错误日志 | backend_only / internal |
| `rule.post.config_v1_get.f59de1d5` | POST /config/v1/get | func | backend_only / internal |
| `rule.get.i18nGet.d5b4dc07` | GET /i18nGet | I18nGet | backend_only / internal |
| `rule.get.metrics.b886a86e` | GET /metrics | gin.WrapH | backend_only / internal |
| `rule.post.portal_api_audienceDeleteNotify.84dbc8ca` | POST /portal/api/audienceDeleteNotify | AudienceDeleteNotify 人群删除通知 | backend_only / internal |
| `rule.post.portal_app_offline.a60310b9` | POST /portal/app/offline | app.Offline | backend_only / internal |
| `rule.get.portal_configDistributionRule_configDistributionGroup_conflictGroup.1619d472` | GET /portal/configDistributionRule/configDistributionGroup/conflictGroup | FindConflictGroup 获取冲突分组列表 | matched / read |
| `rule.post.portal_configDistributionRule_configDistributionGroup_saveConflictGroup.266d8998` | POST /portal/configDistributionRule/configDistributionGroup/saveConflictGroup | SaveConflictGroup 保存冲突分组列表 | matched / write |
| `rule.get.portal_configDistributionRule_conflictRule.2158c347` | GET /portal/configDistributionRule/conflictRule | FindConflictRule 获取冲突规则列表 | matched / read |
| `rule.get.portal_configDistributionRule_deleteRule.4cef650d` | GET /portal/configDistributionRule/deleteRule | SetRuleDelete 规则删除 | matched / write |
| `rule.get.portal_configDistributionRule_detail.89893944` | GET /portal/configDistributionRule/detail | GetRuleDetail 获取规则详情 | matched / read |
| `rule.get.portal_configDistributionRule_findPofilesByEvents.45adaecf` | GET /portal/configDistributionRule/findPofilesByEvents | 分流主体自定义ID获取 | frontend_only / unverified |
| `rule.get.portal_configDistributionRule_getRuleStatusInfo.e2768ae8` | GET /portal/configDistributionRule/getRuleStatusInfo | GetRuleStatusInfo 获取规则状态信息 | matched / read |
| `rule.get.portal_configDistributionRule_list.1a3afd6c` | GET /portal/configDistributionRule/list | GetRuleList 获取规则列表 | matched / read |
| `rule.post.portal_configDistributionRule_modify.fc9c80d0` | POST /portal/configDistributionRule/modify | ModifyRule 规则修改 | matched / write |
| `rule.get.portal_configDistributionRule_offline.7159b3da` | GET /portal/configDistributionRule/offline | SetRuleOffline 规则下线 | matched / write |
| `rule.get.portal_configDistributionRule_online.17cb0f01` | GET /portal/configDistributionRule/online | SetRuleOnline 规则上线 | matched / write |
| `rule.get.portal_configDistributionRule_ruleGroup_getFileUploadTemplate.d889f35d` | GET /portal/configDistributionRule/ruleGroup/getFileUploadTemplate | GetFileUploadTemplate 获取文件上传下载模板 | backend_only / special |
| `rule.get.portal_configDistributionRule_ruleGroup_initRuleGroupId.3da50144` | GET /portal/configDistributionRule/ruleGroup/initRuleGroupId | 分组id生成 | matched / write |
| `rule.post.portal_configDistributionRule_ruleGroup_notifyUpsAudienceTaskStatus.cc1cb8ce` | POST /portal/configDistributionRule/ruleGroup/notifyUpsAudienceTaskStatus | config_distribution.NotifyUpsAudienceTaskStatus | backend_only / internal |
| `rule.get.portal_configDistributionRule_ruleGroup_setAudienceTaskDone.adb47220` | GET /portal/configDistributionRule/ruleGroup/setAudienceTaskDone | SetAudienceTaskDone 设置分群任务完成状态 | backend_only / write |
| `rule.get.portal_configDistributionRule_ruleNameCheck.68dcd2fb` | GET /portal/configDistributionRule/ruleNameCheck | RuleNameCheck 获取规则状态信息 | matched / read |
| `rule.post.portal_configDistributionRule_save.9862189b` | POST /portal/configDistributionRule/save | SaveRule 添加规则 | matched / write |
| `rule.post.portal_configDistributionRule_saveCheck.a5a065c3` | POST /portal/configDistributionRule/saveCheck | SaveCheckRule 添加规则 | matched / read |
| `rule.get.portal_params_abRefList.79050d88` | GET /portal/params/abRefList | GetExperimentByParamId 根据参数ID获取实验 | matched / read |
| `rule.post.portal_params_add.712db55b` | POST /portal/params/add | AddParam 添加参数 | matched / write |
| `rule.post.portal_params_delete.6746b846` | POST /portal/params/delete | DeleteParam 删除参数 | matched / write |
| `rule.get.portal_params_detail.e6e1cd7c` | GET /portal/params/detail | GetParamDetail 获取参数详情 | matched / read |
| `rule.get.portal_params_list.e3a27a83` | GET /portal/params/list | GetParamInfoList 获取参数列表 | matched / read |
| `rule.get.portal_params_ruleRefList.70871504` | GET /portal/params/ruleRefList | GetRuleByParamId 根据参数ID获取规则 | matched / read |
| `rule.get.portal_params_selectParamList.cfb6b7d8` | GET /portal/params/selectParamList | GetSelectParamList 获取参数下拉列表 | matched / read |
| `rule.get.portal_params_selectValueList.da4bf25a` | GET /portal/params/selectValueList | GetSelectParamValueList 获取参数值下拉列表 | matched / read |
| `rule.post.portal_params_update.767cbc4f` | POST /portal/params/update | UpdateParam 更新参数 | matched / write |
| `rule.get.portal_params_verifyParamName.2468a04b` | GET /portal/params/verifyParamName | VerifyParamName 验证参数名称 | matched / read |

## 使用方式

每个接口的参数、返回声明及源码位置见 `references/api/<接口ID>.md`，或调用 SolarCatalog.describe。先检索再读取单个契约，不应一次读取所有接口。
