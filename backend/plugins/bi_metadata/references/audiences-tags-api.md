# audiences-tags 接口参考

自动对照前后端源码生成。目录状态不等于线上验证；调用前使用 `SolarCatalog` 的 describe 获取完整契约。

| 接口 ID | 方法与路径 | 用途 | 状态 / 操作 |
|---|---|---|---|
| `bi.get.analysisBody_deleteAllReportAndUserTag.8561a028` | GET /analysisBody/deleteAllReportAndUserTag | 根据主体ID删除关联报表和标签 | matched / write |
| `bi.get.analysisBody_getAllReportAndUserTag.52335f9b` | GET /analysisBody/getAllReportAndUserTag | 根据主体ID获取关联报表和标签 | matched / read |
| `bi.post.noLogin_audience_createAudienceBaseInfo.b92945af` | POST /noLogin/audience/createAudienceBaseInfo | createAudienceBaseInfo | backend_only / internal |
| `bi.post.noLogin_audience_uploadAudienceEntityData.4fe159b7` | POST /noLogin/audience/uploadAudienceEntityData | 创建分群 | backend_only / internal |
| `bi.get.userGroup_callBackGroupExecute.cb0f13f6` | GET /userGroup/callBackGroupExecute | 刷新分群 | backend_only / internal |
| `bi.post.userGroup_conditionGroup.56acad2e` | POST /userGroup/conditionGroup | 更新分群名称或者备注 | matched / write |
| `bi.post.userGroup_createUploadGroup.140a6ff1` | POST /userGroup/createUploadGroup | 获取分组tag | matched / write |
| `bi.get.userGroup_delGroupById.93257ca3` | GET /userGroup/delGroupById | 创建上传分群 | matched / write |
| `bi.get.userGroup_delVerify.69719007` | GET /userGroup/delVerify | delVerify | backend_only / read |
| `bi.get.userGroup_detail.462d469c` | GET /userGroup/detail | 分群列表 | matched / read |
| `bi.get.userGroup_getGroupProfileList.a627f7b7` | GET /userGroup/getGroupProfileList | getGroupProfileList | backend_only / read |
| `bi.get.userGroup_getGroupTag.b92ad768` | GET /userGroup/getGroupTag | 删除校验 | backend_only / read |
| `bi.get.userGroup_getGroupUserList.040f21f0` | GET /userGroup/getGroupUserList | 回调分群执行 | matched / read |
| `bi.post.userGroup_getGroupUserList.c9455a99` | POST /userGroup/getGroupUserList | 创建结果分群 | frontend_only / unverified |
| `bi.get.userGroup_list.3a33380c` | GET /userGroup/list | 分群列表 | matched / read |
| `bi.post.userGroup_notify.6da68355` | POST /userGroup/notify | Airflow 用户分群回调接口 - v1 | backend_only / internal |
| `bi.get.userGroup_refresh.0142ccb1` | GET /userGroup/refresh | 刷新条件分群 | matched / write |
| `bi.get.userGroup_refreshConditionGroup.11359153` | GET /userGroup/refreshConditionGroup | 删除分群 | backend_only / write |
| `bi.get.userGroup_updGroupNameOrRemark.b3396862` | GET /userGroup/updGroupNameOrRemark | 分群详情 | matched / write |
| `bi.get.userTag_callBackTagExecute.499162fe` | GET /userTag/callBackTagExecute | callBackTagExecute | backend_only / internal |
| `bi.post.userTag_createConditionTag.ab1142fd` | POST /userTag/createConditionTag | 创建条件标签 | matched / write |
| `bi.post.userTag_createFeatureTag.7bd6e449` | POST /userTag/createFeatureTag | 创建条件标签 | matched / write |
| `bi.post.userTag_createIndicatorTag.03364505` | POST /userTag/createIndicatorTag | 创建条件标签 | matched / write |
| `bi.post.userTag_createPresetTag.80ba757b` | POST /userTag/createPresetTag | 获取预置模板列表 | matched / write |
| `bi.post.userTag_createResultTag.ac140bfa` | POST /userTag/createResultTag | 添加结果分群 | matched / write |
| `bi.post.userTag_createUploadTag.a82d740f` | POST /userTag/createUploadTag | 删除标签 | matched / write |
| `bi.get.userTag_delById.8cea6c71` | GET /userTag/delById | 修改用户标签备注 | matched / write |
| `bi.get.userTag_delVerify.14cb93e0` | GET /userTag/delVerify | 获取标签用户的属性列表 | matched / read |
| `bi.get.userTag_detail.92c16574` | GET /userTag/detail | detail | matched / read |
| `bi.get.userTag_entity.37a8d205` | GET /userTag/entity | #region 创建相关 标签主体 | matched / write |
| `bi.get.userTag_findPresetTemplate.8410eec6` | GET /userTag/findPresetTemplate | 获取标签主体 | matched / read |
| `bi.get.userTag_getProfileList.5694be32` | GET /userTag/getProfileList | 标签详情 | backend_only / read |
| `bi.get.userTag_getTagResultDetailList.7242dade` | GET /userTag/getTagResultDetailList | 查询标签值分布 | matched / read |
| `bi.get.userTag_industryTag.3e6b33ee` | GET /userTag/industryTag | 获取行业标签 | matched / read |
| `bi.post.userTag_notify.9735484b` | POST /userTag/notify | Airflow用户标签回调接口 | backend_only / internal |
| `bi.get.userTag_refresh.829eb3e3` | GET /userTag/refresh | 删除校验 | matched / write |
| `bi.get.userTag_tagResult.cb24c665` | GET /userTag/tagResult | 标签值分布 | matched / read |
| `bi.get.userTag_transConditionTag.f88a422c` | GET /userTag/transConditionTag | 回调分群执行 | backend_only / write |
| `bi.post.userTag_updateTag.7af3d826` | POST /userTag/updateTag | 编辑条件标签 | matched / write |
| `bi.get.userTag_updateTagNameById.c67497d6` | GET /userTag/updateTagNameById | 修改名称 | matched / write |
| `bi.get.userTag_updateTagRemarkById.0f3c7c69` | GET /userTag/updateTagRemarkById | 修改用户标签名称 | matched / write |
| `bi.get.userTag_userTagList.285be0d2` | GET /userTag/userTagList | 用户标签列表 | matched / read |

## 使用方式

每个接口的参数、返回声明及源码位置见 `references/api/<接口ID>.md`，或调用 SolarCatalog.describe。先检索再读取单个契约，不应一次读取所有接口。
