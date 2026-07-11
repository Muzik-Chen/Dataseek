<template>
  <AdminCrud :config="config" />
</template>

<script setup>
import AdminCrud from '@/components/admin/AdminCrud.vue'

const config = {
  resource: 'events',
  title: '节日/活动管理',
  columns: [
    { prop: 'id', label: 'ID', width: 60 },
    { prop: 'name', label: '名称', minWidth: 140 },
    { prop: 'event_type', label: '类型', width: 80, type: 'tag', valueMap: { festival: '节日', event: '活动', custom: '民俗' } },
    { prop: 'event_date', label: '日期', width: 110 },
    { prop: 'lunar_date', label: '农历', width: 100 },
    { prop: 'region', label: '地区', width: 100 },
    { prop: 'created_at', label: '创建时间', type: 'datetime', width: 160 },
  ],
  searchFields: ['name', 'description'],
  filters: {
    event_type: { label: '类型', options: [{ label: '节日', value: 'festival' }, { label: '活动', value: 'event' }, { label: '民俗', value: 'custom' }] },
  },
  formFields: [
    { prop: 'name', label: '名称', type: 'text', required: true },
    { prop: 'event_type', label: '类型', type: 'select', options: [{ label: '节日', value: 'festival' }, { label: '活动', value: 'event' }, { label: '民俗', value: 'custom' }], required: true },
    { prop: 'event_date', label: '公历日期', type: 'date', required: true },
    { prop: 'lunar_date', label: '农历备注', type: 'text', placeholder: '如：正月十五' },
    { prop: 'region', label: '地区', type: 'text', required: true },
    { prop: 'description', label: '描述', type: 'textarea' },
  ],
  actions: ['create', 'edit', 'delete'],
}
</script>
