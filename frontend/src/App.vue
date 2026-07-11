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
  margin: 0;
  padding: 0 var(--space-sm);
  background: var(--bg-page);
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

</style>
