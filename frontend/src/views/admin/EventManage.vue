<template>
<<<<<<< HEAD
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
=======
  <div class="admin-page">
    <h1>节日/活动管理</h1>
    <div class="page-toolbar">
      <el-button type="primary" @click="openDialog()">新增节日/活动</el-button>
      <el-select v-model="typeFilter" placeholder="类型筛选" clearable style="width:140px" @change="loadData">
        <el-option label="节日" value="festival" /><el-option label="活动" value="event" /><el-option label="民俗" value="custom" />
      </el-select>
    </div>
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="event_type" label="类型" width="80">
        <template #default="{ row }"><el-tag size="small">{{ { festival: '节日', event: '活动', custom: '民俗' }[row.event_type] }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="event_date" label="日期" width="110" />
      <el-table-column prop="lunar_date" label="农历" width="100" />
      <el-table-column prop="region" label="地区" width="100" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }"><el-button size="small" @click="openDialog(row)">编辑</el-button><el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button></template>
      </el-table-column>
    </el-table>
    <div class="page-pagination"><el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="total, prev, pager, next" @current-change="loadData" /></div>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑' : '新增'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型" required><el-select v-model="form.event_type"><el-option label="节日" value="festival" /><el-option label="活动" value="event" /><el-option label="民俗" value="custom" /></el-select></el-form-item>
        <el-form-item label="公历日期" required><el-date-picker v-model="form.event_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="农历备注"><el-input v-model="form.lunar_date" placeholder="如：正月十五" /></el-form-item>
        <el-form-item label="地区" required><el-input v-model="form.region" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" rows="3" /></el-form-item>
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

const items = ref([]); const loading = ref(false); const page = ref(1); const total = ref(0); const typeFilter = ref('')
const dialogVisible = ref(false); const saving = ref(false); const editId = ref(null)
const form = reactive({ name: '', event_type: 'festival', event_date: '', lunar_date: '', region: '', description: '' })

async function loadData() {
  loading.value = true
  try { const data = await api.get('/admin/events', { params: { page: page.value, event_type: typeFilter.value } }); items.value = data.items || []; total.value = data.total || 0 } catch { /* */ } finally { loading.value = false }
}

function openDialog(row) {
  if (row) { editId.value = row.id; Object.assign(form, { name: row.name, event_type: row.event_type, event_date: row.event_date, lunar_date: row.lunar_date || '', region: row.region, description: row.description || '' }) }
  else { editId.value = null; Object.assign(form, { name: '', event_type: 'festival', event_date: '', lunar_date: '', region: '', description: '' }) }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editId.value) { await api.put(`/admin/events/${editId.value}`, form); toast.success('更新成功') }
    else { await api.post('/admin/events', form); toast.success('新增成功') }
    dialogVisible.value = false; loadData()
  } catch { toast.error('保存失败') } finally { saving.value = false }
}

async function handleDelete(row) {
  try { await confirmDelete('确认删除', `确定删除 "${row.name}" 吗？`); await api.delete(`/admin/events/${row.id}`); toast.success('已删除'); loadData() } catch { /* */ }
}

onMounted(() => loadData())
</script>
<style scoped>
.admin-page h1 { font-size: 1.5rem; margin-bottom: 24px; }
.page-toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.page-pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
