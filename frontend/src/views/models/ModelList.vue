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
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑模型' : '添加模型'" width="600">
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
          <el-input v-model="form.model_id" placeholder="如：deepseek-chat" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="API地址" prop="base_url">
          <el-input v-model="form.base_url" placeholder="https://api.deepseek.com" />
        </el-form-item>
        <el-form-item label="温度" prop="temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" style="padding: 10px" />
        </el-form-item>
        <el-form-item label="最大Tokens" prop="max_tokens">
          <el-input v-model="form.max_tokens" type="number" :min="1" :max="128000" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="saving">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const models = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()
const editId = ref(null)
const isEdit = computed(() => !!editId.value)

const form = reactive({
  name: '',
  provider: 'openai',
  model_id: '',
  api_key: '',
  base_url: '',
  temperature: 0.7,
  max_tokens: 4096,
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  model_id: [{ required: true, message: '请输入模型ID', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入API Key', trigger: 'blur' }]
}

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
  form.is_active = true
  editId.value = null
}

const openCreate = () => {
  resetForm()
  dialogVisible.value = true
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
  form.is_active = !!row.is_active
  editId.value = row.id
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate()
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

onMounted(loadModels)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
