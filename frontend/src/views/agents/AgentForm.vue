<template>
  <div class="agent-form">
    <div class="page-header">
      <h2>{{ isEdit ? '编辑 Agent' : '创建 Agent' }}</h2>
      <el-button @click="$router.go(-1)">返回</el-button>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width: 700px">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="给 Agent 起个名字" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="2" placeholder="简要描述 Agent 的能力" />
      </el-form-item>
      <el-form-item label="系统提示词" prop="system_prompt">
        <el-input v-model="form.system_prompt" type="textarea" :rows="6" placeholder="定义 Agent 的角色、行为、专长。支持 {{user_input}} 等模板变量" />
      </el-form-item>
      <el-form-item label="模板变量">
        <el-input v-model="promptVariablesText" type="textarea" :rows="4" placeholder='JSON 对象，例如：{"language":"中文","style":"简洁"}' />
        <div class="field-hint">在提示词中使用 &#123;&#123;language&#125;&#125;。系统变量：user_input、username、user_id、session_id、current_date；工作流还支持 workflow_id、run_id、step_order、role、instruction。</div>
      </el-form-item>
      <el-form-item label="结构化输出">
        <el-switch v-model="structuredOutputEnabled" />
        <span class="switch-label">要求最终结果符合 JSON Schema</span>
      </el-form-item>
      <el-form-item v-if="structuredOutputEnabled" label="输出模型">
        <div class="schema-editor">
          <el-radio-group v-model="schemaEditorMode" size="small" @change="switchSchemaEditorMode">
            <el-radio-button value="python">Python 模型</el-radio-button>
            <el-radio-button value="json">JSON Schema</el-radio-button>
          </el-radio-group>
          <el-input
            v-if="schemaEditorMode === 'python'"
            v-model="pythonSchemaText"
            type="textarea"
            :rows="12"
            resize="vertical"
            placeholder="class StructuredOutput(BaseModel):&#10;    answer: str = Field(description='最终答案')"
          />
          <el-input
            v-else
            v-model="outputSchemaText"
            type="textarea"
            :rows="12"
            resize="vertical"
            placeholder='{"type":"object","required":["answer"],"properties":{"answer":{"type":"string"}}}'
          />
        </div>
        <div class="field-hint">
          Python 模型仅作为 Schema 描述语言，服务器只解析 AST，不会执行代码。保存时转换为 JSON Schema；模型最终仍输出 JSON。
        </div>
      </el-form-item>
      <el-form-item label="迭代次数" prop="iteration_count">
        <el-input v-model="form.iteration_count"
                  :min="1"
                  type="number"
                  :max="100"
                  placeholder="请输入最大迭代次数"
        />
      </el-form-item>

      <el-form-item label="模型来源">
        <el-radio-group v-model="modelSource" @change="onModelSourceChange">
          <el-radio-button label="custom" value="custom" >自定义模型</el-radio-button>
          <el-radio-button label="builtin" value="builtin">内置模型</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="模型" prop="model">
            <el-select v-model="form.model" style="width: 100%" @change="onModelChange">
              <template v-if="modelSource === 'custom'">
                <el-option
                  v-for="m in userModels"
                  :key="m.id"
                  :value="m.model_id"
                  :label="m.name"
                >
                  {{ m.name }} <span style="color: #9ca3af; font-size: 12px">- {{ m.model_id }}</span>
                </el-option>
              </template>
              <template v-else>
                <el-option
                  v-for="item in builtinModels"
                  :key="item.value"
                  :value="item.value"
                  :label="item.label"
                />
              </template>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="温度" prop="temperature">
            <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" style="padding: 10px" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item v-if="modelSource === 'custom' && userModels.length === 0">
        <el-alert type="info" :closable="false" show-icon>
          还没有自定义模型，请先到「模型管理」添加。
          <el-button type="primary" link @click="$router.push('/models')">去添加</el-button>
        </el-alert>
      </el-form-item>

      <el-divider content-position="left">关联 Skill</el-divider>
      <el-form-item label="Skills">
        <el-select v-model="form.skill_ids" multiple placeholder="选择 Skill" style="width: 100%">
          <el-option v-for="s in skills" :key="s.id" :label="s.name" :value="s.id">
            {{ s.name }} <span style="color: #9ca3af; font-size: 12px">- {{ s.description }}</span>
          </el-option>
        </el-select>
      </el-form-item>

      <el-divider content-position="left">关联 MCP</el-divider>
      <el-form-item label="MCP 配置">
        <el-select v-model="form.mcp_ids" multiple placeholder="选择 MCP 配置" style="width: 100%">
          <el-option v-for="m in mcps" :key="m.id" :label="m.name" :value="m.id">
            {{ m.name }} <span style="color: #9ca3af; font-size: 12px">- {{ m.base_url }}</span>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="saving">
          {{ isEdit ? '保存修改' : '创建' }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const formRef = ref()
const saving = ref(false)
const structuredOutputEnabled = ref(false)
const schemaEditorMode = ref('python')
const promptVariablesText = ref('{}')
const pythonSchemaText = ref(`class StructuredOutput(BaseModel):
    answer: str = Field(description="最终答案")`)
const outputSchemaText = ref(JSON.stringify({
  type: 'object',
  required: ['answer'],
  properties: { answer: { type: 'string' } }
}, null, 2))

const form = reactive({
  name: '',
  description: '',
  system_prompt: '',
  prompt_variables: {},
  output_schema: null,
  iteration_count: 6,
  model: 'deepseek-chat',
  model_config_id: null,
  temperature: 0.7,
  skill_ids: [],
  mcp_ids: []
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  iteration_count: [{ required: true, message: '迭代次数必须大于0', trigger: 'blur' }],
}

const modelSource = ref('builtin')
const userModels = ref([])
const builtinModels = ref([])
const skills = ref([])
const moduleList = ref([])
const mcps = ref([])

const parsePythonSchema = async () => {
  const result = await request.post('/api/output-schema/python-to-json', { source: pythonSchemaText.value })
  outputSchemaText.value = JSON.stringify(result.schema, null, 2)
  return result.schema
}

const renderPythonSchema = async (schema) => {
  const result = await request.post('/api/output-schema/json-to-python', { schema_data: schema })
  pythonSchemaText.value = result.source
}

// 两种编辑模式操作同一份 Schema；切换时立即转换，让用户能够核对最终 JSON。
const switchSchemaEditorMode = async (mode) => {
  try {
    if (mode === 'json') {
      await parsePythonSchema()
    } else {
      const schema = JSON.parse(outputSchemaText.value || '{}')
      await renderPythonSchema(schema)
    }
  } catch (error) {
    schemaEditorMode.value = mode === 'json' ? 'python' : 'json'
    // HTTP 错误已由 request 拦截器展示，这里只补充本地 JSON 解析错误。
    if (!error.response) ElMessage.error(error.message || 'Schema 转换失败')
  }
}

const onModelSourceChange = () => {
  if (modelSource.value === 'custom') {
    form.model_config_id = userModels.value.length > 0 ? userModels.value[0].id: null
    form.model = userModels.value.length > 0 ? userModels.value[0].model_id : ''
  } else {
    form.model_config_id = null
    form.model = builtinModels.value.length > 0 ? builtinModels.value[0].value : 'deepseek-chat'
  }
  debugger
}

const onModelChange = (val) => {
  if (modelSource.value === 'custom') {
    const selected = userModels.value.find(m => m.model_id === val)
    form.model_config_id = selected ? selected.id : null
  } else {
    form.model_config_id = null
  }
  debugger
}

const loadUserModels = async () => {
  try {
    userModels.value = await request.get('/api/modelsList')
  } catch (e) {
    userModels.value = []
  }
}

const loadBuiltinModels = async () => {
  try {
    builtinModels.value = await request.get('/api/ll_models')
  } catch (e) {
    builtinModels.value = []
  }
}

const loadData = async () => {
  try {
    const [skillsList, mcpsList] = await Promise.all([
      request.get('/api/skills'),
      request.get('/api/mcp-configs')
    ])
    skills.value = skillsList
    mcps.value = mcpsList

    if (isEdit.value) {
      const agent = await request.get(`/api/agents/${route.params.id}`)
      form.name = agent.name
      form.description = agent.description
      form.system_prompt = agent.system_prompt
      promptVariablesText.value = JSON.stringify(agent.prompt_variables || {}, null, 2)
      structuredOutputEnabled.value = !!agent.output_schema
      if (agent.output_schema) {
        outputSchemaText.value = JSON.stringify(agent.output_schema, null, 2)
        try {
          await renderPythonSchema(agent.output_schema)
        } catch {
          // 极复杂的历史 JSON Schema 仍可在 JSON 模式继续编辑。
          schemaEditorMode.value = 'json'
        }
      }
      form.iteration_count = agent.iteration_count || 6
      form.model = agent.model
      form.model_config_id = agent.model_config_id
      form.temperature = agent.temperature
      form.skill_ids = agent.skills?.map(s => s.id) || []
      form.mcp_ids = agent.mcps?.map(m => m.id) || []

      if (agent.model_config_id) {
        modelSource.value = 'custom'
      } else {
        modelSource.value = 'builtin'
      }
    }
  } catch (e) { /* 已处理 */ }
}

const handleSubmit = async () => {
  await formRef.value.validate()
  try {
    form.prompt_variables = JSON.parse(promptVariablesText.value || '{}')
    if (!form.prompt_variables || Array.isArray(form.prompt_variables) || typeof form.prompt_variables !== 'object') {
      throw new Error('模板变量必须是 JSON 对象')
    }
    if (!structuredOutputEnabled.value) {
      form.output_schema = null
    } else if (schemaEditorMode.value === 'python') {
      form.output_schema = await parsePythonSchema()
    } else {
      form.output_schema = JSON.parse(outputSchemaText.value || '{}')
    }
    if (structuredOutputEnabled.value && (!form.output_schema || Array.isArray(form.output_schema) || typeof form.output_schema !== 'object')) {
      throw new Error('JSON Schema 必须是 JSON 对象')
    }
  } catch (error) {
    if (!error.response) ElMessage.error(error.message || 'Schema 配置格式错误')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await request.put(`/api/agents/${route.params.id}`, form)
      ElMessage.success('保存成功')
      router.push('/agents')
    } else {
      await request.post('/api/agents', form)
      ElMessage.success('创建成功')
      router.push('/agents')
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadData(), loadUserModels(), loadBuiltinModels()])
})
</script>

<style scoped>
.field-hint { margin-top: 6px; color: #909399; font-size: 12px; line-height: 1.5; }
.switch-label { margin-left: 10px; color: #606266; font-size: 13px; }
.schema-editor { width: 100%; display: flex; flex-direction: column; gap: 10px; }
.schema-editor :deep(textarea) { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; line-height: 1.55; }
</style>
