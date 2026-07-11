<template>
  <div class="admin-page">
    <h1>美食管理</h1>

    <div class="page-toolbar">
      <el-button type="primary" @click="openDialog()">新增美食</el-button>
      <el-input v-model="keyword" placeholder="搜索..." clearable style="width:200px" @input="onSearch" />
    </div>

    <el-table :data="foods" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="type" label="类型" width="80">
        <template #default="{ row }">{{ row.type === 'shop' ? '店铺' : '菜品' }}</template>
      </el-table-column>
      <el-table-column prop="price_range" label="价格" width="70" />
      <el-table-column prop="view_count" label="浏览" width="70" />
      <el-table-column label="推荐" width="70">
        <template #default="{ row }">
          <el-switch :model-value="row.is_recommended" @change="toggleRecommended(row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="page-pagination">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
        layout="total, prev, pager, next" @current-change="loadData" />
    </div>

    <el-dialog v-model="dialogVisible" :title="editId ? '编辑美食' : '新增美食'" width="560px" @close="resetForm">
      <el-form ref="formRef" :model="form" label-width="80px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型" required>
          <el-radio-group v-model="form.type"><el-radio value="dish">菜品</el-radio><el-radio value="shop">店铺</el-radio></el-radio-group>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category_id" placeholder="选择分类"><el-option label="粿品" :value="1" /><el-option label="海鲜" :value="2" /><el-option label="小吃" :value="3" /></el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" rows="3" /></el-form-item>
        <el-form-item label="价格区间"><el-input v-model="form.price_range" placeholder="¥ / ¥¥ / ¥¥¥" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="标签"><el-input v-model="form.tagsStr" placeholder="逗号分隔" /></el-form-item>
        <el-form-item label="图片"><ImageUploader v-model="form.images" :limit="1" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
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

const foods = ref([]); const loading = ref(false); const page = ref(1); const pageSize = ref(20); const total = ref(0)
const keyword = ref(''); const dialogVisible = ref(false); const saving = ref(false); const editId = ref(null)
const form = reactive({ name: '', type: 'dish', category_id: null, description: '', price_range: '', address: '', tagsStr: '', images: [] })

async function loadData() {
  loading.value = true
  try {
    const data = await api.get('/foods', { params: { page: page.value, page_size: pageSize.value, keyword: keyword.value } })
    foods.value = data.items || []; total.value = data.total || 0
  } catch { /* */ } finally { loading.value = false }
}
const onSearch = debounce(() => { page.value = 1; loadData() }, 300)

function openDialog(row) {
  if (row) {
    editId.value = row.id
    Object.assign(form, { name: row.name, type: row.type, category_id: row.category_id, description: row.description, price_range: row.price_range, address: row.address, tagsStr: (row.tags || []).join(','), images: row.image_url ? [row.image_url] : [] })
  } else {
    editId.value = null; resetForm()
  }
  dialogVisible.value = true
}

function resetForm() {
  editId.value = null
  Object.assign(form, { name: '', type: 'dish', category_id: null, description: '', price_range: '', address: '', tagsStr: '', images: [] })
}

async function handleSave() {
  saving.value = true
  try {
    const payload = { ...form, tags: form.tagsStr.split(',').map(s => s.trim()).filter(Boolean), image_url: form.images[0] || '' }
    delete payload.tagsStr; delete payload.images
    if (editId.value) {
      await api.put(`/admin/foods/${editId.value}`, payload)
      toast.success('更新成功')
    } else {
      await api.post('/admin/foods', payload)
      toast.success('新增成功')
    }
    dialogVisible.value = false; loadData()
  } catch { toast.error('保存失败') } finally { saving.value = false }
}

async function toggleRecommended(row) {
  try { await api.put(`/admin/foods/${row.id}`, { is_recommended: !row.is_recommended }); row.is_recommended = !row.is_recommended } catch { /* */ }
}

async function handleDelete(row) {
  try {
    await confirmDelete('确认删除', `确定删除 "${row.name}" 吗？`)
    await api.delete(`/admin/foods/${row.id}`); toast.success('已删除'); loadData()
  } catch { /* */ }
}

onMounted(() => loadData())
</script>

<style scoped>
.admin-page h1 { font-size: 1.5rem; margin-bottom: 24px; }
.page-toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.page-pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
