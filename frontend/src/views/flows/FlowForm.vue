<template>
  <div>
    <div class="page-header"><h2>{{ isEdit ? '编辑 Flow' : '创建 Flow' }}</h2><el-button @click="router.push('/flows')">返回</el-button></div>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" class="config-form">
      <el-card shadow="never">
        <template #header>基本信息</template>
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="状态结构 JSON"><el-input v-model="stateSchemaText" type="textarea" :rows="3" placeholder='例如 {"department":"string"}' /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="form.enabled" active-text="启用" /></el-form-item>
      </el-card>

      <el-card shadow="never">
        <template #header><div class="card-header"><span>节点</span><el-button type="primary" size="small" @click="addNode"><el-icon><Plus /></el-icon>添加节点</el-button></div></template>
        <el-alert title="首个入度为 0 的节点会作为起点；建议每个节点使用稳定且唯一的 Key。" type="info" :closable="false" style="margin-bottom:14px" />
        <el-table :data="form.nodes" border>
          <el-table-column label="Key" min-width="130"><template #default="{ row }"><el-input v-model="row.node_key" placeholder="start" /></template></el-table-column>
          <el-table-column label="名称" min-width="150"><template #default="{ row }"><el-input v-model="row.name" /></template></el-table-column>
          <el-table-column label="类型" width="140"><template #default="{ row }"><el-select v-model="row.node_type" @change="onNodeTypeChange(row)"><el-option v-for="item in nodeTypes" :key="item.value" :label="item.label" :value="item.value" /></el-select></template></el-table-column>
          <el-table-column label="Crew" min-width="180"><template #default="{ row }"><el-select v-if="row.node_type === 'crew'" v-model="row.crew_id" style="width:100%"><el-option v-for="crew in crews" :key="crew.id" :label="crew.name" :value="crew.id" /></el-select><span v-else>-</span></template></el-table-column>
          <el-table-column label="配置 JSON" min-width="220"><template #default="{ row }"><el-input v-model="row.config_text" placeholder="{}" /></template></el-table-column>
          <el-table-column label="坐标 X/Y" width="190"><template #default="{ row }"><el-input-number v-model="row.position_x" controls-position="right" style="width:82px" /><el-input-number v-model="row.position_y" controls-position="right" style="width:82px;margin-left:6px" /></template></el-table-column>
          <el-table-column label="操作" width="80"><template #default="{ $index }"><el-button type="danger" link @click="removeNode($index)">删除</el-button></template></el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never">
        <template #header><div class="card-header"><span>连线与条件</span><el-button type="primary" size="small" @click="addEdge"><el-icon><Plus /></el-icon>添加连线</el-button></div></template>
        <el-table :data="form.edges" border>
          <el-table-column label="来源" min-width="150"><template #default="{ row }"><el-select v-model="row.source_key" style="width:100%"><el-option v-for="node in validNodes" :key="node.node_key" :label="node.name || node.node_key" :value="node.node_key" /></el-select></template></el-table-column>
          <el-table-column label="目标" min-width="150"><template #default="{ row }"><el-select v-model="row.target_key" style="width:100%"><el-option v-for="node in validNodes" :key="node.node_key" :label="node.name || node.node_key" :value="node.node_key" /></el-select></template></el-table-column>
          <el-table-column label="条件" width="150"><template #default="{ row }"><el-select v-model="row.condition_type"><el-option label="总是" value="always" /><el-option label="包含" value="contains" /><el-option label="等于" value="equals" /><el-option label="不包含" value="not_contains" /></el-select></template></el-table-column>
          <el-table-column label="条件值" min-width="180"><template #default="{ row }"><el-input v-model="row.condition_value" :disabled="row.condition_type === 'always'" /></template></el-table-column>
          <el-table-column label="优先级" width="120"><template #default="{ row }"><el-input-number v-model="row.priority" :min="0" controls-position="right" /></template></el-table-column>
          <el-table-column label="操作" width="80"><template #default="{ $index }"><el-button type="danger" link @click="form.edges.splice($index, 1)">删除</el-button></template></el-table-column>
        </el-table>
      </el-card>
      <el-form-item class="actions"><el-button type="primary" :loading="saving" @click="submit">保存</el-button></el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../../utils/request'
const route = useRoute(), router = useRouter(), isEdit = computed(() => Boolean(route.params.id))
const formRef = ref(), saving = ref(false), crews = ref([]), stateSchemaText = ref('{}')
const form = reactive({ name: '', description: '', enabled: true, nodes: [], edges: [] })
const rules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }
const nodeTypes = [{ value: 'crew', label: '执行 Crew' }, { value: 'condition', label: '条件判断' }, { value: 'approval', label: '人工审批' }, { value: 'transform', label: '数据转换' }, { value: 'end', label: '结束' }]
const validNodes = computed(() => form.nodes.filter(node => node.node_key))
const addNode = () => form.nodes.push({ node_key: `node_${form.nodes.length + 1}`, name: '', node_type: 'crew', crew_id: null, config_text: '{}', position_x: form.nodes.length * 220, position_y: 0 })
const addEdge = () => form.edges.push({ source_key: '', target_key: '', condition_type: 'always', condition_value: '', priority: 0 })
const onNodeTypeChange = row => { if (row.node_type !== 'crew') row.crew_id = null }
const removeNode = index => { const key = form.nodes[index].node_key; form.nodes.splice(index, 1); form.edges = form.edges.filter(edge => edge.source_key !== key && edge.target_key !== key) }
const parseJson = (text, label) => { try { const value = JSON.parse(text || '{}'); if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error(); return value } catch { throw new Error(`${label}必须是 JSON 对象`) } }

onMounted(async () => {
  crews.value = (await request.get('/api/crews')).filter(item => item.enabled)
  if (!isEdit.value) { addNode(); return }
  const data = await request.get(`/api/flows/${route.params.id}`)
  Object.assign(form, data, { nodes: (data.nodes || []).map(node => ({ ...node, config_text: JSON.stringify(node.config || {}, null, 0) })), edges: data.edges || [] })
  stateSchemaText.value = JSON.stringify(data.state_schema || {}, null, 2)
})
const submit = async () => {
  const valid = await formRef.value.validate().catch(() => false); if (!valid) return
  if (!form.nodes.length) { ElMessage.warning('请至少添加一个节点'); return }
  const keys = form.nodes.map(node => node.node_key.trim())
  if (keys.some(key => !key) || new Set(keys).size !== keys.length) { ElMessage.warning('节点 Key 不能为空且不能重复'); return }
  let state_schema, nodes
  try { state_schema = parseJson(stateSchemaText.value, '状态结构'); nodes = form.nodes.map(node => ({ ...node, node_key: node.node_key.trim(), config: parseJson(node.config_text, `节点 ${node.name || node.node_key} 的配置`) })) } catch (error) { ElMessage.error(error.message); return }
  if (nodes.some(node => node.node_type === 'crew' && !node.crew_id)) { ElMessage.warning('执行 Crew 类型的节点必须选择 Crew'); return }
  if (form.edges.some(edge => !edge.source_key || !edge.target_key || edge.source_key === edge.target_key)) { ElMessage.warning('连线必须选择不同的来源和目标节点'); return }
  saving.value = true
  try {
    const payload = { name: form.name, description: form.description, enabled: form.enabled, state_schema, nodes: nodes.map(({ config_text, ...node }) => node), edges: form.edges }
    if (isEdit.value) await request.put(`/api/flows/${route.params.id}`, payload); else await request.post('/api/flows', payload)
    ElMessage.success('保存成功'); router.push('/flows')
  } finally { saving.value = false }
}
</script>

<style scoped>
.config-form { min-width:960px; }
.el-card { margin-bottom:16px; }
.card-header { display:flex; align-items:center; justify-content:space-between; }
.actions { margin-top:20px; }
</style>
