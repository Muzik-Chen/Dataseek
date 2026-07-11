<template>
<<<<<<< HEAD
  <div class="admin-sidebar" :class="{ collapsed }">
    <div class="sidebar-brand">
      <span class="brand-icon">🍵</span>
      <span v-show="!collapsed" class="brand-title">管理后台</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in items"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="active"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <router-link to="/" class="back-link">← 返回前台</router-link>
    </div>

    <div class="sidebar-toggle" @click="$emit('toggle')">
      <el-icon><component :is="collapsed ? Expand : Fold" /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { Expand, Fold } from '@element-plus/icons-vue'

defineProps({
  collapsed: { type: Boolean, default: false },
  items: { type: Array, required: true },
})

defineEmits(['toggle'])
=======
  <el-menu
    :default-active="activeMenu"
    :collapse="collapsed"
    :router="true"
    background-color="#1a1a2e"
    text-color="#aaa"
    active-text-color="#fff"
    class="admin-sidebar"
  >
    <div class="admin-sidebar__logo" :class="{ collapsed }">
      <span v-if="!collapsed" class="admin-sidebar__title">管理后台</span>
      <span v-else class="admin-sidebar__icon">🍵</span>
    </div>

    <el-menu-item
      v-for="item in menuItems"
      :key="item.path"
      :index="item.path"
    >
      <el-icon><component :is="item.icon" /></el-icon>
      <template #title>{{ item.label }}</template>
    </el-menu-item>

    <div class="admin-sidebar__toggle" @click="$emit('toggle')">
      <el-icon><component :is="collapsed ? 'Expand' : 'Fold'" /></el-icon>
    </div>
  </el-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  collapsed: { type: Boolean, default: false },
})

defineEmits(['toggle'])

const route = useRoute()
const activeMenu = computed(() => route.path)

const menuItems = [
  { path: '/admin', label: '仪表盘', icon: 'DataBoard' },
  { path: '/admin/users', label: '用户管理', icon: 'User' },
  { path: '/admin/foods', label: '美食管理', icon: 'Food' },
  { path: '/admin/heritages', label: '非遗管理', icon: 'Museum' },
  { path: '/admin/events', label: '节日管理', icon: 'Calendar' },
  { path: '/admin/posts', label: '社区审核', icon: 'ChatLineSquare' },
  { path: '/admin/dashboard-data', label: '数据管理', icon: 'TrendCharts' },
  { path: '/admin/settings', label: '系统设置', icon: 'Setting' },
]
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
</script>

<style scoped>
.admin-sidebar {
<<<<<<< HEAD
  width: 240px;
  background: oklch(0.15 0.01 248);
  color: #fff;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.2s;
  min-height: 100vh;
}

.admin-sidebar.collapsed { width: 64px; }

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 24px 20px;
  border-bottom: 1px solid oklch(1 0 0 / 0.08);
}

.brand-icon { font-size: 24px; flex-shrink: 0; }

.brand-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  white-space: nowrap;
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
  white-space: nowrap;
  overflow: hidden;
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
  padding: 12px 20px;
  border-top: 1px solid oklch(1 0 0 / 0.08);
}

.back-link {
  color: oklch(1 0 0 / 0.5);
  text-decoration: none;
  font-size: 13px;
  transition: color 0.2s;
  white-space: nowrap;
}

.back-link:hover { color: #fff; }

.sidebar-toggle {
  padding: 12px;
  text-align: center;
  cursor: pointer;
  color: oklch(1 0 0 / 0.4);
  border-top: 1px solid oklch(1 0 0 / 0.08);
  transition: color 0.2s;
  font-size: 18px;
}

.sidebar-toggle:hover { color: #fff; }

@media (max-width: 768px) {
  .admin-sidebar { width: 64px; }
  .brand-title, .nav-item span, .back-link { display: none; }
=======
  height: 100vh;
  display: flex;
  flex-direction: column;
  border-right: none;
}

.admin-sidebar:not(.el-menu--collapse) {
  width: 240px;
}

.admin-sidebar__logo {
  padding: 20px 16px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 8px;
}

.admin-sidebar__logo.collapsed {
  padding: 16px;
}

.admin-sidebar__title {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
}

.admin-sidebar__icon {
  font-size: 24px;
}

.admin-sidebar__toggle {
  margin-top: auto;
  padding: 16px;
  text-align: center;
  cursor: pointer;
  color: #aaa;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  transition: color 0.2s;
}

.admin-sidebar__toggle:hover {
  color: #fff;
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
}
</style>
