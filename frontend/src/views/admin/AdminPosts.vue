<template>
  <div class="admin-page">
    <h1>社区审核</h1>
    <div class="page-toolbar">
      <el-select v-model="typeFilter" placeholder="类型筛选" clearable style="width:140px" @change="loadData">
        <el-option label="伴手礼" value="recommend" /><el-option label="盲盒" value="challenge" />
        <el-option label="种草" value="social" /><el-option label="研学" value="study" />
      </el-select>
    </div>
    <el-table :data="posts" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
      <el-table-column label="类型" width="80"><template #default="{ row }"><el-tag size="small">{{ { recommend: '伴手礼', challenge: '盲盒', social: '种草', study: '研学' }[row.post_type] }}</el-tag></template></el-table-column>
      <el-table-column prop="like_count" label="👍" width="60" />
      <el-table-column prop="comment_count" label="💬" width="60" />
      <el-table-column prop="created_at" label="发布时间" width="160" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">查看</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="page-pagination"><el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="total, prev, pager, next" @current-change="loadData" /></div>

    <el-dialog v-model="detailVisible" title="动态详情" width="600px">
      <h2>{{ detail.title }}</h2>
      <p style="color: var(--muted); margin-bottom: 16px;">{{ detail.content }}</p>
      <div v-if="detail.tags?.length" style="margin-bottom: 12px;"><el-tag v-for="t in detail.tags" :key="t" size="small" style="margin-right: 6px;">#{{ t }}</el-tag></div>
      <p style="font-size: 12px; color: var(--muted);">发布于 {{ detail.created_at }} | 👍{{ detail.like_count }} 💬{{ detail.comment_count }} 👀{{ detail.view_count }}</p>
      <template #footer><el-button @click="detailVisible = false">关闭</el-button><el-button type="danger" @click="handleDelete(detail); detailVisible = false">删除此动态</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/request'
import { toast } from '@/utils/toast'
import { confirmDelete } from '@/utils/dialog'

const posts = ref([]); const loading = ref(false); const page = ref(1); const total = ref(0); const typeFilter = ref('')
const detailVisible = ref(false); const detail = ref({})

async function loadData() {
  loading.value = true
  try { const data = await api.get('/admin/posts', { params: { page: page.value, post_type: typeFilter.value } }); posts.value = data.items || []; total.value = data.total || 0 } catch { /* */ } finally { loading.value = false }
}

function viewDetail(row) { detail.value = row; detailVisible.value = true }

async function handleDelete(row) {
  try { await confirmDelete('确认删除', `确定删除 "${row.title}" 吗？`); await api.delete(`/admin/posts/${row.id}`); toast.success('已删除'); loadData() } catch { /* */ }
}

onMounted(() => loadData())
</script>
<style scoped>
.admin-page h1 { font-size: 1.5rem; margin-bottom: 24px; }
.page-toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.page-pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
