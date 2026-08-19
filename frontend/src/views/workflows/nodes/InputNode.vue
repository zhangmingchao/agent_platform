<template>
  <div class="vf-node input-node">
    <Handle type="source" :position="Position.Right" />
    <div class="node-icon"><el-icon><Promotion /></el-icon></div>
    <div class="node-label">{{ data.label || '输入' }}</div>
    <div class="node-desc">接收用户输入</div>
  </div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { Promotion } from '@element-plus/icons-vue'
defineProps({ data: { type: Object, default: () => ({}) } })
</script>
