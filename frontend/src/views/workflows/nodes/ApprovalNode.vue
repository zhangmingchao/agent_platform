<template>
  <div class="vf-node approval-node">
    <Handle type="target" :position="Position.Left" />
    <Handle type="source" :position="Position.Right" />
    <div class="node-header"><el-icon><CircleCheck /></el-icon><span>人工确认</span></div>
    <div class="node-label">{{ data.label || '人工确认' }}</div>
    <div class="node-desc">暂停并等待用户审批</div>
  </div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { CircleCheck } from '@element-plus/icons-vue'
defineProps({ data: { type: Object, default: () => ({}) } })
</script>
