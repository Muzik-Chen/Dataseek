<template>
  <header class="app-header" :class="{ 'menu-open': mobileMenuOpen }">
    <div class="header-inner">
      <router-link to="/" class="logo" aria-label="潮汕文化宣传平台 首页">
        <span class="logo-icon">潮</span>
        <span class="logo-text">潮汕文化</span>
      </router-link>

      <nav class="nav-desktop" aria-label="主导航">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: isActive(item) }"
        >
          <el-icon v-if="item.icon" class="nav-icon"><component :is="item.icon" /></el-icon>
          {{ item.label }}
        </router-link>
      </nav>

      <div class="header-actions">
        <SearchBar
          v-model="searchText"
          placeholder="搜索美食、非遗、民俗…"
          :hot-keywords="hotKeywords"
          @search="onSearch"
        />
        <UserDropdown />
        <button class="mobile-menu-btn" @click="mobileMenuOpen = !mobileMenuOpen" aria-label="菜单">
          <el-icon :size="22"><component :is="mobileMenuOpen ? Close : Menu" /></el-icon>
        </button>
      </div>
    </div>

    <!-- Mobile nav drawer -->
    <transition name="drawer-slide">
      <nav v-if="mobileMenuOpen" class="nav-mobile" aria-label="移动端导航">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          @click="mobileMenuOpen = false"
        >
          <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
          {{ item.label }}
        </router-link>
        <div class="mobile-auth">
          <template v-if="!userStore.isLoggedIn">
            <router-link to="/login" class="btn-text" @click="mobileMenuOpen = false">登录</router-link>
            <router-link to="/register" class="btn-primary-sm" @click="mobileMenuOpen = false">注册</router-link>
          </template>
        </div>
      </nav>
    </transition>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  HomeFilled, Food, Collection, Calendar,
  Guide, ChatRound, ChatDotRound, DataAnalysis,
  Close, Menu,
} from '@element-plus/icons-vue'
import SearchBar from '@/components/common/SearchBar.vue'
import UserDropdown from '@/components/user/UserDropdown.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const searchText = ref('')
const mobileMenuOpen = ref(false)

const navItems = [
  { path: '/', label: '首页', icon: HomeFilled },
  { path: '/foods', label: '美食', icon: Food },
  { path: '/heritages', label: '非遗', icon: Collection },
  { path: '/festival', label: '民俗', icon: Calendar },
  { path: '/trip/create', label: '行程', icon: Guide },
  { path: '/chat', label: 'AI对话', icon: ChatDotRound },
  { path: '/community', label: '社区', icon: ChatRound },
  { path: '/dashboard', label: '数据', icon: DataAnalysis },
]

const hotKeywords = ['牛肉火锅', '英歌舞', '工夫茶', '粿品', '生腌']

function isActive(item) {
  if (item.path === '/') return route.path === '/'
  return route.path.startsWith(item.path)
}

function onSearch(keyword) {
  if (keyword.trim()) {
    router.push({ path: '/search', query: { keyword: keyword.trim() } })
  }
}
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  background: oklch(1 0 0 / 0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-light);
}

.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-md);
  height: 60px;
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

/* Logo */
.logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
  color: var(--ink);
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--brand-red);
  color: var(--text-inverse);
  font-size: var(--fs-lg);
  font-weight: 700;
  border-radius: var(--radius-sm);
}

.logo-text {
  font-size: var(--fs-lg);
  font-weight: 700;
  letter-spacing: 0.02em;
}

/* Desktop nav */
.nav-desktop {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: var(--space-sm) var(--space-md);
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  transition: color var(--duration-fast);
  white-space: nowrap;
  position: relative;
}

.nav-link:hover {
  color: var(--brand-red);
}

/* 红桃粿印 — 激活态下方菱形标记 */
.nav-link.active {
  color: var(--brand-red);
  background: transparent;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 6px;
  height: 6px;
  background: var(--brand-red);
  border-radius: 1px;
}

.nav-icon {
  font-size: var(--fs-base);
}

/* Header actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-left: auto;
}

/* Buttons */
.btn-text {
  padding: var(--space-sm) var(--space-md);
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--ink);
  border-radius: var(--radius-sm);
  transition: background 0.2s;
}

.btn-text:hover {
  background: var(--surface);
}

.btn-primary-sm {
  padding: var(--space-sm) var(--space-md);
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--text-inverse);
  background: var(--brand-red);
  border-radius: var(--radius-sm);
  transition: background var(--duration-fast);
}

.btn-primary-sm:hover {
  background: var(--brand-red-hover);
}

/* Mobile menu */
.mobile-menu-btn {
  display: none;
  border: none;
  background: none;
  color: var(--ink);
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
}

.nav-mobile {
  display: none;
  flex-direction: column;
  padding: var(--space-md);
  background: var(--bg);
  border-top: 1px solid var(--el-border-color-light);
  max-height: calc(100vh - 60px);
  overflow-y: auto;
}

.mobile-auth {
  display: flex;
  gap: var(--space-sm);
  padding-top: var(--space-md);
  border-top: 1px solid var(--el-border-color-light);
  margin-top: var(--space-sm);
}

.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.drawer-slide-enter-from,
.drawer-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Responsive */
@media (max-width: 1023px) {
  .nav-desktop { display: none; }
  .mobile-menu-btn { display: flex; }
  .nav-mobile { display: flex; }
}

@media (max-width: 767px) {
  .logo-text { display: none; }
  .header-actions { gap: var(--space-sm); }
}
</style>
