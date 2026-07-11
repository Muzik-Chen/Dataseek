<template>
  <el-select
    :model-value="modelValue"
    :style="{ width: width }"
    @update:model-value="$emit('update:modelValue', $event)"
    @change="$emit('change', $event)"
  >
    <el-option
      v-for="opt in options"
      :key="opt.value"
      :label="opt.label"
      :value="opt.value"
    />
  </el-select>
</template>

<script setup>
defineProps({
  modelValue: { type: String, default: 'view_count' },
  options: {
    type: Array,
    default: () => [
      { label: '🔥 最热门', value: 'view_count' },
      { label: '🕐 最新',   value: 'created_at' },
    ],
  },
  width: { type: String, default: '130px' },
})

defineEmits(['update:modelValue', 'change'])
</script>
