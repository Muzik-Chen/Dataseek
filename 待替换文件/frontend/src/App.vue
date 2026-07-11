<template>
  <div id="chaoshan-app" :class="{ 'no-header-footer': hideLayout }">
    <AppHeader v-if="!hideLayout && !isAdminRoute" @toggle-search="searchVisible = true" />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <AppFooter v-if="!hideLayout && !isAdminRoute" />
    <!-- 全局组件 -->
    <ChatWidget v-if="!isAdminRoute && route.path !== '/chat'" />
    <SearchOverlay v-model="searchVisible" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import ChatWidget from '@/components/business/ChatWidget.vue'
import SearchOverlay from '@/components/common/SearchOverlay.vue'

const route = useRoute()

const searchVisible = ref(false)

const hideLayout = computed(() => {
  const path = route.path
  return path.startsWith('/admin')
})

const isAdminRoute = computed(() => route.path.startsWith('/admin'))
</script>

<style>
#chaoshan-app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-md);
  /* 潮汕风景照背景 — 与首页探索潮汕以下部分保持一致 */
  background:
    linear-gradient(180deg, oklch(0.95 0.01 85 / 0.92) 0%, oklch(0.92 0.02 80 / 0.88) 100%),
    url('https://images.unsplash.com/photo-1587876933737-e1570c20fb09?w=1920&h=1080&fit=crop') center/cover no-repeat fixed;
  background-attachment: fixed;
}

#chaoshan-app.no-header-footer .main-content {
  max-width: none;
  padding: 0;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

/* iOS 移动端：取消 fixed 背景附着（避免渲染闪烁） */
@media (max-width: 767px) {
  .main-content {
    background-attachment: scroll;
  }
}
</style>
