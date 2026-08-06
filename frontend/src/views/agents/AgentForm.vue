<template>
  <div class="agent-form">
    <div class="page-header">
      <h2>{{ isEdit ? '编辑 Agent' : '创建 Agent' }}</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width: 700px">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="给 Agent 起个名字" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="2" placeholder="简要描述 Agent 的能力" />
      </el-form-item>
      <el-form-item label="系统提示词" prop="system_prompt">
        <el-input v-model="form.system_prompt" type="textarea" :rows="6" placeholder="定义 Agent 的角色、行为、专长等" />
      </el-form-item>
      <el-form-item label="迭代次数" prop="iteration_count">
        <el-input v-model="form.iteration_count"
                  :min="1"
                  type="number"
                  :max="100"
                  placeholder="请输入最大迭代次数"
        />
      </el-form-item>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="模型" prop="model">
            <el-select v-model="form.model" style="width: 100%">
              <el-option value="deepseek-chat" label="deepseek-chat" />
              <el-option value="deepseek-reasoner" label="deepseek-reasoner" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="温度" prop="temperature">
            <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" style="padding: 10px" />
          </el-form-item>
        </el-col>
      </el-row>

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
import { ref, reactive, computed, onMounted,onActivated  } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const formRef = ref()
const saving = ref(false)

const form = reactive({
  name: '',
  description: '',
  system_prompt: '',
  iteration_count: 6,
  model: 'deepseek-chat',
  temperature: 0.7,
  skill_ids: [],
  mcp_ids: []
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  iteration_count: [{ required: true, message: '迭代次数必须大于0', trigger: 'blur' }],
}

const skills = ref([])
const mcps = ref([])

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
      form.iteration_count = agent.iteration_count || 6
      form.model = agent.model
      form.temperature = agent.temperature
      form.skill_ids = agent.skills?.map(s => s.id) || []
      form.mcp_ids = agent.mcps?.map(m => m.id) || []
    }
  } catch (e) { /* handled */ }
}

const handleSubmit = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      await request.put(`/api/agents/${route.params.id}`, form)
      ElMessage.success('保存成功')
    } else {
      await request.post('/api/agents', form)
      ElMessage.success('创建成功')
      router.push('/agents')
    }
  } finally {
    saving.value = false
  }
}

onMounted(loadData)



</script>
