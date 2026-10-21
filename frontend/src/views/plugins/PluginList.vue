<template>
  <div class="plugins-page" v-loading="loading">
    <div class="page-heading">
      <div><h2>插件管理</h2><span class="muted">工作空间 / 集成配置</span></div>
      <el-tooltip content="刷新插件"><el-button :icon="Refresh" circle aria-label="刷新插件" @click="loadPlugins" /></el-tooltip>
    </div>

    <div class="status-band">
      <div><span class="muted">可用插件</span><strong>{{ plugins.length }}</strong></div>
      <div><span class="muted">已添加</span><strong>{{ installedCount }}</strong></div>
      <div><span class="muted">已启用</span><strong class="green">{{ enabledCount }}</strong></div>
      <div><span class="muted">连接异常</span><strong :class="{ red: errorCount }">{{ errorCount }}</strong></div>
    </div>

    <el-alert v-if="loadError" :title="loadError" type="error" show-icon :closable="false" />
    <div class="list-toolbar">
      <el-radio-group v-model="scope" size="default">
        <el-radio-button value="all">全部插件</el-radio-button>
        <el-radio-button value="installed">已添加 {{ installedCount }}</el-radio-button>
      </el-radio-group>
      <div class="list-filters">
        <el-input v-model="search" :prefix-icon="Search" placeholder="搜索插件或工具" clearable aria-label="搜索插件" />
        <el-select v-model="statusFilter" aria-label="启用状态" style="width: 125px">
          <el-option value="all" label="全部状态" /><el-option value="enabled" label="已启用" /><el-option value="disabled" label="未启用" />
        </el-select>
      </div>
    </div>

    <el-table :data="filteredPlugins" class="plugins-table" row-key="manifest.id" :empty-text="loadError ? '插件加载失败' : '没有符合条件的插件'">
      <el-table-column label="插件" min-width="245">
        <template #default="{ row }">
          <div class="plugin-identity"><div class="plugin-icon"><el-icon :size="23"><DataAnalysis /></el-icon></div>
            <div><el-button link type="primary" @click="openPlugin(row)">{{ row.manifest.name }}</el-button>
              <div class="muted identity-meta">{{ row.manifest.id }} <span>v{{ row.manifest.version }}</span></div></div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="来源" width="90"><template #default><el-tag type="info" effect="plain">内置</el-tag></template></el-table-column>
      <el-table-column label="配置" width="110"><template #default="{ row }"><el-tag :type="row.config_status === 'ready' ? 'success' : 'info'" effect="plain">{{ configLabel(row) }}</el-tag></template></el-table-column>
      <el-table-column label="启用" width="85"><template #default="{ row }"><el-switch :model-value="row.enabled" :disabled="busy || !ready(row)" :aria-label="`启用${row.manifest.name}`" @change="value => toggle(row, value)" /></template></el-table-column>
      <el-table-column label="连接状态" width="120"><template #default="{ row }"><span class="health"><i :class="row.health_status" />{{ healthLabel(row) }}</span></template></el-table-column>
      <el-table-column label="最近测试" min-width="165"><template #default="{ row }">{{ formatDate(row.tested_at) }}</template></el-table-column>
      <el-table-column label="Agent" width="80"><template #default="{ row }"><el-button link @click="openPlugin(row, 'agents')">{{ row.agents.length }}</el-button></template></el-table-column>
      <el-table-column label="操作" width="130" fixed="right"><template #default="{ row }">
        <el-tooltip :content="row.manifest.fields.length ? '编辑配置' : '管理插件'"><el-button :icon="Setting" text circle :aria-label="row.manifest.fields.length ? '编辑配置' : '管理插件'" @click="openPlugin(row, 'config')" /></el-tooltip>
        <el-tooltip v-if="row.manifest.capabilities.debug" content="调试工具"><el-button :icon="VideoPlay" text circle aria-label="调试工具" :disabled="!ready(row)" @click="openPlugin(row, 'debug')" /></el-tooltip>
      </template></el-table-column>
    </el-table>
    <div class="list-footer"><span>{{ filteredPlugins.length }} 个插件</span><span>内置目录 · 当前用户独立配置</span></div>

    <el-drawer v-model="drawer" :size="'min(940px, 100vw)'" :before-close="beforeClose" destroy-on-close class="plugin-drawer">
      <template #header>
        <div class="drawer-heading" v-if="selected"><div class="plugin-icon"><el-icon :size="24"><DataAnalysis /></el-icon></div>
          <div><h3>{{ selected.manifest.name }}</h3><span class="muted">{{ selected.manifest.id }} · v{{ selected.manifest.version }}</span></div>
          <el-tag :type="selected.enabled ? 'success' : 'info'">{{ selected.enabled ? '已启用' : '未启用' }}</el-tag>
        </div>
      </template>
      <template v-if="selected">
        <el-tabs v-model="activeTab" @tab-change="loadTab">
          <el-tab-pane label="概览" name="overview">
            <p class="description">{{ selected.manifest.description }}</p>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="插件来源">内置插件</el-descriptions-item>
              <el-descriptions-item label="执行器"><code>{{ selected.manifest.executor }}</code></el-descriptions-item>
              <el-descriptions-item label="配置状态">{{ configLabel(selected) }}</el-descriptions-item>
              <el-descriptions-item label="连接状态"><span class="health"><i :class="selected.health_status" />{{ healthLabel(selected) }}</span></el-descriptions-item>
              <el-descriptions-item label="最近测试">{{ formatDate(selected.tested_at) }}</el-descriptions-item>
              <el-descriptions-item label="权限"><div class="tags"><el-tag v-for="permission in selected.manifest.permissions" :key="permission" type="info" effect="plain">{{ permission }}</el-tag></div></el-descriptions-item>
            </el-descriptions>
            <template v-if="selected.manifest.capabilities.connection_test">
              <div class="section-heading"><h4>连接检测</h4><span class="muted">{{ selected.health_message }}</span></div>
              <PluginFields :fields="selected.manifest.test_fields" :model="probeForm" :disabled="busy" />
              <el-button :icon="Connection" :loading="testing" :disabled="busy || dirty || !ready(selected)" @click="testConnection">测试连接</el-button>
            </template>
            <el-alert v-if="probeResult" :title="probeResult.message" :type="probeResult.ok ? 'success' : 'error'" :description="`耗时 ${probeResult.duration_ms} ms`" show-icon :closable="false" class="result-alert" />
          </el-tab-pane>

          <el-tab-pane :label="selected.manifest.fields.length ? '配置' : '管理'" name="config">
            <template v-if="selected.manifest.fields.length">
              <div class="section-heading"><h4>{{ selected.manifest.config_title }}</h4><el-tag type="info" effect="plain">版本 {{ selected.revision || '草稿' }}</el-tag></div>
              <PluginFields :fields="selected.manifest.fields" :model="form" :configured-secrets="selected.configured_secrets" :disabled="busy" />
            </template>
            <el-alert v-if="configError" :title="configError" type="error" :closable="false" show-icon />
            <div class="config-actions" v-if="selected.manifest.fields.length || selected.manifest.capabilities.environment_import"><el-button v-if="selected.manifest.fields.length" type="primary" :icon="Check" :loading="saving" :disabled="busy && !saving" @click="saveConfig">保存配置</el-button>
              <el-button v-if="selected.manifest.capabilities.environment_import" :icon="Download" :disabled="busy" @click="importEnvironment">导入环境配置</el-button></div>
            <div class="section-heading lifecycle"><h4>插件状态</h4><el-switch :model-value="selected.enabled" :disabled="busy || dirty || !ready(selected)" active-text="启用" inactive-text="停用" @change="value => toggle(selected, value)" /></div>
            <div class="remove-row"><span class="muted">关联 Agent：{{ selected.agents.length }}</span>
              <el-button type="danger" plain :icon="Delete" :disabled="busy || !selected.installed || selected.agents.length > 0" @click="removeConfig">移除插件</el-button></div>
          </el-tab-pane>

          <el-tab-pane label="工具与 Skill" name="tools">
            <div class="section-heading"><h4>工具</h4><el-tag effect="plain">{{ selected.manifest.tools.length }}</el-tag></div>
            <el-alert v-if="tabError" :title="tabError" type="error" :closable="false" />
            <div v-for="tool in tools" :key="tool.name" class="tool-definition"><strong><code>{{ tool.name }}</code></strong><p class="muted">{{ tool.description }}</p><pre>{{ pretty(tool.parameters) }}</pre></div>
            <template v-if="selected.manifest.skill_name"><div class="section-heading"><h4>Skill · {{ selected.manifest.skill_name }}</h4>
              <el-select v-model="skillPath" aria-label="技能文件" style="width: 235px" @change="loadSkill"><el-option v-for="path in selected.manifest.skill_files" :key="path" :value="path" :label="path" /></el-select></div>
            <pre class="skill-content" v-loading="skillLoading">{{ skillContent }}</pre></template>
          </el-tab-pane>

          <el-tab-pane v-if="selected.manifest.capabilities.debug" label="工具调试" name="debug">
            <el-alert v-if="tabError" :title="tabError" type="error" :closable="false" show-icon />
            <div class="section-heading"><el-select v-model="toolName" aria-label="调试工具名称" style="width: 220px" @change="resetToolInput"><el-option v-for="tool in tools" :key="tool.name" :label="tool.name" :value="tool.name" /></el-select>
              <el-radio-group v-if="selected.manifest.debug_panel === 'bi-metadata'" v-model="debugMode" size="small"><el-radio-button value="form">参数</el-radio-button><el-radio-button value="json">JSON</el-radio-button></el-radio-group></div>
            <BiPluginDebug v-if="selected.manifest.debug_panel === 'bi-metadata'" v-show="debugMode === 'form'" :key="selected.manifest.id" v-model="toolInput" />
            <el-input v-if="debugMode === 'json'" v-model="rawArguments" type="textarea" :rows="9" aria-label="工具输入 JSON 对象" />
            <div class="debug-actions"><el-button type="primary" :icon="VideoPlay" :loading="debugging" :disabled="busy || dirty || !ready(selected) || !toolName" @click="debugTool">执行工具</el-button><span class="muted" v-if="debugResult">{{ debugResult.duration_ms }} ms</span></div>
            <el-alert v-if="debugError" :title="debugError" type="error" :closable="false" show-icon />
            <template v-if="debugResult"><div class="section-heading"><h4>查询结果</h4><el-tag :type="debugResult.ok ? 'success' : 'danger'">{{ debugResult.ok ? '成功' : '失败' }}</el-tag><el-tooltip content="复制结果"><el-button :icon="CopyDocument" circle text aria-label="复制结果" @click="copyResult" /></el-tooltip></div><pre class="debug-output">{{ prettyResult }}</pre></template>
          </el-tab-pane>

          <el-tab-pane label="关联 Agent" name="agents">
            <el-empty v-if="!selected.agents.length" description="暂无关联 Agent"><el-button :icon="Plus" type="primary" @click="goTo('/agents/new')">创建 Agent</el-button></el-empty>
            <el-table v-else :data="selected.agents"><el-table-column prop="name" label="Agent" /><el-table-column prop="id" label="ID" width="90" /><el-table-column label="操作" width="95"><template #default="{ row }"><el-tooltip content="编辑 Agent"><el-button :icon="Edit" circle text aria-label="编辑 Agent" @click="goTo(`/agents/${row.id}/edit`)" /></el-tooltip></template></el-table-column></el-table>
          </el-tab-pane>

          <el-tab-pane label="操作记录" name="activity">
            <div class="section-heading"><h4>最近记录</h4><el-tooltip content="刷新记录"><el-button :icon="Refresh" text circle aria-label="刷新记录" @click="loadActivity(false)" /></el-tooltip></div>
            <el-alert v-if="tabError" :title="tabError" type="error" :closable="false" />
            <el-table :data="activities" empty-text="暂无操作记录" v-loading="activityLoading">
              <el-table-column label="时间" min-width="165"><template #default="{ row }">{{ formatDate(row.created_at) }}</template></el-table-column>
              <el-table-column label="操作" width="105"><template #default="{ row }">{{ actionLabels[row.action] || row.action }}</template></el-table-column>
              <el-table-column label="结果" width="80"><template #default="{ row }"><el-tag :type="row.status === 'success' ? 'success' : 'danger'" effect="plain">{{ row.status === 'success' ? '成功' : '失败' }}</el-tag></template></el-table-column>
              <el-table-column prop="message" label="摘要" min-width="180" show-overflow-tooltip />
              <el-table-column label="耗时" width="95"><template #default="{ row }">{{ row.duration_ms }} ms</template></el-table-column>
              <el-table-column label="Trace" width="85"><template #default="{ row }"><el-button v-if="row.trace_run_id" link type="primary" @click="goTo(`/traces?trace_id=${row.trace_run_id}`)">#{{ row.trace_run_id }}</el-button><span v-else>—</span></template></el-table-column>
            </el-table>
            <el-button v-if="hasMoreActivity" class="load-more" :loading="activityLoading" @click="loadActivity(true)">加载更早记录</el-button>
          </el-tab-pane>
        </el-tabs>
      </template>
      <template #footer><div class="drawer-footer"><span class="muted" v-if="selected">{{ dirty ? '有未保存的修改' : `更新于 ${formatDate(selected.updated_at)}` }}</span><el-button :disabled="busy" @click="closeDrawer">关闭</el-button></div></template>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Connection, CopyDocument, DataAnalysis, Delete, Download, Edit, Plus, Refresh, Search, Setting, VideoPlay } from '@element-plus/icons-vue'
import request from '../../utils/request'
import PluginFields from './PluginFields.vue'
import BiPluginDebug from './BiPluginDebug.vue'

const router = useRouter()
const plugins = ref([])
const loading = ref(false)
const loadError = ref('')
const search = ref('')
const scope = ref('all')
const statusFilter = ref('all')
const selected = ref(null)
const drawer = ref(false)
const activeTab = ref('overview')
const saving = ref(false)
const testing = ref(false)
const debugging = ref(false)
const mutating = ref(false)
const busy = computed(() => saving.value || testing.value || debugging.value || mutating.value)
const form = reactive({ values: {}, secrets: {}, clear_secrets: [], revision: 0 })
const probeForm = reactive({ values: {}, secrets: {}, clear_secrets: [] })
const baseline = ref('')
const dirty = computed(() => JSON.stringify(form) !== baseline.value)
const configError = ref('')
const tabError = ref('')
const tools = ref([])
const skillPath = ref('SKILL.md')
const skillContent = ref('')
const skillLoading = ref(false)
const activities = ref([])
const activityLoading = ref(false)
const hasMoreActivity = ref(false)
const toolName = ref('')
const toolInput = ref({})
const debugMode = ref('form')
const rawArguments = ref('{}')
const debugResult = ref(null)
const debugError = ref('')
const probeResult = ref(null)
const actionLabels = { configure: '保存配置', import_environment: '导入配置', enable: '启用', disable: '停用', remove: '移除配置', test: '连接测试', debug: '调试查询', call: 'Agent 调用', bind: '绑定 Agent', unbind: '解除绑定' }
const installedCount = computed(() => plugins.value.filter(p => p.installed).length)
const enabledCount = computed(() => plugins.value.filter(p => p.enabled).length)
const errorCount = computed(() => plugins.value.filter(p => p.health_status === 'error').length)
const filteredPlugins = computed(() => plugins.value.filter(p =>
  (scope.value !== 'installed' || p.installed) && (statusFilter.value === 'all' || p.enabled === (statusFilter.value === 'enabled')) &&
  `${p.manifest.name} ${p.manifest.id} ${p.manifest.tools.join(' ')}`.toLowerCase().includes(search.value.trim().toLowerCase())))
const pretty = value => JSON.stringify(value, null, 2)
const prettyResult = computed(() => {
  try { return pretty(JSON.parse(debugResult.value?.result || '{}')) } catch { return debugResult.value?.result || '' }
})
const formatDate = value => value ? new Date(value.endsWith('Z') ? value : `${value}Z`).toLocaleString('zh-CN', { hour12: false }) : '—'
const ready = plugin => ['ready', 'not_required'].includes(plugin.config_status)
const configLabel = p => ({ ready: '已配置', not_required: '无需配置', incomplete: '待完善', unconfigured: '未配置' }[p.config_status] || p.config_status)
const healthLabel = p => p.manifest.capabilities.connection_test ? ({ healthy: '连接正常', error: '连接异常', untested: '未测试' }[p.health_status] || p.health_status) : '不适用'
const errorMessage = error => typeof error.response?.data?.detail === 'string' ? error.response.data.detail : (error.message || '请求失败')

// 替换公开状态时清空输入中的密钥，空值始终表示保留服务器中已有凭据。
const applyPlugin = plugin => {
  selected.value = plugin
  const index = plugins.value.findIndex(p => p.manifest.id === plugin.manifest.id)
  if (index >= 0) plugins.value[index] = plugin
  Object.assign(form, { values: { ...plugin.config_values }, secrets: Object.fromEntries(plugin.manifest.fields.filter(f => f.kind === 'secret').map(f => [f.key, ''])), clear_secrets: [], revision: plugin.revision })
  baseline.value = JSON.stringify(form)
}
const loadPlugins = async () => {
  loading.value = true
  loadError.value = ''
  try { plugins.value = await request.get('/api/plugins') } catch (error) { loadError.value = errorMessage(error) } finally { loading.value = false }
}
const openPlugin = async (plugin, tab = 'overview') => {
  applyPlugin(plugin)
  activeTab.value = tab
  configError.value = ''; tabError.value = ''; debugError.value = ''
  probeResult.value = null; debugResult.value = null; tools.value = []; activities.value = []
  skillPath.value = 'SKILL.md'; skillContent.value = ''
  toolName.value = ''; toolInput.value = {}; rawArguments.value = '{}'
  debugMode.value = plugin.manifest.debug_panel === 'bi-metadata' ? 'form' : 'json'
  probeForm.values = Object.fromEntries(plugin.manifest.test_fields.map(field => [field.key, field.default ?? (field.kind === 'boolean' ? false : '')]))
  drawer.value = true
  await loadTab(tab)
}
const confirm = async (message, title = '确认操作') => {
  try { await ElMessageBox.confirm(message, title, { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }); return true } catch { return false }
}
const beforeClose = async done => {
  if (busy.value) return
  if (dirty.value && !await confirm('配置尚未保存，确认放弃修改？', '未保存的配置')) return
  form.secrets = {}; done()
}
const closeDrawer = () => beforeClose(() => { drawer.value = false })
const goTo = async path => beforeClose(() => { drawer.value = false; router.push(path) })
const saveConfig = async () => {
  configError.value = ''
  saving.value = true
  try {
    applyPlugin(await request.put(`/api/plugins/${selected.value.manifest.id}/config`, { ...form }))
    probeResult.value = null; debugResult.value = null
    ElMessage.success('配置已保存')
  } catch (error) { configError.value = errorMessage(error) } finally { saving.value = false }
}
const toggle = async (plugin, enabled) => {
  if (!enabled && plugin.agents.length && !await confirm(`停用后，${plugin.agents.map(a => a.name).join('、')} 的后续请求将不再加载此插件。确认停用？`, '停用插件')) return
  mutating.value = true
  try {
    const result = await request.put(`/api/plugins/${plugin.manifest.id}/enabled`, { enabled, revision: plugin.revision })
    if (selected.value?.manifest.id === plugin.manifest.id && drawer.value) applyPlugin(result)
    else plugins.value = plugins.value.map(p => p.manifest.id === result.manifest.id ? result : p)
    ElMessage.success(enabled ? '插件已启用' : '插件已停用')
  } catch { /* 统一请求层展示错误。 */ } finally { mutating.value = false }
}
const importEnvironment = async () => {
  if (!await confirm(`将服务器中「${selected.value.manifest.name}」的环境配置复制到你的插件配置，覆盖已保存字段。确认导入？`, '导入环境配置')) return
  mutating.value = true
  try { applyPlugin(await request.post(`/api/plugins/${selected.value.manifest.id}/import-environment`, null, { params: { revision: selected.value.revision } })); probeResult.value = null; ElMessage.success('环境配置已导入') }
  catch (error) { configError.value = errorMessage(error) } finally { mutating.value = false }
}
const removeConfig = async () => {
  if (!await confirm('将移除此插件的用户配置、凭据和启用状态，操作记录保留。确认移除？', '移除插件')) return
  mutating.value = true
  try {
    const id = selected.value.manifest.id
    await request.delete(`/api/plugins/${id}`, { params: { revision: selected.value.revision } })
    applyPlugin(await request.get(`/api/plugins/${id}`)); probeResult.value = null; debugResult.value = null
    ElMessage.success('配置已移除')
  } catch (error) { configError.value = errorMessage(error) } finally { mutating.value = false }
}
const testConnection = async () => {
  testing.value = true
  try {
    probeResult.value = await request.post(`/api/plugins/${selected.value.manifest.id}/test`, { parameters: { ...probeForm.values } }, { timeout: 75000 })
    // 仅更新公开状态，不覆盖用户正在编辑的本地配置。
    applyPlugin(await request.get(`/api/plugins/${selected.value.manifest.id}`))
  } catch (error) { probeResult.value = { ok: false, message: errorMessage(error), duration_ms: 0 } } finally { testing.value = false }
}
const debugTool = async () => {
  debugError.value = ''; debugResult.value = null
  let input = toolInput.value
  try {
    if (debugMode.value === 'json') input = JSON.parse(rawArguments.value)
    if (!input || Array.isArray(input) || typeof input !== 'object') throw new Error('工具输入必须是 JSON 对象')
  } catch (error) { debugError.value = error.message; return }
  debugging.value = true
  try { debugResult.value = await request.post(`/api/plugins/${selected.value.manifest.id}/debug`, { tool_name: toolName.value, input }, { timeout: 75000 }) }
  catch (error) { debugError.value = errorMessage(error) } finally { debugging.value = false }
}
const loadSkill = async () => {
  skillLoading.value = true
  try { skillContent.value = (await request.get(`/api/plugins/${selected.value.manifest.id}/skill`, { params: { path: skillPath.value } })).content }
  catch (error) { skillContent.value = ''; tabError.value = errorMessage(error) } finally { skillLoading.value = false }
}
const loadActivity = async (more = false) => {
  if (activityLoading.value) return
  activityLoading.value = true
  try {
    const rows = await request.get(`/api/plugins/${selected.value.manifest.id}/activity`, { params: more ? { before_id: activities.value.at(-1)?.id } : {} })
    activities.value = more ? [...activities.value, ...rows] : rows
    hasMoreActivity.value = rows.length === 30
  } catch (error) { tabError.value = errorMessage(error) } finally { activityLoading.value = false }
}
const loadTab = async tab => {
  tabError.value = ''
  if (tab === 'tools' || tab === 'debug') {
    try {
      tools.value = await request.get(`/api/plugins/${selected.value.manifest.id}/tools`)
      if (!toolName.value) { toolName.value = tools.value[0]?.name || ''; resetToolInput() }
      if (tab === 'tools' && selected.value.manifest.skill_name) await loadSkill()
    } catch (error) { tabError.value = errorMessage(error) }
  }
  if (tab === 'activity') await loadActivity()
}
const copyResult = async () => {
  try { await navigator.clipboard.writeText(prettyResult.value); ElMessage.success('结果已复制') } catch { ElMessage.warning('复制失败') }
}
const resetToolInput = () => {
  const tool = tools.value.find(item => item.name === toolName.value)
  if (selected.value.manifest.debug_panel === 'bi-metadata') return
  // 通用面板从工具定义读取示例与默认值，不依赖特定插件的参数名。
  const input = tool?.example_input || Object.fromEntries(Object.entries(tool?.parameters.properties || {}).map(([key, field]) => [key, field.default ?? (field.type === 'boolean' ? false : field.type === 'integer' ? 0 : field.type === 'array' ? [] : '')]))
  toolInput.value = input
  rawArguments.value = pretty(input)
}
watch(debugMode, mode => { if (mode === 'json' && selected.value?.manifest.debug_panel === 'bi-metadata') rawArguments.value = pretty(toolInput.value) })
onMounted(loadPlugins)
</script>

<style scoped>
.plugins-page { min-width: 0; color: #303133; }
.page-heading, .list-toolbar, .list-filters, .section-heading, .probe-row, .config-actions, .remove-row, .debug-actions, .drawer-footer { display: flex; align-items: center; gap: 12px; }
.page-heading, .list-toolbar, .remove-row, .drawer-footer { justify-content: space-between; }
.page-heading { margin-bottom: 24px; }
h2 { margin: 0 0 7px; font-size: 22px; font-weight: 600; }
h3 { margin: 0 0 6px; font-size: 18px; }
h4 { margin: 0; font-size: 15px; font-weight: 600; }
.muted { color: #858b95; font-size: 13px; }
.status-band { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); padding: 22px 0; border-top: 1px solid #e4e7ed; border-bottom: 1px solid #e4e7ed; margin-bottom: 24px; }
.status-band > div { display: flex; flex-direction: column; gap: 10px; padding-left: 24px; border-right: 1px solid #e4e7ed; }
.status-band > div:first-child { padding-left: 0; }
.status-band > div:last-child { border: 0; }
.status-band strong { font-size: 25px; font-weight: 600; }
.green { color: #27966b; }.red { color: #d85151; }
.list-toolbar { margin: 22px 0 16px; flex-wrap: wrap; }
.list-filters { flex-wrap: wrap; }.list-filters .el-input { width: 235px; max-width: 100%; }
.plugins-table { border-top: 1px solid #e4e7ed; }
.plugins-table :deep(th.el-table__cell) { background: #f0f2f5; color: #69717d; font-weight: 500; }
.plugins-table :deep(td.el-table__cell) { padding: 21px 0; }
.plugin-identity, .drawer-heading { display: flex; align-items: center; gap: 13px; min-width: 0; }
.plugin-icon { display: grid; place-items: center; width: 44px; height: 44px; flex: 0 0 44px; background: #e7f4ee; color: #268564; border-radius: 8px; }
.identity-meta { margin-top: 6px; font-size: 12px; }.identity-meta span { margin-left: 10px; }
.health { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; }.health i { width: 7px; height: 7px; border-radius: 50%; background: #b5bac3; }.health .healthy { background: #27966b; }.health .error { background: #d85151; }
.list-footer { display: flex; justify-content: space-between; gap: 12px; color: #858b95; font-size: 12px; margin-top: 16px; }
.drawer-heading { flex-wrap: wrap; }.drawer-heading > div:nth-child(2) { flex: 1; min-width: 180px; }
.description { margin: 20px 0 24px; line-height: 1.8; color: #606773; }
.section-heading { margin: 24px 0 16px; flex-wrap: wrap; }.section-heading h4 { flex: 1; }.section-heading .muted { overflow-wrap: anywhere; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }.probe-row { align-items: flex-start; }.probe-row .el-input { max-width: 400px; }.result-alert { margin-top: 16px; }
.config-form { max-width: 600px; }.config-form .el-input-number { width: 220px; max-width: 100%; }.config-form .el-checkbox { margin-top: 4px; }
.config-actions { margin-top: 24px; flex-wrap: wrap; }.lifecycle { border-top: 1px solid #ebeef3; padding-top: 24px; margin-top: 32px; }.remove-row { padding: 18px 0; }
.debug-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 20px; }.debug-form .el-input-number, .debug-form .el-select { width: 100%; }
pre { margin: 12px 0; padding: 16px; background: #f5f6f8; border: 1px solid #e6e9ef; border-radius: 6px; font: 12px/1.7 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; white-space: pre-wrap; overflow-wrap: anywhere; max-height: 480px; overflow: auto; }
.argument-preview { color: #68717e; max-height: 190px; }.debug-actions { margin: 18px 0; }.debug-output { background: #fafbfc; }.tool-definition { padding-bottom: 15px; border-bottom: 1px solid #ebeef3; }.skill-content { max-height: 500px; }.load-more { margin-top: 16px; }.drawer-footer { width: 100%; text-align: left; }.drawer-footer .muted { overflow-wrap: anywhere; }
@media (max-width: 760px) {
  .status-band { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 22px 0; }.status-band > div:nth-child(3) { padding-left: 0; }.status-band > div:nth-child(2) { border-right: 0; }
  .list-filters { width: 100%; }.list-filters .el-input { flex: 1; min-width: 130px; }.list-footer { flex-wrap: wrap; }.debug-form { grid-template-columns: minmax(0, 1fr); }.probe-row { flex-wrap: wrap; }.drawer-heading > div:nth-child(2) { min-width: 140px; }
}
</style>
