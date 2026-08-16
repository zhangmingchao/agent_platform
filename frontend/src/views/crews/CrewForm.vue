<template>
  <div>
    <div class="page-header"><h2>{{ isEdit ? '编辑 Crew' : '创建 Crew' }}</h2><el-button @click="router.push('/crews')">返回</el-button></div>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="130px" class="config-form">
      <el-card shadow="never">
        <template #header>团队配置</template>
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="执行方式" prop="process"><el-radio-group v-model="form.process"><el-radio value="sequential">顺序执行</el-radio><el-radio value="hierarchical">层级委派</el-radio></el-radio-group></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="最大 RPM"><el-input-number v-model="form.max_rpm" :min="1" clearable /></el-form-item></el-col>
        </el-row>
        <el-form-item label="成员 Agent" prop="agent_ids"><el-select v-model="form.agent_ids" multiple filterable style="width:100%" @change="syncAgentSelection"><el-option v-for="item in agents" :key="item.id" :label="`${item.name}（${item.role}）`" :value="item.id" /></el-select></el-form-item>
        <el-form-item v-if="form.process === 'hierarchical'" label="Manager" prop="manager_agent_id"><el-select v-model="form.manager_agent_id" style="width:100%" placeholder="从成员中选择 Manager"><el-option v-for="item in memberAgents" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
        <el-form-item label="执行开关"><el-checkbox v-model="form.planning">Planning</el-checkbox><el-checkbox v-model="form.memory">Memory</el-checkbox><el-checkbox v-model="form.cache_enabled">Cache</el-checkbox><el-checkbox v-model="form.verbose">Verbose</el-checkbox><el-checkbox v-model="form.enabled">启用</el-checkbox></el-form-item>
      </el-card>

      <el-card shadow="never">
        <template #header><div class="card-header"><span>Task 编排</span><el-button type="primary" size="small" @click="addTask"><el-icon><Plus /></el-icon>添加 Task</el-button></div></template>
        <el-empty v-if="!form.tasks.length" description="请至少添加一个 Task" />
        <el-card v-for="(task, index) in form.tasks" :key="task.client_key" shadow="never" class="task-card">
          <template #header><div class="card-header"><strong>Task {{ index + 1 }}：{{ task.name || '未命名' }}</strong><div><el-button size="small" :disabled="index === 0" @click="moveTask(index, -1)">上移</el-button><el-button size="small" :disabled="index === form.tasks.length - 1" @click="moveTask(index, 1)">下移</el-button><el-button type="danger" size="small" @click="removeTask(index)">删除</el-button></div></div></template>
          <el-row :gutter="20"><el-col :span="12"><el-form-item label="名称" :prop="`tasks.${index}.name`" :rules="required('请输入 Task 名称')"><el-input v-model="task.name" /></el-form-item></el-col><el-col :span="12"><el-form-item label="负责 Agent" :prop="`tasks.${index}.agent_id`" :rules="form.process === 'sequential' ? required('请选择负责 Agent') : []"><el-select v-model="task.agent_id" clearable style="width:100%" placeholder="层级模式可由 Manager 分派"><el-option v-for="item in taskAgents" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item></el-col></el-row>
          <el-form-item label="任务描述" :prop="`tasks.${index}.description`" :rules="required('请输入任务描述')"><el-input v-model="task.description" type="textarea" :rows="3" placeholder="可使用 {{ user_input }} 引用用户输入" /></el-form-item>
          <el-form-item label="预期输出" :prop="`tasks.${index}.expected_output`" :rules="required('请输入预期输出')"><el-input v-model="task.expected_output" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="依赖 Task"><el-select v-model="task.dependency_keys" multiple clearable style="width:100%"><el-option v-for="candidate in dependencyCandidates(task)" :key="candidate.client_key" :label="candidate.name || candidate.client_key" :value="candidate.client_key" /></el-select></el-form-item>
          <el-alert title="以下 Skill/MCP 是负责 Agent 已有能力的任务级白名单；不选择表示允许使用该 Agent 的全部对应能力。" type="info" :closable="false" style="margin-bottom:14px" />
          <el-row :gutter="20"><el-col :span="12"><el-form-item label="Skill 白名单"><el-select v-model="task.skill_ids" multiple clearable style="width:100%"><el-option v-for="item in agentSkills(task.agent_id)" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item></el-col><el-col :span="12"><el-form-item label="MCP 白名单"><el-select v-model="task.mcp_ids" multiple clearable style="width:100%"><el-option v-for="item in agentMcps(task.agent_id)" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item></el-col></el-row>
          <el-row :gutter="20"><el-col :span="12"><el-form-item label="输出文件"><el-input v-model="task.output_file" placeholder="可选，例如 output/report.md" /></el-form-item></el-col><el-col :span="12"><el-form-item label="失败重试"><el-input-number v-model="task.max_retries" :min="0" :max="10" /></el-form-item></el-col></el-row>
          <el-form-item label="Task 开关"><el-checkbox v-model="task.async_execution">异步执行</el-checkbox><el-checkbox v-model="task.markdown">Markdown 输出</el-checkbox><el-checkbox v-model="task.human_input">人工确认（预留）</el-checkbox></el-form-item>
          <el-form-item label="Guardrail"><el-input v-model="task.guardrail" placeholder="可选，输出约束说明" /></el-form-item>
        </el-card>
      </el-card>
      <el-form-item class="actions"><el-button type="primary" :loading="saving" @click="submit">保存</el-button></el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'

const route = useRoute(), router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const formRef = ref(), saving = ref(false), agents = ref([])
const form = reactive({ name: '', description: '', process: 'sequential', manager_agent_id: null, agent_ids: [], tasks: [], planning: false, memory: false, cache_enabled: false, verbose: false, max_rpm: null, enabled: true })
const rules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }], agent_ids: [{ type: 'array', required: true, min: 1, message: '至少选择一个 Agent', trigger: 'change' }] }
const required = message => [{ required: true, message, trigger: 'blur' }]
const memberAgents = computed(() => agents.value.filter(item => form.agent_ids.includes(item.id)))
const taskAgents = computed(() => memberAgents.value.filter(item => form.process !== 'hierarchical' || item.id !== form.manager_agent_id))
const newTask = () => ({ client_key: `task_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`, name: '', description: '处理用户输入：{{ user_input }}', expected_output: '完整、准确的结果', agent_id: null, dependency_keys: [], skill_ids: [], mcp_ids: [], async_execution: false, human_input: false, markdown: true, guardrail: '', max_retries: 2, output_file: '' })
const addTask = () => form.tasks.push(newTask())
const removeTask = index => { const [removed] = form.tasks.splice(index, 1); form.tasks.forEach(task => { task.dependency_keys = task.dependency_keys.filter(key => key !== removed.client_key) }) }
const moveTask = (index, offset) => {
  const target = index + offset
  if (target < 0 || target >= form.tasks.length) return
  ;[form.tasks[index], form.tasks[target]] = [form.tasks[target], form.tasks[index]]
  const positions = Object.fromEntries(form.tasks.map((task, taskIndex) => [task.client_key, taskIndex]))
  form.tasks.forEach((task, taskIndex) => { task.dependency_keys = task.dependency_keys.filter(key => positions[key] < taskIndex) })
}
const dependencyCandidates = task => {
  const index = form.tasks.findIndex(item => item.client_key === task.client_key)
  return form.tasks.slice(0, Math.max(0, index))
}
const selectedAgent = id => agents.value.find(item => item.id === id)
const agentSkills = id => selectedAgent(id)?.skills || []
const agentMcps = id => selectedAgent(id)?.mcps || []
const syncAgentSelection = () => { if (!form.agent_ids.includes(form.manager_agent_id)) form.manager_agent_id = null; form.tasks.forEach(task => { if (!form.agent_ids.includes(task.agent_id)) { task.agent_id = null; task.skill_ids = []; task.mcp_ids = [] } }) }
watch(() => form.process, value => { if (value === 'sequential') form.manager_agent_id = null })
watch(() => form.manager_agent_id, managerId => {
  if (!managerId || form.process !== 'hierarchical') return
  form.tasks.forEach(task => { if (task.agent_id === managerId) { task.agent_id = null; task.skill_ids = []; task.mcp_ids = [] } })
})

onMounted(async () => {
  const summaries = await request.get('/api/agentsList')
  agents.value = await Promise.all(summaries.filter(item => item.enabled).map(item => request.get(`/api/agents/${item.id}`)))
  if (!isEdit.value) { addTask(); return }
  const data = await request.get(`/api/crews/${route.params.id}`)
  const keyById = Object.fromEntries((data.tasks || []).map(task => [task.id, `task_${task.id}`]))
  Object.assign(form, data, {
    // aiomysql 返回 TINYINT 为 int 0/1，checkbox 需要严格的 true/false 布尔
    planning: Boolean(data.planning ?? false),
    memory: Boolean(data.memory ?? false),
    cache_enabled: Boolean(data.cache_enabled ?? false),
    verbose: Boolean(data.verbose ?? false),
    enabled: Boolean(data.enabled ?? true),
    max_rpm: data.max_rpm ?? null,
    agent_ids: (data.agents || []).map(item => item.id),
    tasks: (data.tasks || []).map(task => ({ ...task, client_key: keyById[task.id], dependency_keys: (task.dependency_ids || []).map(id => keyById[id]).filter(Boolean), skill_ids: task.skill_ids || [], mcp_ids: task.mcp_ids || [],
      async_execution: Boolean(task.async_execution ?? false),
      human_input: Boolean(task.human_input ?? false),
      markdown: Boolean(task.markdown ?? true),
    }))
  })
})

const submit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (!form.tasks.length) { ElMessage.warning('请至少添加一个 Task'); return }
  saving.value = true
  try {
    const payload = { ...form, tasks: form.tasks.map((task, index) => ({ ...task, order_no: index + 1 })) }
    if (isEdit.value) await request.put(`/api/crews/${route.params.id}`, payload)
    else await request.post('/api/crews', payload)
    ElMessage.success('保存成功')
    router.push('/crews')
  } finally { saving.value = false }
}
</script>

<style scoped>
.config-form { max-width: 1100px; }
.el-card { margin-bottom: 16px; }
.task-card { margin: 14px 0; border-color: #dcdfe6; }
.card-header { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.actions { margin-top:20px; }
</style>
