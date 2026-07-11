<template>
  <div class="admin-page">
    <h1>非遗管理</h1>
    <div class="page-toolbar">
      <el-button type="primary" @click="openDialog()">新增非遗</el-button>
      <el-input v-model="keyword" placeholder="搜索..." clearable style="width:200px" @input="onSearch" />
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="category" label="级别" width="80"><template #default="{ row }"><el-tag :type="row.category==='国家级'?'danger':row.category==='省级'?'warning':'success'" size="small">{{ row.category }}</el-tag></template></el-table-column>
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="region" label="地区" width="80" />
      <el-table-column prop="view_count" label="浏览" width="70" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }"><el-button size="small" @click="openDialog(row)">编辑</el-button><el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button></template>
      </el-table-column>
    </el-table>
    <div class="page-pagination"><el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="total, prev, pager, next" @current-change="loadData" /></div>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑非遗' : '新增非遗'" width="560px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="级别" required><el-select v-model="form.category"><el-option label="国家级" value="国家级" /><el-option label="省级" value="省级" /><el-option label="市级" value="市级" /></el-select></el-form-item>
        <el-form-item label="类型" required><el-select v-model="form.type"><el-option label="传统戏剧" value="传统戏剧" /><el-option label="传统技艺" value="传统技艺" /><el-option label="民俗" value="民俗" /><el-option label="传统舞蹈" value="传统舞蹈" /><el-option label="传统美术" value="传统美术" /></el-select></el-form-item>
        <el-form-item label="地区" required><el-input v-model="form.region" /></el-form-item>
        <el-form-item label="传承人"><el-input v-model="form.inheritor" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" rows="3" /></el-form-item>
        <el-form-item label="图片"><ImageUploader v-model="form.images" :limit="1" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="handleSave">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api/request'
import { toast } from '@/utils/toast'
import { confirmDelete } from '@/utils/dialog'
import { debounce } from '@/utils/debounce'
import ImageUploader from '@/components/common/ImageUploader.vue'

const items = ref([]); const loading = ref(false); const page = ref(1); const total = ref(0); const keyword = ref('')
const dialogVisible = ref(false); const saving = ref(false); const editId = ref(null)
const form = reactive({ name: '', category: '省级', type: '传统技艺', region: '', inheritor: '', description: '', images: [] })

async function loadData() {
  loading.value = true
  try { const data = await api.get('/heritages', { params: { page: page.value, keyword: keyword.value } }); items.value = data.items || []; total.value = data.total || 0 } catch { /* */ } finally { loading.value = false }
}
const onSearch = debounce(() => { page.value = 1; loadData() }, 300)

function openDialog(row) {
  if (row) {
    editId.value = row.id
    Object.assign(form, { name: row.name, category: row.category, type: row.type, region: row.region, inheritor: row.inheritor || '', description: row.description || '', images: row.image_url ? [row.image_url] : [] })
  } else { editId.value = null; Object.assign(form, { name: '', category: '省级', type: '传统技艺', region: '', inheritor: '', description: '', images: [] }) }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    const payload = { ...form, image_url: form.images[0] || '' }; delete payload.images
    if (editId.value) { await api.put(`/admin/heritages/${editId.value}`, payload); toast.success('更新成功') }
    else { await api.post('/admin/heritages', payload); toast.success('新增成功') }
    dialogVisible.value = false; loadData()
  } catch { toast.error('保存失败') } finally { saving.value = false }
}

async function handleDelete(row) {
  try { await confirmDelete('确认删除', `确定删除 "${row.name}" 吗？`); await api.delete(`/admin/heritages/${row.id}`); toast.success('已删除'); loadData() } catch { /* */ }
}

onMounted(() => loadData())
</script>
<style scoped>
.admin-page h1 { font-size: 1.5rem; margin-bottom: 24px; }
.page-toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.page-pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
