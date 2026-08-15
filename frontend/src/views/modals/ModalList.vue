<template>
  <div>
    <div class="page-header"><h2>模型 管理</h2>
      <el-button type="primary" @click="$router.push('/modals/new')">
        <el-icon>
          <Plus/>
        </el-icon>
        创建 模型
      </el-button>
    </div>
    <el-alert title="模型管理" type="info" :closable="false"
              show-icon style="margin-bottom:16px"/>
    <el-table :data="modals" v-loading="loading" stripe>
      <el-table-column prop="name" label="名称" width="160"/>
      <el-table-column prop="model" label="模型" width="180"/>
      <el-table-column prop="baseUrl" label="base_url" width="180"/>
      <el-table-column prop="apiKey" label="api_key" width="180"/>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/modals/${row.id}/edit`)">编辑</el-button>
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

const modals = ref([])
const loading = ref(false)
const load = async () => {
  loading.value = true;
  try {
    modals.value = [
      {
        "id":1,
        "name":"deepseek-1",
        "model":"deepseek-1",
        "enabled":true,
        "baseUrl":"https://api.deepseek.com",
        "apiKey":"11sdfasdfasdfasdfasdfasdfsdfsadf"
      },
      {
        "id":2,
        "name":"deepseek-2",
        "model":"deepseek-2",
        "enabled":false,
        "baseUrl":"https://api.deepseek.com",
        "apiKey":"11sdfasdfasdfasdfasdfasdfsdfsadf"
      }
    ]
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
