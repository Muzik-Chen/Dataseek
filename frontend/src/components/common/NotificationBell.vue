<template>
  <el-badge :value="count" :hidden="count <= 0" :max="99" class="notification-bell">
    <el-button :icon="Bell" circle :size="size" class="bell-btn" @click="$emit('click')" />
  </el-badge>
</template>

<script setup>
import { Bell } from '@element-plus/icons-vue'

defineProps({
  count: { type: Number, default: 0 },
  size: { type: String, default: 'default' },
})

defineEmits(['click'])
</script>

<style scoped>
.notification-bell {
  display: inline-flex;
}
.bell-btn {
  border: none;
  background: transparent;
  color: var(--ink, #2C3E50);
  transition: color 0.2s;
}
.bell-btn:hover {
  color: var(--primary, #C0392B);
}
</style>
