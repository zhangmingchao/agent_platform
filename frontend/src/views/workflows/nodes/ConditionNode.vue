<template>
  <div class="vf-node condition-node">
    <Handle type="target" :position="Position.Left" />
    <div class="node-header">
      <el-icon><Switch /></el-icon>
      <span>条件判断</span>
    </div>
    <div class="node-label">{{ data.label || '条件分支' }}</div>
    <div class="node-branches">
      <div v-for="(cond, i) in (data.conditions && data.conditions.length ? data.conditions : [{label: '默认'}])" :key="i" class="branch-item">
        <span class="branch-label">{{ cond.label || `分支 ${i+1}` }}</span>
        <Handle type="source" :position="Position.Right" :id="`cond-${i}`" class="branch-handle" />
      </div>
    </div>
  </div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { Switch } from '@element-plus/icons-vue'
defineProps({ data: { type: Object, default: () => ({}) } })
</script>
