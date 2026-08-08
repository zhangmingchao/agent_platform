<template>
  <div class="mcp-list">
    <div class="page-header">
      <h2>MCP 配置</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建 MCP
      </el-button>
    </div>

    <el-table :data="mcps" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column prop="base_url" label="服务器地址" />
      <el-table-column prop="endpoint" label="端点" width="120" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="270" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="openToolsDialog(row)">工具/调试</el-button>
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑 MCP 配置' : '新建 MCP 配置'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="如: 天气服务" />
        </el-form-item>
        <el-form-item label="服务器地址">
          <el-input v-model="form.base_url" placeholder="http://localhost:18888" />
        </el-form-item>
        <el-form-item label="端点">
          <el-input v-model="form.endpoint" placeholder="/mcp" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="toolsDialogVisible"
      :title="`${currentMcp?.name || ''} - MCP 工具`"
      width="900px"
    >
      <el-alert
        v-if="toolsError"
        :title="toolsError"
        type="error"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <el-table :data="tools" v-loading="toolsLoading" max-height="520" stripe empty-text="未发现工具">
        <el-table-column prop="name" label="工具名称" width="210" />
        <el-table-column prop="description" label="描述" min-width="260" show-overflow-tooltip />
        <el-table-column label="参数 Schema" min-width="280">
          <template #default="{ row }">
            <pre class="schema-preview">{{ formatJson(row.inputSchema || {}) }}</pre>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDebugDialog(row)">调试</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button :loading="toolsLoading" @click="loadTools">刷新工具</el-button>
        <el-button @click="toolsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="debugDialogVisible"
      :title="`调试工具：${currentTool?.name || ''}`"
      width="720px"
      append-to-body
    >
      <div v-if="currentTool?.description" class="tool-description">{{ currentTool.description }}</div>
      <el-form label-position="top">
        <el-form-item label="参数 Schema">
          <pre class="debug-schema">{{ formatJson(currentTool?.inputSchema || {}) }}</pre>
        </el-form-item>
        <el-form-item label="调用参数（JSON 对象）">
          <el-input
            v-model="debugArguments"
            type="textarea"
            :rows="10"
            placeholder="{}"
            class="json-input"
          />
        </el-form-item>
        <el-form-item v-if="debugResult" label="调用结果">
          <pre class="debug-result">{{ debugResult }}</pre>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="debugDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="debugRunning" @click="callTool">执行调用</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

// MCP 列表和各类弹窗/请求状态。
const mcps = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const editingId = ref(null)
const toolsDialogVisible = ref(false)
const toolsLoading = ref(false)
const toolsError = ref('')
const tools = ref([])
const currentMcp = ref(null)
const debugDialogVisible = ref(false)
const debugRunning = ref(false)
const currentTool = ref(null)
const debugArguments = ref('{}')
const debugResult = ref('')

// 新建或编辑 MCP 时共用的表单数据。
const form = reactive({
  name: '',
  base_url: 'http://localhost:18888',
  endpoint: '/mcp',
  description: ''
})

// editingId 有值时代表编辑模式，否则代表创建模式。
const isEdit = computed(() => !!editingId.value)

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''
const formatJson = (value) => JSON.stringify(value, null, 2)

const buildArgumentTemplate = (schema = {}) => {
  // 根据 MCP 工具的 JSON Schema 自动生成可编辑的参数示例。
  const args = {}
  const required = new Set(schema.required || [])
  Object.entries(schema.properties || {}).forEach(([name, property]) => {
    if (!required.has(name) && property.default === undefined && property.example === undefined) return
    if (property.default !== undefined) args[name] = property.default
    else if (property.example !== undefined) args[name] = property.example
    else if (property.type === 'boolean') args[name] = false
    else if (property.type === 'number' || property.type === 'integer') args[name] = 0
    else if (property.type === 'array') args[name] = []
    else if (property.type === 'object') args[name] = {}
    else args[name] = ''
  })
  return formatJson(args)
}

const loadMcps = async () => {
  loading.value = true
  try {
    mcps.value = await request.get('/api/mcp-configs', {
      // 添加时间戳参数，避免浏览器或代理返回旧的缓存结果。
      params: { _t: Date.now() }
    })
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  // 打开创建弹窗前先清空上一次遗留的表单内容。
  editingId.value = null
  form.name = ''
  form.base_url = 'http://localhost:18888'
  form.endpoint = '/mcp'
  form.description = ''
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  // 将当前行数据回填到表单，供用户修改。
  editingId.value = row.id
  form.name = row.name
  form.base_url = row.base_url
  form.endpoint = row.endpoint
  form.description = row.description
  dialogVisible.value = true
}

const loadTools = async () => {
  // 调用后端连接 MCP Server，读取该服务对外暴露的工具列表。
  if (!currentMcp.value) return
  toolsLoading.value = true
  toolsError.value = ''
  try {
    const data = await request.get(`/api/mcp-configs/${currentMcp.value.id}/tools`, {
      params: { _t: Date.now() }
    })
    tools.value = data.tools || []
  } catch (e) {
    tools.value = []
    toolsError.value = e.response?.data?.detail || '获取 MCP 工具失败'
  } finally {
    toolsLoading.value = false
  }
}

const openToolsDialog = async (row) => {
  // 先记录当前 MCP，再显示工具弹窗并加载其工具。
  currentMcp.value = row
  tools.value = []
  toolsDialogVisible.value = true
  await loadTools()
}

const openDebugDialog = (tool) => {
  // 为选中的工具生成参数模板，方便直接测试调用。
  currentTool.value = tool
  debugArguments.value = buildArgumentTemplate(tool.inputSchema)
  debugResult.value = ''
  debugDialogVisible.value = true
}

const callTool = async () => {
  // 文本框中的参数需要先解析并确认是 JSON 对象。
  let args
  try {
    args = JSON.parse(debugArguments.value || '{}')
    if (!args || Array.isArray(args) || typeof args !== 'object') {
      throw new Error('参数必须是 JSON 对象')
    }
  } catch (e) {
    ElMessage.warning(`JSON 参数格式错误：${e.message}`)
    return
  }

  debugRunning.value = true
  debugResult.value = ''
  try {
    // 将工具名与用户编辑后的参数发给后端，由后端转发到 MCP Server。
    const data = await request.post(`/api/mcp-configs/${currentMcp.value.id}/call`, {
      name: currentTool.value.name,
      arguments: args
    })
    debugResult.value = typeof data.result === 'string'
      ? data.result
      : formatJson(data.result)
  } catch (e) {
    debugResult.value = e.response?.data?.detail || '工具调用失败'
  } finally {
    debugRunning.value = false
  }
}

const handleSubmit = async () => {
  // 创建和编辑共用一个弹窗，根据 isEdit 决定调用哪个接口。
  if (isEdit.value) {
    await request.put(`/api/mcp-configs/${editingId.value}`, form)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    window.location.reload()
    return
  } else {
    await request.post('/api/mcp-configs', form)
  }
  ElMessage.success('保存成功')
  dialogVisible.value = false
  await loadMcps()
}

const handleDelete = async (row) => {
  // 用户确认后删除，并刷新列表。
  await ElMessageBox.confirm(`确定删除 MCP "${row.name}" 吗？`, '确认删除', { type: 'warning' })
  await request.delete(`/api/mcp-configs/${row.id}`)
  ElMessage.success('删除成功')
  loadMcps()
}

// 页面首次挂载时加载 MCP 配置。
onMounted(loadMcps)
</script>

<style scoped>
.schema-preview {
  margin: 0;
  max-height: 110px;
  overflow: auto;
  white-space: pre-wrap;
  font-size: 12px;
  line-height: 1.4;
  color: #606266;
}
.tool-description {
  margin-bottom: 16px;
  padding: 10px 12px;
  border-radius: 6px;
  background: #f5f7fa;
  color: #606266;
}
.debug-result {
  box-sizing: border-box;
  width: 100%;
  min-height: 120px;
  max-height: 320px;
  margin: 0;
  padding: 12px;
  overflow: auto;
  border-radius: 6px;
  background: #1e1e1e;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.5;
}
.debug-schema {
  box-sizing: border-box;
  width: 100%;
  max-height: 180px;
  margin: 0;
  padding: 10px 12px;
  overflow: auto;
  border-radius: 6px;
  background: #f5f7fa;
  color: #606266;
  white-space: pre-wrap;
  font-size: 12px;
  line-height: 1.4;
}
</style>
