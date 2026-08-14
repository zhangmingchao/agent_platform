<template>
  <div>
    <div class="page-header"><h2>Agent 管理</h2>
      <el-button type="primary" @click="$router.push('/agents/new')">
        <el-icon>
          <Plus/>
        </el-icon>
        创建 Agent
      </el-button>
    </div>
    <el-alert title="Agent 是可复用的专业成员；请在 Crew 中组合 Agent 和 Task 后开始执行。" type="info" :closable="false"
              show-icon style="margin-bottom:16px"/>
    <el-table :data="agents" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" width="180"/>
      <el-table-column prop="role" label="Role" width="200" show-overflow-tooltip/>
      <el-table-column prop="goal" label="Goal" min-width="260" show-overflow-tooltip/>
      <el-table-column prop="model" label="模型" width="160"/>
      <el-table-column label="能力" width="210">
        <template #default="{ row }">
          <el-tag v-if="row.reasoning" size="small">Reasoning</el-tag>
          <el-tag v-if="row.planning" size="small" type="success">Planning</el-tag>
          <el-tag v-if="row.memory" size="small" type="warning">Memory</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/agents/${row.id}/edit`)">编辑</el-button>
          <el-button type="danger" size="small" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import request from '../../utils/request'

const agents = ref([])
const loading = ref(false)
const load = async () => {
  loading.value = true;
  try {
    agents.value = await request.get('/api/agentsList')
  } finally {
    loading.value = false
  }
}
const remove = async row => {
  await ElMessageBox.confirm(`确定删除 Agent“${row.name}”吗？`, '确认删除', {type: 'warning'});
  await request.delete(`/api/agents/${row.id}`);
  ElMessage.success('已删除');
  load()
}
onMounted(load)
</script>
