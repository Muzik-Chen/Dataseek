<template>
  <div class="admin-layout">
    <aside class="admin-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-brand">
        <span class="brand-icon">🍵</span>
        <span v-show="!sidebarCollapsed">管理后台</span>
      </div>
      <nav class="sidebar-nav">
        <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item" active-class="active">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <router-link to="/" class="back-link">← 返回前台</router-link>
      </div>
    </aside>
    <main class="admin-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { DataBoard, User, Food, Collection, Calendar, ChatRound, TrendCharts, Setting } from '@element-plus/icons-vue'

const sidebarCollapsed = ref(false)

const navItems = [
  { path: '/admin', label: '仪表盘', icon: DataBoard },
  { path: '/admin/users', label: '用户管理', icon: User },
  { path: '/admin/foods', label: '美食管理', icon: Food },
  { path: '/admin/heritages', label: '非遗管理', icon: Collection },
  { path: '/admin/events', label: '节日管理', icon: Calendar },
  { path: '/admin/posts', label: '社区审核', icon: ChatRound },
  { path: '/admin/dashboard-data', label: '数据管理', icon: TrendCharts },
  { path: '/admin/settings', label: '系统设置', icon: Setting },
]
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.admin-sidebar {
  width: 240px;
  background: oklch(0.15 0.01 248);
  color: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.2s;
}

.admin-sidebar.collapsed {
  width: 64px;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 24px;
  border-bottom: 1px solid oklch(1 0 0 / 0.08);
  font-size: 18px;
  font-weight: 600;
}

.brand-icon {
  font-size: 24px;
}

.sidebar-nav {
  flex: 1;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: oklch(1 0 0 / 0.65);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
}

.nav-item:hover {
  background: oklch(1 0 0 / 0.08);
  color: #fff;
}

.nav-item.active {
  background: var(--primary, #C0392B);
  color: #fff;
}

.sidebar-footer {
  padding: 16px 24px;
  border-top: 1px solid oklch(1 0 0 / 0.08);
}

.back-link {
  color: oklch(1 0 0 / 0.5);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.back-link:hover { color: #fff; }

.admin-main {
  flex: 1;
  background: var(--bg);
  padding: 32px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .admin-sidebar { width: 64px; }
  .sidebar-brand span:last-child,
  .nav-item span,
  .back-link { display: none; }
  .admin-main { padding: 16px; }
}
</style>
