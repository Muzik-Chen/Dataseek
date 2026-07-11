<template>
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

function viewDetail(row) {
  toast.info(`用户详情: ${row.nickname} — 功能开发中`)
}

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
