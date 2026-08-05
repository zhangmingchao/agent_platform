<template>
  <div class="skill-list">
    <div class="page-header">
      <h2>Skill 管理</h2>
      <div>
        <el-upload :auto-upload="false" :on-change="handleUpload" accept=".md,.txt">
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            上传 SKILL.md
          </el-button>
        </el-upload>
        <el-button @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          手动创建
        </el-button>
      </div>
    </div>

    <el-table :data="skills" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="内容预览" width="200">
        <template #default="{ row }">{{ row.content?.substring(0, 80) }}...</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handleView(row)">查看</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreateDialog" title="创建 Skill" width="600px">
      <el-form :model="newSkill" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="newSkill.name" placeholder="skill 名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newSkill.description" placeholder="skill 描述" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="newSkill.content" type="textarea" :rows="10" placeholder="SKILL.md 内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showViewDialog" title="Skill 详情" width="700px">
      <pre class="skill-content">{{ currentSkill?.content }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

const skills = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const currentSkill = ref(null)

const newSkill = reactive({ name: '', description: '', content: '' })

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const loadSkills = async () => {
  loading.value = true
  try {
    skills.value = await request.get('/api/skills')
  } finally {
    loading.value = false
  }
}

const handleUpload = async (file) => {
  const formData = new FormData()
  formData.append('file', file.raw)
  try {
    await request.post('/api/skills/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('上传成功')
    loadSkills()
  } catch (e) { /* handled */ }
}

const handleCreate = async () => {
  await request.post('/api/skills', newSkill)
  ElMessage.success('创建成功')
  showCreateDialog.value = false
  newSkill.name = ''
  newSkill.description = ''
  newSkill.content = ''
  loadSkills()
}

const handleView = (row) => {
  currentSkill.value = row
  showViewDialog.value = true
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除 Skill "${row.name}" 吗？`, '确认删除', { type: 'warning' })
  await request.delete(`/api/skills/${row.id}`)
  ElMessage.success('删除成功')
  loadSkills()
}

onMounted(loadSkills)
</script>

<style scoped>
.skill-content {
  max-height: 400px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  white-space: pre-wrap;
  font-size: 13px;
}
</style>