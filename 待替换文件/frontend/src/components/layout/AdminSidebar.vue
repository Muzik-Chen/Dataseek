<template>
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
</script>

<style scoped>
.admin-sidebar {
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
}
</style>
