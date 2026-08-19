<template>
  <div class="vf-node parallel-node">
    <Handle type="target" :position="Position.Left" />
    <div class="node-header">
      <el-icon><Share /></el-icon>
      <span>并行执行</span>
    </div>
    <div class="node-label">{{ data.label || '并行' }}</div>
    <div class="node-desc">同时执行所有下游节点</div>
    <Handle type="source" :position="Position.Right" id="out" />
  </div>
</template>
<script setup>
import { Handle, Position } from '@vue-flow/core'
import { Share } from '@element-plus/icons-vue'
defineProps({ data: { type: Object, default: () => ({}) } })
</script>
