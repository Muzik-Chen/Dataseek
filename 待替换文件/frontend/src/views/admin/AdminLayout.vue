<template>
  <div class="admin-layout">
    <AdminSidebar
      :items="adminNavItems"
      :collapsed="sidebarCollapsed"
      @toggle="sidebarCollapsed = !sidebarCollapsed"
    />
    <main class="admin-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { DataBoard, User, Food, Collection, Calendar, ChatRound, TrendCharts, Setting } from '@element-plus/icons-vue'
import AdminSidebar from '@/components/layout/AdminSidebar.vue'

const sidebarCollapsed = ref(false)

/**
 * 统一导航注册表 — Phase 3 引入。
 * 新增管理页面只需在此数组中添加一项，侧边栏自动渲染。
 */
const adminNavItems = [
  { path: '/admin',              label: '仪表盘',   icon: DataBoard },
  { path: '/admin/users',        label: '用户管理', icon: User },
  { path: '/admin/foods',        label: '美食管理', icon: Food },
  { path: '/admin/heritages',    label: '非遗管理', icon: Collection },
  { path: '/admin/events',       label: '节日管理', icon: Calendar },
  { path: '/admin/posts',        label: '社区审核', icon: ChatRound },
  { path: '/admin/dashboard-data', label: '数据管理', icon: TrendCharts },
  { path: '/admin/settings',     label: '系统设置', icon: Setting },
]
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.admin-main {
  flex: 1;
  background: var(--bg);
  padding: 32px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .admin-main { padding: 16px; }
}
</style>
