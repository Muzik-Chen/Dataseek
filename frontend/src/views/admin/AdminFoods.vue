<template>
  <AdminCrud :config="config" />
</template>

<script setup>
import AdminCrud from '@/components/admin/AdminCrud.vue'

const config = {
  resource: 'foods',
  title: '美食管理',
  columns: [
    { prop: 'id', label: 'ID', width: 60 },
    { prop: 'name', label: '名称', minWidth: 140 },
    { prop: 'type', label: '类型', width: 80, type: 'tag', tagMap: { dish: 'success', shop: 'warning' }, valueMap: { dish: '菜品', shop: '店铺' } },
    { prop: 'category_id', label: '分类', width: 80, valueMap: { 1: '粿品', 2: '海鲜', 3: '小吃' } },
    { prop: 'price_range', label: '价格', width: 70 },
    { prop: 'view_count', label: '浏览', width: 70 },
    { prop: 'is_recommended', label: '推荐', width: 70, type: 'switch' },
    { prop: 'created_at', label: '创建时间', width: 160, type: 'datetime' },
  ],
  searchFields: ['name', 'description'],
  filters: {
    type: { label: '类型', options: [{ label: '菜品', value: 'dish' }, { label: '店铺', value: 'shop' }] },
  },
  formFields: [
    { prop: 'name', label: '名称', type: 'text', required: true },
    { prop: 'type', label: '类型', type: 'select', options: [{ label: '菜品', value: 'dish' }, { label: '店铺', value: 'shop' }], required: true },
    { prop: 'category_id', label: '分类', type: 'select', options: [{ label: '粿品', value: 1 }, { label: '海鲜', value: 2 }, { label: '小吃', value: 3 }] },
    { prop: 'image_url', label: '图片', type: 'image' },
    { prop: 'tags', label: '标签', type: 'tag', limit: 10 },
    { prop: 'description', label: '描述', type: 'textarea' },
    { prop: 'price_range', label: '价格区间', type: 'text', placeholder: '¥ / ¥¥ / ¥¥¥' },
    { prop: 'address', label: '地址', type: 'text' },
    { prop: 'is_recommended', label: '推荐', type: 'switch' },
  ],
  actions: ['create', 'edit', 'delete'],
}
</script>
