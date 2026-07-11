<template>
<<<<<<< HEAD
  <AdminCrud :config="config">
    <template #column-role="{ row }">
      <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
        {{ row.role === 'admin' ? '管理员' : '用户' }}
      </el-tag>
    </template>

    <template #column-is_disabled="{ row }">
      <template v-if="row.role === 'admin'">
        <el-tag type="warning" size="small">管理员</el-tag>
      </template>
      <template v-else>
        <el-switch
          :model-value="!row.is_disabled"
          size="small"
          @change="(val) => toggleDisabled(row, val)"
        />
      </template>
    </template>

    <template #actions="{ row }">
      <el-button size="small" @click="viewDetail(row)">详情</el-button>
      <el-button
        v-if="row.role !== 'admin'"
        size="small"
        type="danger"
        @click="deleteUser(row)"
      >删除</el-button>
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

const config = {
  resource: 'users',
  title: '用户管理',
  columns: [
    { prop: 'id', label: 'ID', width: 60 },
    { prop: 'email', label: '邮箱', width: 180 },
    { prop: 'nickname', label: '昵称', minWidth: 120 },
    { prop: 'persona_type', label: '类型', width: 100 },
    { prop: 'role', label: '角色', width: 80 },
    { prop: 'is_disabled', label: '状态', width: 80 },
    { prop: 'created_at', label: '注册时间', type: 'datetime', width: 160 },
  ],
  searchFields: ['email', 'nickname'],
  filters: {
    role: { label: '角色', options: [{ label: '普通用户', value: 'user' }, { label: '管理员', value: 'admin' }] },
    persona_type: { label: '用户类型', options: [
      { label: '游客', value: 'tourist' }, { label: '爱好者', value: 'enthusiast' }, { label: '美食家', value: 'foodie' },
    ]},
  },
  actions: ['delete'],
}

// ── Inline disable toggle ──────────────────────────

async function toggleDisabled(row, val) {
  try {
    await adminApi.users.update(row.id, { is_disabled: !val })
    row.is_disabled = !val
    toast.success(row.is_disabled ? '已禁用' : '已启用')
  } catch (e) {
    toast.error(e?.message || '操作失败')
  }
}

// ── Detail (placeholder) ───────────────────────────
=======
  <div class="admin-page">
    <h1>用户管理</h1>

    <div class="page-toolbar">
      <el-input v-model="keyword" placeholder="搜索手机号/昵称..." clearable style="width:240px" @input="onSearch" />
      <el-select v-model="roleFilter" placeholder="角色筛选" clearable style="width:140px" @change="loadData">
        <el-option label="普通用户" value="user" />
        <el-option label="管理员" value="admin" />
      </el-select>
      <el-select v-model="personaFilter" placeholder="用户类型" clearable style="width:140px" @change="loadData">
        <el-option label="游客" value="tourist" />
        <el-option label="家庭" value="family" />
        <el-option label="情侣" value="couple" />
        <el-option label="研究者" value="researcher" />
      </el-select>
      <el-button type="primary" @click="loadData">查询</el-button>
    </div>

    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column prop="nickname" label="昵称" min-width="120" />
      <el-table-column prop="persona_type" label="类型" width="100" />
      <el-table-column prop="role" label="角色" width="80">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">{{ row.role === 'admin' ? '管理员' : '用户' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-switch :model-value="!row.is_disabled" active-text="" inactive-text="" @change="toggleDisabled(row)" />
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="160" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="page-pagination">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/request'
import { toast } from '@/utils/toast'
import { confirmDelete } from '@/utils/dialog'
import { debounce } from '@/utils/debounce'

const users = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const roleFilter = ref('')
const personaFilter = ref('')

async function loadData() {
  loading.value = true
  try {
    const data = await api.get('/admin/users', {
      params: { page: page.value, page_size: pageSize.value, keyword: keyword.value, role: roleFilter.value, persona_type: personaFilter.value }
    })
    users.value = data.items || []
    total.value = data.total || 0
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}

const onSearch = debounce(() => { page.value = 1; loadData() }, 300)
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22

function viewDetail(row) {
  toast.info(`用户详情: ${row.nickname} — 功能开发中`)
}

<<<<<<< HEAD
// ── Delete (FIXED: now actually sends DELETE) ──────

async function deleteUser(row) {
  try {
    await confirmDelete('确认删除', `确定删除用户 "${row.nickname}" 吗？此操作将级联删除该用户的所有数据且不可撤销。`)
  } catch {
    return // user cancelled
  }
  try {
    await adminApi.users.delete(row.id)
    toast.success('已删除')
    crudRef.value?.loadData()
  } catch (e) {
    toast.error(e?.message || '删除失败')
  }
}
</script>
=======
async function toggleDisabled(row) {
  try {
    await api.put(`/admin/users/${row.id}`, { is_disabled: !row.is_disabled })
    row.is_disabled = !row.is_disabled
    toast.success(row.is_disabled ? '已禁用' : '已启用')
  } catch { toast.error('操作失败') }
}

async function handleDelete(row) {
  try {
    await confirmDelete('确认删除', `确定删除用户 "${row.nickname}" 吗？`)
    toast.success('已删除')
    loadData()
  } catch { /* 用户取消 */ }
}

onMounted(() => loadData())
</script>

<style scoped>
.admin-page h1 { font-size: 1.5rem; margin-bottom: 24px; }
.page-toolbar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.page-pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
