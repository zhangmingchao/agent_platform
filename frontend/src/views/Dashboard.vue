<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #409EFF"><el-icon :size="28"><User /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.agents }}</div>
            <div class="stat-label">Agent 总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #67C23A"><el-icon :size="28"><Document /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.skills }}</div>
            <div class="stat-label">Skill 总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #E6A23C"><el-icon :size="28"><Connection /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.mcps }}</div>
            <div class="stat-label">MCP 配置</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #F56C6C"><el-icon :size="28"><ChatDotRound /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.sessions }}</div>
            <div class="stat-label">会话总数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近 Agent</span>
              <el-button type="primary" link @click="$router.push('/agents')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentAgents" empty-text="暂无 Agent">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column prop="model" label="模型" width="140" />
            <el-table-column label="操作" width="160">
              <template #default="{ row }">
                <el-button type="primary" link @click="$router.push(`/agents/${row.id}/chat`)">对话</el-button>
                <el-button link @click="$router.push(`/agents/${row.id}/edit`)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近会话</span>
            </div>
          </template>
          <el-table :data="recentSessions" empty-text="暂无会话">
            <el-table-column prop="title" label="标题" show-overflow-tooltip />
            <el-table-column prop="updated_at" label="更新时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.updated_at) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../utils/request'

const stats = ref({ agents: 0, skills: 0, mcps: 0, sessions: 0 })
const recentAgents = ref([])
const recentSessions = ref([])

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(async () => {
  try {
    const [agents, skills, mcps, sessions] = await Promise.all([
      request.get('/api/agents'),
      request.get('/api/skills'),
      request.get('/api/mcp-configs'),
      request.get('/api/sessions')
    ])
    stats.value = {
      agents: agents.length,
      skills: skills.length,
      mcps: mcps.length,
      sessions: sessions.length
    }
    recentAgents.value = agents.slice(0, 5)
    recentSessions.value = sessions.slice(0, 5)
  } catch (e) {
    // handled by interceptor
  }
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  border: none;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
}
.stat-label {
  color: #9ca3af;
  font-size: 13px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
</style>