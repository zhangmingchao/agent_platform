<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #409EFF">
            <el-icon :size="28">
              <User/>
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.agents }}</div>
            <div class="stat-label">{{ t('dashboard.agentTotal') }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #7c3aed">
            <el-icon :size="28">
              <UserFilled/>
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.crews }}</div>
            <div class="stat-label">{{ t('dashboard.crewTotal') }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #0ea5e9">
            <el-icon :size="28">
              <Operation/>
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.flows }}</div>
            <div class="stat-label">{{ t('dashboard.flowTotal') }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #67C23A">
            <el-icon :size="28">
              <Document/>
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.skills }}</div>
            <div class="stat-label">{{ t('dashboard.skillTotal') }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #E6A23C">
            <el-icon :size="28">
              <Connection/>
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.mcps }}</div>
            <div class="stat-label">{{ t('dashboard.mcpTotal') }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #F56C6C">
            <el-icon :size="28">
              <ChatDotRound/>
            </el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.sessions }}</div>
            <div class="stat-label">{{ t('dashboard.sessionTotal') }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.recentCrews') }}</span>
              <el-button type="primary" link @click="$router.push('/crews')">{{ t('dashboard.viewAll') }}</el-button>
            </div>
          </template>
          <el-table :data="recentCrews" :empty-text="t('dashboard.noCrews')">
            <el-table-column prop="name" :label="t('dashboard.name')"/>
            <el-table-column prop="description" :label="t('dashboard.description')" show-overflow-tooltip/>
            <el-table-column prop="process" :label="t('dashboard.process')" width="140"/>
            <el-table-column :label="t('dashboard.actions')" width="160">
              <template #default="{ row }">
                <el-button type="primary" link @click="$router.push(`/crews/${row.id}/chat`)">{{
                    t('dashboard.chat')
                  }}
                </el-button>
                <el-button link @click="$router.push(`/crews/${row.id}/edit`)">{{ t('dashboard.edit') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.recentSessions') }}</span>
            </div>
          </template>
          <el-table :data="recentSessions" :empty-text="t('dashboard.noSessions')">
            <el-table-column prop="title" :label="t('dashboard.title')" show-overflow-tooltip/>
            <el-table-column prop="updated_at" :label="t('dashboard.updatedAt')" width="180">
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
import {ref, onMounted} from 'vue'
import request from '../utils/request'
import {useI18n} from 'vue-i18n'

// t 用于通过语言包 key 获取当前语言的文案。
const {t, locale} = useI18n()

// ref 创建响应式数据：修改 .value 后，模板会自动重新渲染。
const stats = ref({agents: 0, crews: 0, flows: 0, skills: 0, mcps: 0, sessions: 0})
const recentCrews = ref([])
const recentSessions = ref([])

// 将后端返回的时间字符串格式化成适合页面展示的本地时间。
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString(locale.value)
}

// 页面首次显示后，同时加载仪表盘需要的四类数据。
onMounted(async () => {
  try {
    const [agents, crews, flows, skills, mcps, sessions] = await Promise.all([
      request.get('/api/agentsList'),
      request.get('/api/crews'),
      request.get('/api/flows'),
      request.get('/api/skills'),
      request.get('/api/mcp-configs'),
      request.get('/api/sessions')
    ])
    // 仪表盘只展示数量，因此从每个列表的 length 计算统计值。
    stats.value = {
      agents: agents.length,
      crews: crews.length,
      flows: flows.length,
      skills: skills.length,
      mcps: mcps.length,
      sessions: sessions.length
    }
    // 接口已按时间排序，这里取前 5 条作为“最近”数据。
    recentCrews.value = crews.slice(0, 5)
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
