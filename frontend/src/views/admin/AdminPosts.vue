<template>
  <AdminCrud ref="crudRef" :config="config">
    <template #column-post_type="{ row }">
      <el-tag size="small">{{ typeLabels[row.post_type] || row.post_type }}</el-tag>
    </template>

    <template #actions="{ row }">
      <el-button size="small" @click="viewDetail(row)">查看</el-button>
      <el-button size="small" type="danger" @click="deletePost(row)">删除</el-button>
    </template>

    <template #detail>
      <el-dialog v-model="detailVisible" title="动态详情" width="600px">
        <template v-if="detail">
          <h2 style="margin-bottom: 12px;">{{ detail.title }}</h2>
          <p style="color: var(--muted); margin-bottom: 16px; white-space: pre-wrap;">{{ detail.content }}</p>
          <div v-if="detail.tags?.length" style="margin-bottom: 12px;">
            <el-tag v-for="t in detail.tags" :key="t" size="small" style="margin-right: 6px;">#{{ t }}</el-tag>
          </div>
          <p style="font-size: 12px; color: var(--muted);">
            发布于 {{ detail.created_at }} | 👍{{ detail.like_count }} 💬{{ detail.comment_count }} 👀{{ detail.view_count }}
          </p>
        </template>
        <template #footer>
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button type="danger" @click="deletePost(detail); detailVisible = false">删除此动态</el-button>
        </template>
      </el-dialog>
    </template>
  </AdminCrud>
</template>

<script setup>
import { ref } from 'vue'
import AdminCrud from '@/components/admin/AdminCrud.vue'
import adminApi from '@/api/admin'
import { toast } from '@/utils/toast'
import { confirmDelete } from '@/utils/dialog'

const crudRef = ref(null)
const detailVisible = ref(false)
const detail = ref(null)

const typeLabels = { recommend: '伴手礼', challenge: '盲盒', social: '种草', study: '研学' }

const config = {
  resource: 'posts',
  title: '社区审核',
  columns: [
    { prop: 'id', label: 'ID', width: 60 },
    { prop: 'title', label: '标题', minWidth: 180 },
    { prop: 'post_type', label: '类型', width: 80 },
    { prop: 'like_count', label: '👍', width: 60 },
    { prop: 'comment_count', label: '💬', width: 60 },
    { prop: 'created_at', label: '发布时间', type: 'datetime', width: 160 },
  ],
  filters: {
    post_type: { label: '类型', options: [
      { label: '伴手礼', value: 'recommend' }, { label: '盲盒', value: 'challenge' },
      { label: '种草', value: 'social' }, { label: '研学', value: 'study' },
    ]},
  },
  actions: ['delete'],
}

function viewDetail(row) {
  detail.value = row
  detailVisible.value = true
}

async function deletePost(row) {
  try {
    await confirmDelete('确认删除', `确定删除 "${row.title}" 吗？`)
  } catch {
    return
  }
  try {
    await adminApi.posts.delete(row.id)
    toast.success('已删除')
    crudRef.value?.loadData()
  } catch (e) {
    toast.error(e?.message || '删除失败')
  }
}
</script>
