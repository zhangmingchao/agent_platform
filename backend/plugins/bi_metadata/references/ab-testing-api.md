# ab-testing 接口参考

自动对照前后端源码生成。目录状态不等于线上验证；调用前使用 `SolarCatalog` 的 describe 获取完整契约。

| 接口 ID | 方法与路径 | 用途 | 状态 / 操作 |
|---|---|---|---|
| `rule.post.portal_experiment_add.72503f7b` | POST /portal/experiment/add | Add 添加试验 | matched / write |
| `rule.get.portal_experiment_checkInputDebugDevice.629f07e0` | GET /portal/experiment/checkInputDebugDevice | 校验调试设备 | matched / read |
| `rule.get.portal_experiment_checkName.8fdeb554` | GET /portal/experiment/checkName | 试验名称检查 | matched / read |
| `rule.get.portal_experiment_checkSelectedParam.f4446652` | GET /portal/experiment/checkSelectedParam | 判断当前参数是否在其他试验层中使用 | matched / read |
| `rule.get.portal_experiment_del.3d9d18f1` | GET /portal/experiment/del | Delete 试验删除 | matched / write |
| `rule.get.portal_experiment_detail.fd792f7e` | GET /portal/experiment/detail | 获取试验详情 | matched / read |
| `rule.post.portal_experiment_experimentLayer_add.38ed5576` | POST /portal/experiment/experimentLayer/add | AddExperimentLayer 添加试验层 | matched / write |
| `rule.get.portal_experiment_experimentLayer_checkExperiment.714c4bfe` | GET /portal/experiment/experimentLayer/checkExperiment | CheckExperimentLayerCanDelete 检查试验层关联的试验 | matched / read |
| `rule.get.portal_experiment_experimentLayer_checkName.2769c0c7` | GET /portal/experiment/experimentLayer/checkName | CheckExperimentLayerName 检查试验层名称是否已存在 | matched / read |
| `rule.post.portal_experiment_experimentLayer_delete.55034072` | POST /portal/experiment/experimentLayer/delete | DeleteExperimentLayer 删除试验层 | matched / write |
| `rule.get.portal_experiment_experimentLayer_detail.ebbbae25` | GET /portal/experiment/experimentLayer/detail | GetExperimentLayer 获取试验层详情 | matched / read |
| `rule.get.portal_experiment_experimentLayer_getValidFlowValue.377f2a1a` | GET /portal/experiment/experimentLayer/getValidFlowValue | GetValidFlowValue 获取试验层的可用流量 | matched / read |
| `rule.get.portal_experiment_experimentLayer_list.0e6d5acd` | GET /portal/experiment/experimentLayer/list | GetExperimentLayerList 获取试验层列表 | matched / read |
| `rule.get.portal_experiment_experimentLayer_listAvailable.37f2fa9a` | GET /portal/experiment/experimentLayer/listAvailable | GetAvailableExperimentLayerList 获取可用试验层列表 | matched / read |
| `rule.post.portal_experiment_experimentLayer_modify.abceb9f9` | POST /portal/experiment/experimentLayer/modify | ModifyExperimentLayer 编辑试验层 | matched / write |
| `rule.get.portal_experiment_getExperimentGroupList.284e288e` | GET /portal/experiment/getExperimentGroupList | GetExperimentGroupList 获取当前试验下的实验组 | matched / read |
| `rule.get.portal_experiment_list.09374427` | GET /portal/experiment/list | List 试验列表 | matched / read |
| `rule.post.portal_experiment_modify.fc44991b` | POST /portal/experiment/modify | 编辑试验 | matched / write |
| `rule.post.portal_experiment_pushOut.315c354f` | POST /portal/experiment/pushOut | PushOut 试验推全 | matched / write |
| `rule.post.portal_experiment_pushOutCheck.f5fbf0ba` | POST /portal/experiment/pushOutCheck | PushOutCheck 试验推全检查 | matched / read |
| `rule.get.portal_experiment_report_basicInfo.77abcfa5` | GET /portal/experiment/report/basicInfo | ReportBasicInfo 报告基础信息 | matched / read |
| `rule.post.portal_experiment_report_enterGroupSql.7deef10f` | POST /portal/experiment/report/enterGroupSql | EnterGroupSql 获取进组sql | backend_only / read |
| `rule.post.portal_experiment_report_indDetailByDay.76567f9e` | POST /portal/experiment/report/indDetailByDay | ReportIndicatorsDetail 指标趋势图 | matched / read |
| `rule.post.portal_experiment_report_indSummary.189819d3` | POST /portal/experiment/report/indSummary | ReportSummaryInd 指标汇总 | matched / read |
| `rule.post.portal_experiment_report_retention.9f12e611` | POST /portal/experiment/report/retention | ReportRetention 试验报告 留存指标 | matched / read |
| `rule.post.portal_experiment_report_sampleComputer.9e560d83` | POST /portal/experiment/report/sampleComputer | 样本计算器计算指标均值和指标标准差 / | matched / read |
| `rule.post.portal_experiment_setOffline.8245ee25` | POST /portal/experiment/setOffline | SetOffline 试验下线 | matched / write |
| `rule.post.portal_experiment_setOfflineCheck.143ba917` | POST /portal/experiment/setOfflineCheck | SetOfflineCheck 试验下线检查，此时不走真实的下线逻辑， | matched / read |
| `rule.get.portal_experiment_setOnline.820548b1` | GET /portal/experiment/setOnline | SetOnline 试验上线 | matched / write |
| `rule.post.portal_experiment_tempSave.37eb5391` | POST /portal/experiment/tempSave | 暂存试验 | matched / write |
| `rule.get.portal_experiment_urlVerify.2e1ce4a6` | GET /portal/experiment/urlVerify | UrlVerify 试验url校验 | matched / read |

## 使用方式

每个接口的参数、返回声明及源码位置见 `references/api/<接口ID>.md`，或调用 SolarCatalog.describe。先检索再读取单个契约，不应一次读取所有接口。
