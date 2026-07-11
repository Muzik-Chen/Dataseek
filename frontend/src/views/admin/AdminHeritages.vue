<template>
  <AdminCrud :config="config" />
</template>

<script setup>
import AdminCrud from '@/components/admin/AdminCrud.vue'

const config = {
  resource: 'heritages',
  title: '非遗管理',
  columns: [
    { prop: 'id', label: 'ID', width: 60 },
    { prop: 'name', label: '名称', minWidth: 140 },
    { prop: 'category', label: '级别', width: 80, type: 'tag', tagMap: { '国家级': 'danger', '省级': 'warning', '市级': 'success' } },
    { prop: 'type', label: '类型', width: 100 },
    { prop: 'region', label: '地区', width: 80 },
    { prop: 'view_count', label: '浏览', width: 70 },
    { prop: 'created_at', label: '创建时间', type: 'datetime', width: 160 },
  ],
  searchFields: ['name', 'description'],
  formFields: [
    { prop: 'name', label: '名称', type: 'text', required: true },
    { prop: 'category', label: '级别', type: 'select', options: [{ label: '国家级', value: '国家级' }, { label: '省级', value: '省级' }, { label: '市级', value: '市级' }], required: true },
    { prop: 'type', label: '类型', type: 'select', options: [
      { label: '传统戏剧', value: '传统戏剧' }, { label: '传统技艺', value: '传统技艺' },
      { label: '民俗', value: '民俗' }, { label: '传统舞蹈', value: '传统舞蹈' }, { label: '传统美术', value: '传统美术' },
    ], required: true },
    { prop: 'region', label: '地区', type: 'text', required: true },
    { prop: 'inheritor', label: '传承人', type: 'text' },
    { prop: 'description', label: '描述', type: 'textarea' },
    { prop: 'image_url', label: '图片', type: 'image' },
  ],
  actions: ['create', 'edit', 'delete'],
}
</script>
