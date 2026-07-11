<template>
  <div v-if="total > pageSize" class="pagination-wrap">
    <el-pagination
      v-model:current-page="current"
      :page-size="pageSize"
      :total="total"
      :layout="layout"
      background
      @current-change="$emit('change', $event)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total:      { type: Number, default: 0 },
  page:       { type: Number, default: 1 },
  pageSize:   { type: Number, default: 20 },
  layout:     { type: String, default: 'prev, pager, next' },
})

const emit = defineEmits(['update:page', 'change'])

const current = computed({
  get: () => props.page,
  set: (v) => {
    emit('update:page', v)
    emit('change', v)
  },
})
</script>

<style scoped>
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}
</style>
