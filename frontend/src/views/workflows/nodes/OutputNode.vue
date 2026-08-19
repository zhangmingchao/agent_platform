<template>
  <div class="vf-node output-node">
    <Handle type="target" :position="Position.Left" />
    <div class="node-icon"><el-icon><Download /></el-icon></div>
    <div class="node-label">{{ data.label || '输出' }}</div>
    <div class="node-desc">最终结果</div>
  </div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { Download } from '@element-plus/icons-vue'
defineProps({ data: { type: Object, default: () => ({}) } })
</script>
