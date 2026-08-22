<template>
  <div class="workflow-form">
    <div class="page-header">
      <h2>{{ isEdit ? '编辑工作流' : '创建工作流' }}</h2>
      <el-button @click="$router.go(-1)">返回</el-button>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" class="wf-meta">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" maxlength="200" placeholder="例如：需求分析与审查" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="2" placeholder="简要说明" />
      </el-form-item>
    </el-form>

    <div class="wf-canvas-shell">
      <!-- 节点面板 -->
      <div class="wf-palette">
        <div class="palette-title">节点类型</div>
        <div class="palette-item" draggable @dragstart="onDragStart($event, 'agent')" @click="addNodeAtCenter('agent')">
          <el-icon><User /></el-icon><span>Agent 节点</span>
        </div>
        <div class="palette-item" draggable @dragstart="onDragStart($event, 'condition')" @click="addNodeAtCenter('condition')">
          <el-icon><Switch /></el-icon><span>条件分支</span>
        </div>
        <div class="palette-item" draggable @dragstart="onDragStart($event, 'parallel')" @click="addNodeAtCenter('parallel')">
          <el-icon><Share /></el-icon><span>并行执行</span>
        </div>
        <div class="palette-item" draggable @dragstart="onDragStart($event, 'output')" @click="addNodeAtCenter('output')">
          <el-icon><Download /></el-icon><span>输出节点</span>
        </div>
        <el-divider />
        <div class="palette-hint">拖拽到画布或点击添加</div>
      </div>

      <!-- 画布 -->
      <div class="wf-canvas" @drop="onDrop" @dragover.prevent @dragenter.prevent>
        <VueFlow
          :nodes="nodes"
          :edges="edges"
          :node-types="nodeTypes"
          :default-edge-options="{ type: 'smoothstep', animated: true }"
          fit-view-on-init
          @connect="onConnect"
          @node-click="onNodeClick"
          @node-drag-stop="onNodeDragStop"
          @edge-click="onEdgeClick"
        >
          <Background pattern-color="#aaa" :gap="16" />
          <Controls />
          <MiniMap />
        </VueFlow>
      </div>

      <!-- 配置面板 -->
      <div class="wf-config">
        <template v-if="selectedNode">
          <div class="config-title">节点配置</div>

          <el-form label-width="80px" size="small">
            <el-form-item label="名称">
              <el-input v-model="selectedNode.data.label" placeholder="节点名称" />
            </el-form-item>

            <!-- Agent 配置 -->
            <template v-if="selectedNode.type === 'agent'">
              <el-form-item label="Agent">
                <el-select v-model="selectedNode.data.agent_id" filterable placeholder="选择 Agent" style="width:100%" @change="onAgentChange">
                  <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id">
                    <span>{{ a.name }}</span>
                    <span class="opt-meta">- {{ a.description || '无描述' }}</span>
                  </el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="角色">
                <el-input v-model="selectedNode.data.role" placeholder="例如：需求分析师" />
              </el-form-item>
              <el-form-item label="指令">
                <el-input v-model="selectedNode.data.instruction" type="textarea" :rows="6" placeholder="告诉 Agent 当前步骤要做什么" />
              </el-form-item>
            </template>

            <!-- 条件分支配置 -->
            <template v-if="selectedNode.type === 'condition'">
              <el-form-item label="说明">
                <div class="cond-hint">按顺序匹配，命中则走对应分支。未命中走"默认"分支。</div>
              </el-form-item>
              <div v-for="(cond, i) in selectedNode.data.conditions" :key="i" class="cond-row">
                <div class="cond-label">分支 {{ i + 1 }}</div>
                <el-input v-model="cond.label" placeholder="分支名称" size="small" />
                <el-select v-model="cond.type" size="small" style="margin-top:4px">
                  <el-option label="包含关键词" value="contains" />
                  <el-option label="正则匹配" value="regex" />
                  <el-option label="默认/其他" value="else" />
                </el-select>
                <el-input v-if="cond.type !== 'else'" v-model="cond.value" placeholder="关键词或正则表达式" size="small" style="margin-top:4px" />
                <el-button text type="danger" size="small" @click="removeCondition(i)" style="margin-top:4px">删除分支</el-button>
              </div>
              <el-button text type="primary" size="small" @click="addCondition">+ 添加分支</el-button>
            </template>

            <!-- 并行节点配置 -->
            <template v-if="selectedNode.type === 'parallel'">
              <el-form-item label="说明">
                <div class="cond-hint">并行节点会同时执行所有下游连接的节点，结果合并后传给下一个节点。</div>
              </el-form-item>
            </template>

            <el-divider />
            <el-button text type="danger" @click="deleteSelectedNode">删除此节点</el-button>
          </el-form>
        </template>
        <el-empty v-else description="点击画布中的节点进行配置" :image-size="60" />
      </div>
    </div>

    <div class="wf-actions">
      <el-button type="primary" :loading="saving" @click="handleSubmit">
        {{ isEdit ? '保存修改' : '创建工作流' }}
      </el-button>
      <el-button @click="$router.push('/workflows')">取消</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, markRaw, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Switch, Share, Download, Promotion } from '@element-plus/icons-vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

import InputNode from './nodes/InputNode.vue'
import AgentNode from './nodes/AgentNode.vue'
import ConditionNode from './nodes/ConditionNode.vue'
import ParallelNode from './nodes/ParallelNode.vue'
import OutputNode from './nodes/OutputNode.vue'
import request from '../../utils/request'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)

const formRef = ref()
const saving = ref(false)
const agents = ref([])
const selectedNodeId = ref(null)
let nodeCounter = 0

const form = reactive({ name: '', description: '' })
const rules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }

const nodeTypes = {
  input: markRaw(InputNode),
  agent: markRaw(AgentNode),
  condition: markRaw(ConditionNode),
  parallel: markRaw(ParallelNode),
  output: markRaw(OutputNode),
}

const nodes = ref([])
const edges = ref([])

const { addEdges, addNodes, screenToFlowCoordinate, onConnect, onNodeClick, removeNodes } = useVueFlow()

onConnect((params) => {
  const edge = { ...params, id: `edge-${Date.now()}`, type: 'smoothstep', animated: true }
  addEdges([edge])
})

onNodeClick(({ node }) => {
  selectedNodeId.value = node.id
})

const selectedNode = computed(() => nodes.value.find(n => n.id === selectedNodeId.value) || null)

const onAgentChange = (agentId) => {
  if (!selectedNode.value) return
  const agent = agents.value.find(a => a.id === agentId)
  if (agent) selectedNode.value.data.agent_name = agent.name
}

const createNodeData = (type) => {
  const base = { label: { agent: 'Agent 节点', condition: '条件分支', parallel: '并行执行', output: '输出' }[type] || type }
  if (type === 'agent') return { ...base, agent_id: null, agent_name: '', role: '', instruction: '' }
  if (type === 'condition') return { ...base, conditions: [{ label: '默认', type: 'else' }] }
  return base
}

const addNodeAtCenter = (type) => {
  const id = `node-${++nodeCounter}-${Date.now()}`
  addNodes({ id, type, position: { x: 250 + Math.random() * 100, y: 150 + Math.random() * 100 }, data: createNodeData(type) })
  selectedNodeId.value = id
}

const onDragStart = (event, type) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', type)
    event.dataTransfer.effectAllowed = 'move'
  }
}

const onDrop = (event) => {
  event.preventDefault()
  const type = event.dataTransfer?.getData('application/vueflow')
  if (!type) return
  const position = screenToFlowCoordinate({ x: event.clientX, y: event.clientY })
  const id = `node-${++nodeCounter}-${Date.now()}`
  addNodes({ id, type, position, data: createNodeData(type) })
  selectedNodeId.value = id
}

const onNodeDragStop = ({ node }) => {
  selectedNodeId.value = node.id
}

const onEdgeClick = ({ edge }) => {
  if (confirm('删除这条连线？')) {
    edges.value = edges.value.filter(e => e.id !== edge.id)
  }
}

const deleteSelectedNode = () => {
  if (!selectedNode.value) return
  const id = selectedNode.value.id
  removeNodes([id])
  edges.value = edges.value.filter(e => e.source !== id && e.target !== id)
  selectedNodeId.value = null
}

const addCondition = () => {
  if (!selectedNode.value || selectedNode.value.type !== 'condition') return
  selectedNode.value.data.conditions.push({ label: `分支 ${selectedNode.value.data.conditions.length + 1}`, type: 'contains', value: '' })
}

const removeCondition = (index) => {
  if (!selectedNode.value || selectedNode.value.type !== 'condition') return
  selectedNode.value.data.conditions.splice(index, 1)
  const outEdges = edges.value.filter(e => e.source === selectedNode.value.id)
  if (outEdges[index]) {
    edges.value = edges.value.filter(e => e.id !== outEdges[index].id)
  }
}

const loadAgents = async () => {
  agents.value = await request.get('/api/agentsList')
}

const initDefaultGraph = () => {
  nodeCounter = 0
  nodes.value = [
    { id: `input-${++nodeCounter}`, type: 'input', position: { x: 0, y: 200 }, data: { label: '用户输入' } },
    { id: `output-${++nodeCounter}`, type: 'output', position: { x: 600, y: 200 }, data: { label: '最终输出' } },
  ]
  edges.value = [{ id: `edge-${++nodeCounter}`, source: 'input-1', target: 'output-1', type: 'smoothstep', animated: true }]
}

const loadWorkflow = async () => {
  if (!isEdit.value) {
    initDefaultGraph()
    return
  }
  const wf = await request.get(`/api/workflows/${route.params.id}`)
  form.name = wf.name
  form.description = wf.description || ''
  const config = wf.config || {}
  nodes.value = (config.nodes || []).map(n => ({ ...n, data: { ...n.data } }))
  const condNodes = {}
  for (const n of config.nodes || []) {
    if (n.type === 'condition') condNodes[n.id] = n.data?.conditions || []
  }
  edges.value = (config.edges || []).map(e => {
    const sh = e.source_handle ?? e.sourceHandle ?? null
    const th = e.target_handle ?? e.targetHandle ?? null
    let label = ''
    if (sh && sh.startsWith('cond-')) {
      const idx = parseInt(sh.replace('cond-', ''))
      const conds = condNodes[e.source] || []
      if (conds[idx]) label = conds[idx].label || ''
    }
    return { ...e, sourceHandle: sh, targetHandle: th, type: 'smoothstep', animated: true, label }
  })
  nodeCounter = nodes.value.length
}

const buildConfig = () => ({
  nodes: nodes.value.map(n => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
  edges: edges.value.map(e => ({ id: e.id, source: e.source, target: e.target, source_handle: e.sourceHandle || null, target_handle: e.targetHandle || null })),
})

const handleSubmit = async () => {
  await formRef.value.validate()
  const agentNodes = nodes.value.filter(n => n.type === 'agent')
  if (agentNodes.length === 0) {
    ElMessage.warning('至少需要一个 Agent 节点')
    return
  }
  for (const n of agentNodes) {
    if (!n.data.agent_id) {
      ElMessage.warning(`节点 "${n.data.label}" 未选择 Agent`)
      return
    }
  }

  saving.value = true
  try {
    const payload = { name: form.name.trim(), description: form.description || '', mode: 'dag', config: buildConfig() }
    if (isEdit.value) {
      await request.put(`/api/workflows/${route.params.id}`, payload)
      ElMessage.success('保存成功')
    } else {
      const wf = await request.post('/api/workflows', payload)
      ElMessage.success('创建成功')
      router.push(`/workflows/${wf.id}/run`)
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadAgents()
  await loadWorkflow()
})
</script>

<style scoped>
.workflow-form { max-width: 1400px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.wf-meta { background: #fff; padding: 16px; border-radius: 8px; margin-bottom: 16px; }
.wf-canvas-shell {
  display: grid;
  grid-template-columns: 180px 1fr 320px;
  gap: 12px;
  height: 600px;
  background: #fff;
  border-radius: 8px;
  padding: 12px;
}
.wf-palette {
  border-right: 1px solid #e5e7eb;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}
.palette-title { font-weight: 600; font-size: 14px; color: #1f2937; margin-bottom: 4px; }
.palette-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: grab;
  font-size: 13px;
  transition: all 0.15s;
}
.palette-item:hover { border-color: #409eff; background: #f0f7ff; }
.palette-hint { font-size: 12px; color: #9ca3af; }
.wf-canvas {
  position: relative;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  min-height: 560px;
}
.wf-config {
  border-left: 1px solid #e5e7eb;
  padding: 12px;
  overflow-y: auto;
}
.config-title { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.cond-row { margin-bottom: 12px; padding: 8px; background: #f8fafc; border-radius: 6px; }
.cond-label { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.cond-hint { font-size: 12px; color: #6b7280; line-height: 1.5; }
.opt-meta { color: #9ca3af; font-size: 12px; }
.wf-actions { margin-top: 16px; display: flex; gap: 12px; }
</style>

<style>
/* Vue Flow 节点样式（全局） */
.vf-node {
  background: #fff;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 14px;
  min-width: 140px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.vf-node.input-node, .vf-node.output-node {
  background: #f0fdf4;
  border-color: #86efac;
}
.vf-node.agent-node {
  background: #eff6ff;
  border-color: #93c5fd;
}
.vf-node.condition-node {
  background: #fef3c7;
  border-color: #fcd34d;
}
.vf-node.parallel-node {
  background: #f5f3ff;
  border-color: #c4b5fd;
}
.node-header {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
}
.node-icon { font-size: 20px; margin-bottom: 4px; color: #6b7280; }
.node-label { font-size: 14px; font-weight: 600; color: #1f2937; }
.node-desc { font-size: 12px; color: #6b7280; margin-top: 2px; }
.node-branches { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.branch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: #fff;
  border-radius: 4px;
  font-size: 12px;
  position: relative;
}
.branch-label { font-weight: 500; color: #92400e; }
.branch-handle {
  width: 10px !important;
  height: 10px !important;
  background: #f59e0b !important;
  border: 2px solid #fff !important;
}
.vue-flow__node { cursor: pointer; }
.vue-flow__node.selected .vf-node {
  box-shadow: 0 0 0 2px #409eff, 0 8px 20px rgba(64,158,255,0.2);
}
.vue-flow__edge-path { stroke-width: 2; }
.vue-flow__edge.animated .vue-flow__edge-path { stroke-dasharray: 6; animation: dashmove 0.5s linear infinite; }
@keyframes dashmove { to { stroke-dashoffset: -6; } }
.vue-flow__edge-textwrapper {
  font-size: 11px;
  font-weight: 600;
}
.vue-flow__edge-text {
  font-size: 11px;
  font-weight: 600;
  fill: #92400e;
  background: #fef3c7;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
