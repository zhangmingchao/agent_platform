<template>
  <div class="skill-list">
    <div class="page-header">
      <h2>Skill 管理</h2>
      <div>
        <el-button type="primary" @click="openUploadDialog">
          <el-icon><Upload /></el-icon>
          上传 Skill
        </el-button>
        <el-button @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          手动创建
        </el-button>
      </div>
    </div>

    <el-table :data="skills" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" width="180" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="handleView(row)">查看</el-button>
          <el-button type="primary" size="small" @click="openFileEditor(row)">编辑文件</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showUploadDialog" title="创建 Skill" width="560px" :close-on-click-modal="false">
      <el-form :model="uploadSkill" label-width="90px">
        <el-form-item label="技能名称" required>
          <el-input v-model="uploadSkill.name" placeholder="例如：商业保险投保分析" />
        </el-form-item>
        <el-form-item label="技能描述" required>
          <el-input v-model="uploadSkill.description" type="textarea" :rows="3" placeholder="简述这个技能可以解决什么问题" />
        </el-form-item>
        <el-form-item label="技能压缩包" required>
          <el-upload
            :auto-upload="false"
            :limit="1"
            accept=".zip"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-button>选择 ZIP 文件</el-button>
            <template #tip>
              <div class="el-upload__tip">仅支持 ZIP，压缩包中必须包含 SKILL.md。</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">创建</el-button>
      </template>
    </el-dialog>

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

    <el-dialog v-model="showFileEditor" :title="`编辑 Skill 文件 - ${editingSkill?.name || ''}`" width="900px" :close-on-click-modal="false">
      <div class="file-editor">
        <aside class="file-list" v-loading="filesLoading">
          <div v-if="skillFiles.length === 0" class="empty-files">该 Skill 没有可编辑的解压文件。</div>
          <el-button
            v-for="file in skillFiles"
            :key="file.path"
            text
            :class="['file-item', { active: selectedFilePath === file.path }]"
            @click="selectSkillFile(file.path)"
          >
            {{ file.path }}
          </el-button>
        </aside>
        <section class="file-content">
          <div v-if="selectedFilePath" class="file-toolbar">
            <span>{{ selectedFilePath }}</span>
            <el-button type="primary" size="small" :loading="fileSaving" @click="saveSkillFile">保存</el-button>
          </div>
          <el-input
            v-if="selectedFilePath"
            v-model="editingFileContent"
            type="textarea"
            class="file-textarea"
            :autosize="{ minRows: 20, maxRows: 26 }"
            :loading="fileLoading"
          />
          <div v-else class="empty-files">请从左侧选择要编辑的文件。</div>
        </section>
      </div>
      <template #footer>
        <el-button @click="showFileEditor = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../../utils/request'

// 列表、弹窗开关和当前查看的 Skill 都是页面响应式状态。
const skills = ref([])
const loading = ref(false)
const showUploadDialog = ref(false)
const uploading = ref(false)
const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const showFileEditor = ref(false)
const currentSkill = ref(null)
const editingSkill = ref(null)
const skillFiles = ref([])
const selectedFilePath = ref('')
const editingFileContent = ref('')
const filesLoading = ref(false)
const fileLoading = ref(false)
const fileSaving = ref(false)

// 新建弹窗的表单模型。
const newSkill = reactive({ name: '', description: '', content: '' })
const uploadSkill = reactive({ name: '', description: '', file: null })

const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const loadSkills = async () => {
  loading.value = true
  try {
    skills.value = await request.get('/api/skills')
  } finally {
    loading.value = false
  }
}

const openUploadDialog = () => {
  uploadSkill.name = ''
  uploadSkill.description = ''
  uploadSkill.file = null
  showUploadDialog.value = true
}

const handleFileChange = (file) => {
  // Element Plus 传入 UploadFile，其 raw 属性才是真正的浏览器 File 对象。
  uploadSkill.file = file.raw
}

const handleFileRemove = () => {
  uploadSkill.file = null
}

const handleUpload = async () => {
  if (!uploadSkill.name.trim() || !uploadSkill.description.trim() || !uploadSkill.file) {
    ElMessage.warning('请填写技能名称、描述并选择 ZIP 文件')
    return
  }

  // 文件上传必须使用 FormData，与后端 Form + File 参数对应。
  const formData = new FormData()
  formData.append('name', uploadSkill.name.trim())
  formData.append('description', uploadSkill.description.trim())
  formData.append('file', uploadSkill.file)
  uploading.value = true
  try {
    await request.post('/api/skills/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    ElMessage.success('创建成功')
    showUploadDialog.value = false
    await loadSkills()
  } catch (e) { /* request 拦截器统一提示错误 */ } finally {
    uploading.value = false
  }
}

const handleCreate = async () => {
  // 创建后关闭弹窗、清空表单并刷新列表。
  await request.post('/api/skills', newSkill)
  ElMessage.success('创建成功')
  showCreateDialog.value = false
  newSkill.name = ''
  newSkill.description = ''
  newSkill.content = ''
  loadSkills()
}

const handleView = (row) => {
  // 将被点击行保存起来，供“查看内容”弹窗展示。
  currentSkill.value = row
  showViewDialog.value = true
}

const openFileEditor = async (row) => {
  editingSkill.value = row
  skillFiles.value = []
  selectedFilePath.value = ''
  editingFileContent.value = ''
  showFileEditor.value = true
  filesLoading.value = true
  try {
    skillFiles.value = await request.get(`/api/skills/${row.id}/files`)
    // 优先打开 SKILL.md，让用户直接编辑 Agent 的核心指令。
    const skillFile = skillFiles.value.find(file => file.path.toLowerCase().endsWith('skill.md'))
    if (skillFile) await selectSkillFile(skillFile.path)
  } catch (e) { /* request 拦截器统一提示错误 */ } finally {
    filesLoading.value = false
  }
}

const selectSkillFile = async (filePath) => {
  if (!editingSkill.value || fileLoading.value) return
  selectedFilePath.value = filePath
  fileLoading.value = true
  try {
    const file = await request.get(`/api/skills/${editingSkill.value.id}/files/${filePath}`)
    editingFileContent.value = file.content
  } catch (e) { /* request 拦截器统一提示错误 */ } finally {
    fileLoading.value = false
  }
}

const saveSkillFile = async () => {
  if (!editingSkill.value || !selectedFilePath.value) return
  fileSaving.value = true
  try {
    await request.put(`/api/skills/${editingSkill.value.id}/files/${selectedFilePath.value}`, {
      content: editingFileContent.value
    })
    ElMessage.success('文件已保存')
    // 编辑 SKILL.md 时，同步更新列表中存的内容。
    if (selectedFilePath.value.toLowerCase().endsWith('skill.md')) await loadSkills()
  } catch (e) { /* request 拦截器统一提示错误 */ } finally {
    fileSaving.value = false
  }
}

const handleDelete = async (row) => {
  // 删除操作使用确认框，并在成功后重新获取数据。
  await ElMessageBox.confirm(`确定删除 Skill "${row.name}" 吗？`, '确认删除', { type: 'warning' })
  await request.delete(`/api/skills/${row.id}`)
  ElMessage.success('删除成功')
  loadSkills()
}

// 页面首次挂载时获取 Skill 列表。
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
.file-editor {
  display: flex;
  min-height: 480px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}
.file-list {
  width: 240px;
  padding: 8px;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
}
.file-item {
  display: block;
  width: 100%;
  height: auto;
  padding: 8px;
  text-align: left;
  white-space: normal;
  word-break: break-all;
}
.file-item.active {
  background: #ecf5ff;
  color: #409eff;
}
.file-content {
  flex: 1;
  min-width: 0;
  padding: 12px;
}
.file-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  color: #606266;
  font-size: 13px;
}
.file-textarea :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  line-height: 1.6;
}
.empty-files {
  padding: 20px;
  color: #909399;
  text-align: center;
}
</style>
