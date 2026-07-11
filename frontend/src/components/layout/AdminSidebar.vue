<template>
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
</script>

<style scoped>
.admin-sidebar {
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
}
</style>
