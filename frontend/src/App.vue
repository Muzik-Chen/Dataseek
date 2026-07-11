<template>
  <div id="chaoshan-app" :class="{ 'no-header-footer': hideLayout }">
    <AppHeader v-if="!hideLayout && !isAdminRoute" @toggle-search="searchVisible = true" />
    <main class="main-content" :class="{ 'main-content--full': isFullMap }">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <AppFooter v-if="!hideLayout && !isAdminRoute && !isFullMap" />
    <!-- 全局组件 -->
    <ChatWidget v-if="!isAdminRoute && !isFullMap && route.path !== '/chat'" />
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
  return path.startsWith('/login') || path.startsWith('/register') || path.startsWith('/admin')
})

const isAdminRoute = computed(() => route.path.startsWith('/admin'))
const isFullMap = computed(() => route.meta.fullMap)
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
  /* 极淡纸纹 — 用品牌琥珀色在 2% 透明度模拟宣纸质感 */
  background-image:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      oklch(0.75 0.06 75 / 0.015) 2px,
      oklch(0.75 0.06 75 / 0.015) 4px
    );
}

#chaoshan-app.no-header-footer .main-content {
  max-width: none;
  padding: 0;
}

.main-content--full {
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
</style>
