<template>
  <el-form label-position="top" :disabled="disabled" class="plugin-fields">
    <el-form-item v-for="field in fields" :key="field.key" :label="field.label" :required="field.required">
      <el-input-number v-if="field.kind === 'integer'" v-model="model.values[field.key]" :min="field.minimum ?? undefined" :max="field.maximum ?? undefined" controls-position="right" />
      <el-switch v-else-if="field.kind === 'boolean'" v-model="model.values[field.key]" :aria-label="field.label" />
      <el-select v-else-if="field.kind === 'select'" v-model="model.values[field.key]" :placeholder="field.placeholder || '请选择'" :aria-label="field.label" clearable>
        <el-option v-for="option in field.options" :key="option.value" :label="option.label" :value="option.value" />
      </el-select>
      <template v-else-if="field.kind === 'secret'">
        <el-input v-model="model.secrets[field.key]" type="password" autocomplete="new-password" :maxlength="field.max_length"
          :aria-label="field.label" :disabled="model.clear_secrets.includes(field.key)"
          :placeholder="configuredSecrets.includes(field.key) ? '已保存，留空保留原值' : (field.placeholder || `输入${field.label}`)" />
        <el-checkbox v-if="configuredSecrets.includes(field.key)" v-model="model.clear_secrets" :value="field.key" @change="() => clearSecret(field.key)">清除已保存的{{ field.label }}</el-checkbox>
      </template>
      <el-input v-else v-model="model.values[field.key]" :placeholder="field.placeholder" :maxlength="field.max_length" :aria-label="field.label" autocomplete="off" />
    </el-form-item>
  </el-form>
</template>

<script setup>
// 配置和检测参数共用声明式控件，每个密钥都有独立的保留与清除状态。
const props = defineProps({
  fields: { type: Array, required: true },
  model: { type: Object, required: true },
  configuredSecrets: { type: Array, default: () => [] },
  disabled: Boolean
})
const clearSecret = key => {
  if (props.model.clear_secrets.includes(key)) props.model.secrets[key] = ''
}
</script>

<style scoped>
.plugin-fields { max-width: 600px; }
.plugin-fields .el-input-number { width: 220px; max-width: 100%; }
.plugin-fields .el-checkbox { margin-top: 4px; white-space: normal; height: auto; min-height: 32px; }
</style>
