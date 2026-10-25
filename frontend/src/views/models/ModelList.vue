<template>
  <div class="model-page">
    <div class="page-header">
      <h2>模型管理</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        添加模型
      </el-button>
    </div>

    <el-table :data="models" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" width="160" />
      <el-table-column prop="provider" label="提供商" width="100" />
      <el-table-column prop="model_id" label="模型ID" width="180" show-overflow-tooltip />
      <el-table-column prop="base_url" label="API地址" min-width="200" show-overflow-tooltip />
      <el-table-column label="温度" width="80">
        <template #default="{ row }">{{ row.temperature }}</template>
      </el-table-column>
      <el-table-column label="Token限额" min-width="210">
        <template #default="{ row }">
          <template v-if="row.quota_mode === 'daily'">
            <div>每日 {{ formatTokens(row.daily_token_limit) }}</div>
            <div class="quota-usage">
              已用 {{ formatTokens(row.today_usage?.used_tokens || 0) }}，
              剩余 {{ formatTokens(row.today_usage?.remaining_tokens || 0) }}
            </div>
          </template>
          <el-tag v-else type="info" size="small">不限额</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button type="success" link :loading="testingId === row.id" @click="handleTest(row)">测试</el-button>
          <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑模型' : '添加模型'" width="min(760px, calc(100vw - 32px))" top="5vh">
      <template v-if="!isEdit">
        <el-radio-group v-model="addMode" class="catalog-mode" @change="changeAddMode">
          <el-radio-button value="bailian">阿里云百炼目录</el-radio-button>
          <el-radio-button value="custom">自定义添加</el-radio-button>
        </el-radio-group>
        <div v-if="addMode === 'bailian'" class="catalog-panel">
          <div class="catalog-toolbar">
            <el-input v-model="catalogSearch" placeholder="搜索模型名称或 ID" clearable maxlength="100" />
            <el-button :loading="catalogLoading" @click="loadCatalog(true)">刷新目录</el-button>
          </div>
          <el-alert v-if="catalogError" :title="catalogError" type="error" :closable="false" show-icon />
          <el-button v-if="catalogError" link type="primary" @click="loadCatalog(true)">重试加载</el-button>
          <el-table :data="catalogItems" v-loading="catalogLoading" height="230" @row-click="selectCatalogModel" highlight-current-row>
            <el-table-column label="模型" min-width="210">
              <template #default="{ row }">
                <div>{{ row.name }}</div><div class="quota-usage">{{ row.model_id }}</div>
              </template>
            </el-table-column>
            <el-table-column label="上下文" width="110">
              <template #default="{ row }">{{ row.context_window ? formatTokens(row.context_window) : '—' }}</template>
            </el-table-column>
            <el-table-column label="选择" width="80">
              <template #default="{ row }">
                <el-button link type="primary" @click.stop="selectCatalogModel(row)">{{ selectedCatalogId === row.model_id ? '已选择' : '选择' }}</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination v-model:current-page="catalogPage" :page-size="10" :total="catalogTotal" layout="total, prev, pager, next" @current-change="loadCatalog()" />
          <p class="quota-usage">目录按文字聊天能力筛选，具体权限及接口支持请使用「测试连接」验证。</p>
          <p v-if="selectedCatalog" class="catalog-description">{{ selectedCatalog.description }}</p>
        </div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：DeepSeek Chat" />
        </el-form-item>
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="通义千问" value="qwen" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型ID" prop="model_id">
          <el-input v-model="form.model_id" :readonly="!isEdit && addMode === 'bailian'" placeholder="选择目录模型或自定义填写 ID" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password :placeholder="isEdit ? '留空保留原 API Key' : '填写用于推理的 API Key'" />
        </el-form-item>
        <el-form-item label="API地址" prop="base_url">
          <el-input v-model="form.base_url" placeholder="如 https://…/compatible-mode/v1，不含 /chat/completions" />
        </el-form-item>
        <el-form-item label="温度" prop="temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" style="padding: 10px" />
        </el-form-item>
        <el-form-item label="最大Tokens" prop="max_tokens">
          <el-input-number v-model="form.max_tokens" :min="1" :max="128000" controls-position="right" />
        </el-form-item>
        <el-form-item label="Token限额" prop="quota_mode">
          <el-radio-group v-model="form.quota_mode">
            <el-radio-button value="unlimited">不限额</el-radio-button>
            <el-radio-button value="daily">每日限额</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.quota_mode === 'daily'" label="每日额度" prop="daily_token_limit">
          <el-input-number
            v-model="form.daily_token_limit"
            :min="1"
            :max="10000000000"
            :step="1000"
            controls-position="right"
          />
          <span class="field-hint">每天 00:00（Asia/Shanghai）进入新的统计周期</span>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <!-- 测试结果 -->
      <el-alert
        v-if="testResult"
        :title="testResult.success ? '连接成功' : '连接失败'"
        :type="testResult.success ? 'success' : 'error'"
        :description="testResult.detail + (testResult.response ? ' — 模型回复: ' + testResult.response : '')"
        :closable="true"
        show-icon
        style="margin-bottom: 16px"
        @close="testResult = null"
      />

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="success" :loading="testingInDialog" @click="handleTestInDialog">
          测试连接
        </el-button>
        <el-button type="primary" @click="handleSubmit" :loading="saving">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const models = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const editId = ref(null)
const isEdit = computed(() => !!editId.value)
const testingId = ref(null)
const testingInDialog = ref(false)
const testResult = ref(null)

// 目录仅包含公开模型信息；目录查询凭据由后端管理。
const addMode = ref('bailian')
const catalogItems = ref([])
const catalogTotal = ref(0)
const catalogPage = ref(1)
const catalogSearch = ref('')
const catalogLoading = ref(false)
const catalogError = ref('')
const selectedCatalogId = ref('')
const selectedCatalog = ref(null)
let catalogRequestId = 0
let searchTimer

// refresh 表示主动刷新缓存；请求序号避免旧搜索结果覆盖新页面。
const loadCatalog = async (refresh = false) => {
  const requestId = ++catalogRequestId
  catalogLoading.value = true
  catalogError.value = ''
  try {
    const result = await request.get('/api/models/catalog', {
      params: { page_no: catalogPage.value, page_size: 10, search: catalogSearch.value, refresh }
    })
    if (requestId !== catalogRequestId) return
    catalogItems.value = result.items
    catalogTotal.value = result.total
  } catch (error) {
    if (requestId !== catalogRequestId) return
    catalogItems.value = []
    catalogTotal.value = 0
    catalogError.value = error.response?.data?.detail || '目录加载失败，请重试或使用自定义添加'
  } finally {
    if (requestId === catalogRequestId) catalogLoading.value = false
  }
}

// model 为公开目录实体，选择后带出兼容调用地址和模型标识。
const selectCatalogModel = (model) => {
  selectedCatalogId.value = model.model_id
  selectedCatalog.value = model
  form.name = model.name
  form.model_id = model.model_id
  form.provider = model.provider
  form.base_url = model.base_url
  form.max_tokens = Math.min(4096, model.max_output_tokens || 4096)
  testResult.value = null
  formRef.value?.clearValidate()
}

// mode 为添加方式；切换后清空模型标识，避免把目录 ID 和手动地址混用。
const changeAddMode = (mode) => {
  selectedCatalogId.value = ''
  selectedCatalog.value = null
  form.name = ''
  form.model_id = ''
  form.provider = mode === 'bailian' ? 'qwen' : 'openai'
  form.base_url = ''
  testResult.value = null
  formRef.value?.clearValidate()
  if (mode === 'bailian') loadCatalog()
}

watch(catalogSearch, () => {
  clearTimeout(searchTimer)
  ++catalogRequestId
  searchTimer = setTimeout(() => {
    catalogPage.value = 1
    if (dialogVisible.value && addMode.value === 'bailian') loadCatalog()
  }, 300)
})

const form = reactive({
  name: '',
  provider: 'openai',
  model_id: '',
  api_key: '',
  base_url: '',
  temperature: 0.7,
  max_tokens: 4096,
  quota_mode: 'unlimited',
  daily_token_limit: null,
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  model_id: [{ required: true, message: '请输入模型ID', trigger: 'blur' }],
  api_key: [{
    validator: (_rule, value, callback) => callback(!isEdit.value && !value?.trim() ? new Error('请输入 API Key') : undefined),
    trigger: 'blur'
  }],
  daily_token_limit: [{
    validator: (_rule, value, callback) => {
      if (form.quota_mode === 'daily' && (!value || Number(value) <= 0)) {
        callback(new Error('请输入大于 0 的每日 Token 限额'))
        return
      }
      callback()
    },
    trigger: 'change'
  }]
}

const formatTokens = (value) => Number(value || 0).toLocaleString('zh-CN')

const loadModels = async () => {
  loading.value = true
  try {
    models.value = await request.get('/api/modelsList')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.name = ''
  form.provider = 'openai'
  form.model_id = ''
  form.api_key = ''
  form.base_url = ''
  form.temperature = 0.7
  form.max_tokens = 4096
  form.quota_mode = 'unlimited'
  form.daily_token_limit = null
  form.is_active = true
  editId.value = null
  testResult.value = null
  formRef.value?.clearValidate()
}

const openCreate = () => {
  resetForm()
  addMode.value = 'bailian'
  catalogPage.value = 1
  catalogSearch.value = ''
  selectedCatalogId.value = ''
  selectedCatalog.value = null
  form.provider = 'qwen'
  dialogVisible.value = true
  loadCatalog()
}

const openEdit = (row) => {
  resetForm()
  form.name = row.name
  form.provider = row.provider
  form.model_id = row.model_id
  form.api_key = ''
  form.base_url = row.base_url
  form.temperature = row.temperature
  form.max_tokens = row.max_tokens
  form.quota_mode = row.quota_mode || 'unlimited'
  form.daily_token_limit = row.daily_token_limit
  form.is_active = !!row.is_active
  editId.value = row.id
  dialogVisible.value = true
}

const handleSubmit = async () => {
  // 字段校验失败时停留在弹窗，避免未处理的 Promise 异常。
  if (!await formRef.value.validate().catch(() => false)) return
  if (form.quota_mode === 'unlimited') {
    form.daily_token_limit = null
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await request.put(`/api/models/${editId.value}`, form)
      ElMessage.success('保存成功')
    } else {
      await request.post('/api/models', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadModels()
  } finally {
    saving.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除模型「${row.name}」吗？`, '提示', { type: 'warning' })
  await request.delete(`/api/models/${row.id}`)
  ElMessage.success('删除成功')
  await loadModels()
}

const handleTest = async (row) => {
  testingId.value = row.id
  try {
    const result = await request.post(`/api/models/${row.id}/test`)
    if (result.success) {
      ElMessage.success(`「${row.name}」连接成功 — 模型回复: ${result.response || '(空)'}`)
    } else {
      ElMessage.error(`「${row.name}」连接失败: ${result.detail}`)
    }
  } catch (e) {
    ElMessage.error(e.message || '测试请求失败')
  } finally {
    testingId.value = null
  }
}

const handleTestInDialog = async () => {
  if (!form.model_id || !form.api_key) {
    ElMessage.warning('请先填写模型 ID 和 API Key')
    return
  }
  testingInDialog.value = true
  testResult.value = null
  try {
    testResult.value = await request.post('/api/models/test', form)
  } catch (e) {
    testResult.value = { success: false, detail: e.message || '测试请求失败' }
  } finally {
    testingInDialog.value = false
  }
}

onMounted(loadModels)
onUnmounted(() => {
  clearTimeout(searchTimer)
  ++catalogRequestId
})
</script>

<style scoped>
.catalog-mode { margin-bottom: 16px; }
:deep(.el-dialog__body) { max-height: calc(85vh - 140px); overflow-y: auto; }
.catalog-panel { margin-bottom: 20px; }
.catalog-toolbar { display: flex; gap: 12px; margin-bottom: 12px; }
.catalog-description { font-size: 12px; line-height: 1.6; max-height: 70px; overflow: auto; }
.catalog-panel :deep(.el-pagination) { margin-top: 12px; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.quota-usage,
.field-hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.field-hint {
  margin-left: 12px;
}
</style>
