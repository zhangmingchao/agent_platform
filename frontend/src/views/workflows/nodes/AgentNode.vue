<template>
  <div class="vf-node agent-node">
    <Handle type="target" :position="Position.Left" />
    <Handle type="source" :position="Position.Right" />
    <div class="node-header">
      <el-icon><User /></el-icon>
      <span>AGENT</span>
    </div>
    <div class="node-label">{{ data.role || data.label || '未命名' }}</div>
    <div class="node-desc">{{ data.agent_name || '未选择 Agent' }}</div>
  </div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { User } from '@element-plus/icons-vue'
defineProps({ data: { type: Object, default: () => ({}) } })
</script>
