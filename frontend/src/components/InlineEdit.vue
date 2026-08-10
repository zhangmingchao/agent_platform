<template>
  <div class="inline-edit" :class="{ editing }">
    <template v-if="editing">
      <el-input
        ref="inputRef"
        v-model="draft"
        :maxlength="maxlength"
        :placeholder="placeholder"
        size="small"
        @blur="commit"
        @keydown.enter.prevent="commit"
        @keydown.esc.prevent="cancel"
      />
    </template>
    <template v-else>
      <span class="inline-edit-text" :class="{ placeholder: !displayValue }" :title="displayValue">
        {{ displayValue || placeholder }}
      </span>
      <el-tooltip content="编辑" placement="top" :show-after="300">
        <el-button
          class="inline-edit-button"
          type="primary"
          link
          circle
          size="small"
          aria-label="编辑"
          @click.stop="startEdit"
        >
          <el-icon><Edit /></el-icon>
        </el-button>
      </el-tooltip>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '暂无内容' },
  maxlength: { type: Number, default: 500 }
})
const emit = defineEmits(['save'])

const editing = ref(false)
const draft = ref('')
const inputRef = ref(null)
const displayValue = computed(() => props.modelValue || '')

const startEdit = async () => {
  draft.value = props.modelValue || ''
  editing.value = true
  await nextTick()
  inputRef.value?.focus()
  inputRef.value?.select()
}

const commit = () => {
  if (!editing.value) return
  editing.value = false
  emit('save', draft.value.trim())
}

const cancel = () => {
  editing.value = false
}
</script>

<style scoped>
.inline-edit {
  display: flex;
  align-items: center;
  min-width: 0;
  min-height: 28px;
  gap: 6px;
}
.inline-edit.editing {
  width: 100%;
}
.inline-edit-text {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.inline-edit-text.placeholder {
  color: #a8abb2;
}
.inline-edit-button {
  flex-shrink: 0;
  margin: 0;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.16s;
}
.inline-edit:hover .inline-edit-button,
.inline-edit-button:focus {
  opacity: 1;
  pointer-events: auto;
}
</style>
