<template>
  <div>
    <div class="page-header">
      <h2>{{ isEdit ? '编辑 Agent' : '创建 Agent' }}</h2>
      <el-button @click="router.push('/agents')">返回</el-button>
    </div>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="130px" class="config-form">
      <el-card shadow="never">
        <template #header>身份与目标</template>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name"/>
        </el-form-item>
        <el-form-item label="列表描述">
          <el-input v-model="form.description" type="textarea" :rows="2"/>
        </el-form-item>
        <el-form-item label="Role" prop="role">
          <el-input v-model="form.role" placeholder="例如：资深数据分析师"/>
        </el-form-item>
        <el-form-item label="Goal" prop="goal">
          <el-input v-model="form.goal" type="textarea" :rows="3" placeholder="该 Agent 要持续达成的目标"/>
        </el-form-item>
        <el-form-item label="Backstory">
          <el-input v-model="form.backstory" type="textarea" :rows="4" placeholder="专业背景、经验和工作风格"/>
        </el-form-item>
        <el-form-item label="额外行为规则">
          <el-input v-model="form.system_prompt" type="textarea" :rows="4"/>
        </el-form-item>
      </el-card>

      <el-card shadow="never">
        <template #header>模型与执行能力</template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模型">
              <el-select v-model="form.model" style="width:100%">
                <el-option v-for="m in models" :key="m.value" :label="m.label" :value="m.value"/>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="温度">
              <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1"/>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="最大迭代次数">
          <el-input-number v-model="form.iteration_count" :min="1" :max="100"/>
        </el-form-item>
        <el-form-item label="能力开关">
          <el-checkbox v-model="form.allow_delegation">允许委派</el-checkbox>
          <el-checkbox v-model="form.reasoning">Reasoning</el-checkbox>
          <el-checkbox v-model="form.planning">Planning</el-checkbox>
          <el-checkbox v-model="form.memory">Memory</el-checkbox>
          <el-checkbox v-model="form.enabled">启用</el-checkbox>
        </el-form-item>
      </el-card>

      <el-card shadow="never">
        <template #header>Agent 能力（Tool / Skill / MCP）</template>
        <el-form-item label="Skills">
          <el-select v-model="form.skill_ids" multiple style="width:100%" placeholder="选择 Agent 可以使用的 Skill">
            <el-option v-for="item in skills" :key="item.id" :label="item.name" :value="item.id"/>
          </el-select>
        </el-form-item>
        <el-form-item label="MCP Servers">
          <el-select v-model="form.mcp_ids" multiple style="width:100%" placeholder="选择 Agent 可以使用的 MCP">
            <el-option v-for="item in mcps" :key="item.id" :label="item.name" :value="item.id"/>
          </el-select>
        </el-form-item>
      </el-card>

      <el-form-item class="actions">
        <el-button type="primary" :loading="saving" @click="submit">{{ isEdit ? '保存' : '创建' }}</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import {computed, onMounted, reactive, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import request from '../../utils/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const formRef = ref()
const saving = ref(false)
const models = ref([])
const skills = ref([])
const mcps = ref([])
const form = reactive({
  name: '', description: '', role: 'AI Agent', goal: '', backstory: '', system_prompt: '',
  model: 'deepseek-chat', temperature: 0.7, iteration_count: 6,
  allow_delegation: false, reasoning: false, planning: false, memory: false, enabled: true,
  skill_ids: [], mcp_ids: []
})
const rules = {
  name: [{required: true, message: '请输入名称', trigger: 'blur'}],
  role: [{required: true, message: '请输入 Role', trigger: 'blur'}],
  goal: [{required: true, message: '请输入 Goal', trigger: 'blur'}]
}

onMounted(async () => {
  const [modelList, skillList, mcpList] = await Promise.all([
    request.get('/api/ll_models'), request.get('/api/skills'), request.get('/api/mcp-configs')
  ])
  models.value = modelList
  skills.value = skillList
  mcps.value = mcpList
  if (isEdit.value) {
    const data = await request.get(`/api/agents/${route.params.id}`)
    Object.assign(form, data, {
      skill_ids: data.skills?.map(item => item.id) || [],
      mcp_ids: data.mcps?.map(item => item.id) || []
    })
  }
})

const submit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (isEdit.value) await request.put(`/api/agents/${route.params.id}`, form)
    else await request.post('/api/agents', form)
    ElMessage.success('保存成功')
    router.push('/agents')
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
