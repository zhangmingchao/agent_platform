<template>
  <el-form label-position="top" class="bi-debug-form">
    <el-form-item label="查询对象"><el-select v-model="command" aria-label="查询对象"><el-option v-for="item in commands" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
    <el-form-item label="产品标识" required><el-input v-model="productKey" aria-label="调试产品标识" placeholder="product-key" /></el-form-item>
    <template v-if="paginated"><el-form-item label="页码"><el-input-number v-model="pageNum" :min="1" :max="100000" /></el-form-item><el-form-item label="每页条数"><el-input-number v-model="pageSize" :min="1" :max="200" /></el-form-item></template>
    <el-form-item v-if="paginated" label="搜索词"><el-input v-model="searchText" clearable /></el-form-item>
    <el-form-item v-if="command === 'user-properties'" label="分析主体"><el-input v-model="entityType" placeholder="users" /></el-form-item>
  </el-form>
  <pre>{{ JSON.stringify(argumentsArray) }}</pre>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
// BI 特有命令留在专用面板，通用插件页面只处理工具输入对象。
const emit = defineEmits(['update:modelValue'])
defineProps({ modelValue: { type: Object, default: () => ({}) } })
const command = ref('events')
const productKey = ref('')
const pageNum = ref(1)
const pageSize = ref(50)
const searchText = ref('')
const entityType = ref('users')
const commands = [{ value: 'events', label: '事件' }, { value: 'user-properties', label: '用户属性' }, { value: 'event-properties', label: '事件属性' }, { value: 'analysis-bodies', label: '分析主体' }, { value: 'metrics', label: '指标' }]
const paginated = computed(() => ['events', 'event-properties', 'metrics'].includes(command.value))
const argumentsArray = computed(() => {
  const args = ['metadata', command.value, 'list', '--product-key', productKey.value.trim()]
  if (paginated.value) args.push('--page-num', String(pageNum.value), '--page-size', String(pageSize.value))
  if (paginated.value && searchText.value.trim()) args.push('--search-text', searchText.value.trim())
  if (command.value === 'user-properties') args.push('--entity-type', entityType.value.trim() || 'users')
  return args
})
watch(argumentsArray, argumentsValue => emit('update:modelValue', { arguments: argumentsValue }), { immediate: true })
</script>

<style scoped>
.bi-debug-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 20px; }
.bi-debug-form .el-input-number, .bi-debug-form .el-select { width: 100%; }
pre { padding: 16px; background: #f5f6f8; border: 1px solid #e6e9ef; border-radius: 6px; font: 12px/1.7 ui-monospace, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 760px) { .bi-debug-form { grid-template-columns: minmax(0, 1fr); } }
</style>
