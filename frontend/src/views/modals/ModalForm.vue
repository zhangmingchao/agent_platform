<template>
  <div>
    <div class="page-header">
      <h2>{{ isEdit ? '编辑 Modal' : '创建 Modal' }}</h2>
      <el-button @click="router.push('/modals')">返回</el-button>
    </div>
    <el-form ref="formRef" :model="form" label-width="130px" class="config-form">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name"/>
      </el-form-item>
      <el-form-item label="模型">
        <el-input v-model="form.modal" />
      </el-form-item>
      <el-form-item label="base url">
        <el-input v-model="form.baseUrl" />
      </el-form-item>
      <el-form-item label="API KEY">
        <el-input v-model="form.apiKey" />
      </el-form-item>
      <el-form-item class="actions">
        <el-button type="primary"  @click="submit">{{ isEdit ? '保存' : '创建' }}</el-button>
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
const formRef = ref()
const form = reactive({
  "name":""
})
const isEdit = computed(() => Boolean(route.params.id))




onMounted(async () => {
  if (isEdit.value) {
    form.name = 'deepseek'
    form.modal = 'deepseek'
  }
})

const submit = async () => {
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
