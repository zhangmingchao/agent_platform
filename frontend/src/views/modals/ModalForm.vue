<template>
  <div>
    <div class="page-header">
      <h2>{{ isEdit ? '编辑模型' : '创建模型' }}</h2>
      <el-button @click="router.push('/modals')">返回</el-button>
    </div>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" class="config-form" v-loading="loading">
      <el-card shadow="never">
        <template #header>基本信息</template>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：DeepSeek 对话模型" />
        </el-form-item>
        <el-form-item label="模型标识" prop="model_key">
          <el-input v-model="form.model_key" placeholder="例如：deepseek-chat（Agent 通过此标识引用模型）" />
        </el-form-item>
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" style="width: 100%">
            <el-option label="OpenAI 兼容" value="openai_compatible" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="DeepSeek" value="deepseek" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="例如：deepseek-chat（API 实际调用的模型名）" />
        </el-form-item>
      </el-card>

      <el-card shadow="never">
        <template #header>连接配置</template>
        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="https://api.deepseek.com" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="isEdit && form.has_api_key ? `当前: ${form.api_key_masked}（留空则不修改）` : 'sk-...'"
          />
        </el-form-item>
        <el-form-item label="组织 (Org)">
          <el-input v-model="form.organization" placeholder="可选，OpenAI Organization ID" />
        </el-form-item>
        <el-form-item label="额外请求头">
          <el-input
            v-model="extraHeadersText"
            type="textarea"
            :rows="3"
            placeholder='JSON 格式，例如：{"X-Custom-Header": "value"}'
          />
        </el-form-item>
      </el-card>

      <el-card shadow="never">
        <template #header>运行参数</template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="超时秒数">
              <el-input-number v-model="form.timeout_seconds" :min="5" :max="600" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大重试">
              <el-input-number v-model="form.max_retries" :min="0" :max="10" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="开关">
          <el-checkbox v-model="form.enabled">启用</el-checkbox>
          <el-checkbox v-model="form.is_default">设为默认模型</el-checkbox>
        </el-form-item>
      </el-card>

      <el-form-item class="actions">
        <el-button type="primary" :loading="saving" @click="submit">{{ isEdit ? '保存' : '创建' }}</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'

const route = useRoute()
const router = useRouter()
const formRef = ref()
const loading = ref(false)
const saving = ref(false)
const isEdit = computed(() => Boolean(route.params.id))

const form = reactive({
  name: '',
  model_key: '',
  provider: 'openai_compatible',
  model_name: '',
  base_url: '',
  api_key: '',
  organization: '',
  timeout_seconds: 60,
  max_retries: 2,
  enabled: true,
  is_default: false,
  has_api_key: false,
  api_key_masked: '',
})

const extraHeadersText = ref('{}')

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  model_key: [
    { required: true, message: '请输入模型标识', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9._:-]+$/, message: '只允许字母、数字和 . _ : -', trigger: 'blur' },
  ],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  base_url: [
    { required: true, message: '请输入 Base URL', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value && !value.startsWith('http://') && !value.startsWith('https://')) {
          callback(new Error('Base URL 必须以 http:// 或 https:// 开头'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

onMounted(async () => {
  if (!isEdit.value) return
  loading.value = true
  try {
    const data = await request.get(`/api/llm-models/${route.params.id}`)
    Object.assign(form, {
      name: data.name,
      model_key: data.model_key,
      provider: data.provider,
      model_name: data.model_name,
      base_url: data.base_url,
      organization: data.organization || '',
      timeout_seconds: data.timeout_seconds,
      max_retries: data.max_retries,
      enabled: !!data.enabled,
      is_default: !!data.is_default,
      has_api_key: !!data.has_api_key,
      api_key_masked: data.api_key_masked || '',
    })
    extraHeadersText.value = JSON.stringify(data.extra_headers || {}, null, 2)
  } finally {
    loading.value = false
  }
})

const submit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  let extraHeaders = {}
  if (extraHeadersText.value.trim()) {
    try {
      extraHeaders = JSON.parse(extraHeadersText.value)
    } catch {
      ElMessage.error('额外请求头不是有效的 JSON')
      return
    }
  }

  const payload = {
    name: form.name,
    model_key: form.model_key,
    provider: form.provider,
    model_name: form.model_name,
    base_url: form.base_url,
    api_key: form.api_key,
    organization: form.organization,
    extra_headers: extraHeaders,
    timeout_seconds: form.timeout_seconds,
    max_retries: form.max_retries,
    enabled: form.enabled,
    is_default: form.is_default,
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await request.put(`/api/llm-models/${route.params.id}`, payload)
    } else {
      await request.post('/api/llm-models', payload)
    }
    ElMessage.success(isEdit.value ? '保存成功' : '创建成功')
    router.push('/modals')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.config-form {
  max-width: 900px;
}
.el-card {
  margin-bottom: 16px;
}
.actions {
  margin-top: 20px;
}
</style>
