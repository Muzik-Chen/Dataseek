<template>
  <header class="app-header" :class="{ 'menu-open': mobileMenuOpen }">
    <div class="header-inner">
      <router-link to="/" class="logo" aria-label="潮汕文化宣传平台 首页">
        <span class="logo-icon">潮</span>
        <span class="logo-text">岭海潮韵</span>
      </router-link>

      <nav class="nav-desktop" aria-label="主导航">
        <router-link
          v-for="item in visibleNavItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: isActive(item) }"
        >
          <el-icon v-if="item.icon" class="nav-icon"><component :is="item.icon" /></el-icon>
          {{ item.label }}
        </router-link>
        <!-- 水墨笔触装饰线 -->
        <span class="nav-brush-line" aria-hidden="true"></span>
      </nav>

      <div class="header-actions">
        <SearchBar
          v-model="searchText"
          placeholder="搜索美食、非遗…"
          :hot-keywords="hotKeywords"
          @search="onSearch"
        />
        <div class="user-area">
          <!-- 音乐控制按钮 -->
          <button
            class="music-toggle-btn"
            :class="{ 'music-toggle-btn--playing': musicPlaying }"
            :title="musicPlaying ? '暂停音乐' : '播放音乐'"
            :aria-label="musicPlaying ? '暂停音乐' : '播放音乐'"
            @click="toggleMusic"
          >
            <el-icon :size="18">
              <component :is="musicPlaying ? VideoPause : VideoPlay" />
            </el-icon>
          </button>
          <template v-if="userStore.isLoggedIn">
            <el-dropdown trigger="click" popper-class="user-dropdown-popper">
              <button class="user-avatar-btn" aria-label="用户菜单">
                <el-avatar :size="34" :icon="UserFilled" />
                <span class="user-nickname">{{ userStore.user?.nickname || '用户' }}</span>
                <el-icon class="arrow-icon"><ArrowDown /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>
                    <router-link to="/profile">个人中心</router-link>
                  </el-dropdown-item>
                  <el-dropdown-item>
                    <router-link to="/trip/create">我的行程</router-link>
                  </el-dropdown-item>
                  <el-dropdown-item v-if="userStore.isAdmin">
                    <router-link to="/admin">管理后台</router-link>
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="userStore.logout()">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <router-link to="/login" class="btn-text">登录</router-link>
            <router-link to="/register" class="btn-primary-sm">注册</router-link>
          </template>
        </div>
        <button class="mobile-menu-btn" @click="mobileMenuOpen = !mobileMenuOpen" aria-label="菜单">
          <el-icon :size="22"><component :is="mobileMenuOpen ? Close : Menu" /></el-icon>
        </button>
      </div>
    </div>

    <!-- Mobile nav drawer -->
    <transition name="drawer-slide">
      <nav v-if="mobileMenuOpen" class="nav-mobile" aria-label="移动端导航">
        <!-- 移动端顶部水墨装饰 -->
        <div class="mobile-ink-decoration" aria-hidden="true"></div>
        <router-link
          v-for="item in visibleNavItems"
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
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  HomeFilled, Food, Collection, Calendar,
  Guide, ChatRound, ChatDotRound, DataAnalysis, Setting,
  ArrowDown, UserFilled, Close, Menu, VideoPlay, VideoPause,
} from '@element-plus/icons-vue'
import SearchBar from '@/components/common/SearchBar.vue'
import { useMusic } from '@/composables/useMusic'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const searchText = ref('')
const mobileMenuOpen = ref(false)

const { isPlaying: musicPlaying, toggle: toggleMusic } = useMusic()

const navItems = [
  { path: '/', label: '首页', icon: HomeFilled },
  { path: '/foods', label: '美食', icon: Food },
  { path: '/heritages', label: '非遗', icon: Collection },
  { path: '/festival', label: '民俗', icon: Calendar },
  { path: '/trip/create', label: '行程', icon: Guide },
  { path: '/chat', label: 'AI对话', icon: ChatDotRound },
  { path: '/community', label: '社区', icon: ChatRound },
  { path: '/dashboard', label: '数据', icon: DataAnalysis },
  { path: '/admin', label: '管理', icon: Setting, adminOnly: true },
]

const visibleNavItems = computed(() =>
  navItems.filter(item => !item.adminOnly || userStore.isAdmin)
)

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
/* ============================================
   半透明暗灰毛玻璃导航 — 潮汕文化宣传平台
   保留水墨笔触与纹理，底色为暗灰半透明玻璃
   ============================================ */

.app-header {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);

  /* 暗灰半透明底色，叠加极淡的水墨纹理 */
  background:
    /* 细微横纹 — 模拟宣纸帘纹（调整为暗调） */
    repeating-linear-gradient(
      180deg,
      transparent,
      transparent 1px,
      rgba(255, 255, 255, 0.015) 1px,
      rgba(255, 255, 255, 0.015) 2px
    ),
    /* 散布的墨点纹理 — 暗部透明，保持水墨感 */
    radial-gradient(ellipse at 15% 30%, rgba(0, 0, 0, 0.08) 0%, transparent 60%),
    radial-gradient(ellipse at 78% 55%, rgba(0, 0, 0, 0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 42% 80%, rgba(0, 0, 0, 0.07) 0%, transparent 55%),
    radial-gradient(ellipse at 88% 12%, rgba(0, 0, 0, 0.04) 0%, transparent 45%),
    /* 主底色 — 半透明暗灰 */
    rgba(40, 42, 48, 0.72);

  /* 毛玻璃模糊效果 */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);

  /* 底部浅色半透明分割线，增强玻璃层次 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.06),
    0 4px 12px rgba(0, 0, 0, 0.25),
    0 8px 24px rgba(0, 0, 0, 0.15);
}

/* 移动端菜单打开时适当降低模糊，保证可读性 */
.app-header.menu-open {
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* ========== 头部内部布局 ========== */
.header-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-md);
  height: 64px;
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}

/* ========== Logo — 朱砂印章风格（适配暗底） ========== */
.logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
  color: #f0e6d8; /* 改为暖米白 */
  text-decoration: none;
  position: relative;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  background:
    radial-gradient(circle at 40% 35%, rgba(255, 255, 255, 0.18) 0%, transparent 60%),
    linear-gradient(135deg, #c43a31 0%, #a8322a 40%, #8b2520 100%);
  color: #fff;
  font-size: var(--fs-lg);
  font-weight: 700;
  border-radius: 3px;
  box-shadow:
    inset 0 0 0 1px rgba(0, 0, 0, 0.2),
    0 1px 3px rgba(0, 0, 0, 0.3),
    0 2px 0 rgba(100, 20, 10, 0.4);
  font-family: "STKaiti", "KaiTi", "楷体", "Noto Serif SC", serif;
  letter-spacing: 0.05em;
  transition: box-shadow 0.3s ease;
}

.logo:hover .logo-icon {
  box-shadow:
    inset 0 0 0 1px rgba(0, 0, 0, 0.25),
    0 2px 6px rgba(0, 0, 0, 0.35),
    0 3px 0 rgba(100, 20, 10, 0.45);
}

.logo-text {
  font-size: var(--fs-lg);
  font-weight: 700;
  letter-spacing: 0.08em;
  font-family: "STKaiti", "KaiTi", "楷体", "Noto Serif SC", serif;
  color: #f2e6d6;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.3);
}

/* ========== 桌面端导航 — 匾额墨韵（暗底上保留） ========== */
.nav-desktop {
  display: flex;
  align-items: center;
  gap: 4px;
  /* 深墨色背景，与暗色玻璃形成层次 */
  background:
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 3px,
      rgba(255, 255, 255, 0.008) 3px,
      rgba(255, 255, 255, 0.008) 4px
    ),
    linear-gradient(180deg, #2a221a 0%, #1f1810 40%, #140e08 100%);
  padding: 6px 20px;
  border-radius: 6px;
  box-shadow:
    0 0 0 1px rgba(200, 170, 130, 0.2),
    inset 0 0 0 1px rgba(255, 220, 180, 0.06),
    0 2px 8px rgba(0, 0, 0, 0.4),
    0 1px 0 rgba(255, 200, 150, 0.08);
  position: relative;
}

.nav-brush-line {
  position: absolute;
  bottom: -4px;
  left: 12px;
  right: 12px;
  height: 3px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.05) 8%,
    rgba(200, 180, 140, 0.3) 25%,
    rgba(200, 180, 140, 0.4) 50%,
    rgba(200, 180, 140, 0.3) 75%,
    rgba(255, 255, 255, 0.05) 92%,
    transparent 100%
  );
  border-radius: 50%;
  filter: blur(0.6px);
  pointer-events: none;
  z-index: 0;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 14px;
  font-size: var(--fs-sm);
  font-weight: 500;
  color: #efe0cc;
  border-radius: 5px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  position: relative;
  font-family: "STKaiti", "KaiTi", "楷体", "Noto Serif SC", serif;
  letter-spacing: 0.04em;
  text-decoration: none;
  z-index: 1;
}

.nav-link:hover {
  color: #ffe4b8;
  background: rgba(255, 210, 150, 0.12);
  text-shadow: 0 0 10px rgba(255, 200, 140, 0.4);
}

.nav-link::before {
  content: "";
  position: absolute;
  width: 0;
  height: 2px;
  left: 50%;
  transform: translateX(-50%);
  bottom: 2px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(220, 170, 110, 0.8) 20%,
    rgba(240, 190, 130, 0.95) 50%,
    rgba(220, 170, 110, 0.8) 80%,
    transparent
  );
  border-radius: 1px;
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  filter: blur(0.4px);
}

.nav-link:hover::before {
  width: 75%;
}

.nav-link.active {
  color: #ffe8c8;
  background: rgba(200, 80, 50, 0.25);
  text-shadow: 0 0 8px rgba(255, 180, 140, 0.35);
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 7px;
  height: 7px;
  background: linear-gradient(135deg, #d4453a, #b33028);
  border-radius: 1px;
  box-shadow:
    0 0 6px rgba(200, 60, 40, 0.6),
    0 0 0 1px rgba(255, 180, 150, 0.4);
  z-index: 2;
}

.nav-link.active::before {
  display: none;
}

.nav-icon {
  font-size: var(--fs-base);
  opacity: 0.9;
}

/* ========== 操作区域 ========== */
.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-left: auto;
}

/* ── 音乐控制按钮 ── */
.music-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.55);
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.music-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.85);
  border-color: rgba(255, 255, 255, 0.3);
}

.music-toggle-btn--playing {
  background: rgba(200, 80, 50, 0.25);
  border-color: rgba(220, 120, 80, 0.4);
  color: #ffe0cc;
}

.music-toggle-btn--playing:hover {
  background: rgba(200, 80, 50, 0.4);
  border-color: rgba(220, 120, 80, 0.6);
  color: #fff;
  box-shadow: 0 0 12px rgba(200, 80, 50, 0.3);
}

.user-area {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.user-avatar-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 4px 10px;
  border: none;
  background: rgba(255, 255, 255, 0.08);
  color: #efe0cc;
  font-size: var(--fs-sm);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.15);
  font-family: "STKaiti", "KaiTi", "楷体", "Noto Serif SC", serif;
}

.user-avatar-btn:hover {
  background: rgba(255, 255, 255, 0.14);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
  color: #fff;
}

.user-nickname {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: 0.03em;
}

.arrow-icon {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  transition: transform 0.3s ease;
}

.user-avatar-btn:hover .arrow-icon {
  color: rgba(255, 255, 255, 0.8);
}

/* ========== 登录/注册标签按钮 ========== */
.btn-text {
  padding: 4px 12px;
  font-size: 0.78rem;
  font-weight: 500;
  color: #d0c8b8;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  transition: all 0.25s ease;
  text-decoration: none;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.btn-text:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.btn-primary-sm {
  padding: 4px 12px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #c94038 0%, #b03028 50%, #962118 100%);
  border: 1px solid rgba(200, 80, 50, 0.4);
  border-radius: 6px;
  text-decoration: none;
  transition: all 0.25s ease;
  letter-spacing: 0.03em;
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.btn-primary-sm:hover {
  background: linear-gradient(135deg, #d44a40 0%, #b8352c 50%, #a02820 100%);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  transform: translateY(-1px);
}

.btn-primary-sm:active {
  transform: translateY(0);
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.3);
}

/* ========== 移动端菜单按钮 ========== */
.mobile-menu-btn {
  display: none;
  border: none;
  background: rgba(255, 255, 255, 0.08);
  color: #efe0cc;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12);
}

.mobile-menu-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

/* ========== 移动端抽屉 — 同样暗色玻璃风格 ========== */
.nav-mobile {
  display: none;
  flex-direction: column;
  padding: var(--space-md) var(--space-md) var(--space-lg);
  background:
    repeating-linear-gradient(
      180deg,
      transparent,
      transparent 1px,
      rgba(255, 255, 255, 0.015) 1px,
      rgba(255, 255, 255, 0.015) 2px
    ),
    rgba(30, 32, 36, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  max-height: calc(100vh - 64px);
  overflow-y: auto;
  position: relative;
  box-shadow:
    inset 0 2px 12px rgba(0, 0, 0, 0.2),
    0 4px 20px rgba(0, 0, 0, 0.3);
}

.mobile-ink-decoration {
  width: 100%;
  height: 4px;
  margin-bottom: var(--space-sm);
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.05) 10%,
    rgba(200, 180, 140, 0.25) 30%,
    rgba(200, 180, 140, 0.35) 50%,
    rgba(200, 180, 140, 0.25) 70%,
    rgba(255, 255, 255, 0.05) 90%,
    transparent 100%
  );
  border-radius: 50%;
  filter: blur(0.8px);
}

.nav-mobile .nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  font-size: var(--fs-base);
  font-weight: 500;
  color: #e0d3c0;
  border-radius: 8px;
  transition: all 0.3s ease;
  font-family: "STKaiti", "KaiTi", "楷体", "Noto Serif SC", serif;
  letter-spacing: 0.05em;
  text-decoration: none;
  position: relative;
}

.nav-mobile .nav-link:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav-mobile .nav-link.router-link-exact-active,
.nav-mobile .nav-link.active {
  color: #f0c0a0;
  background: rgba(200, 80, 50, 0.2);
  font-weight: 600;
  box-shadow: inset 4px 0 0 #c94038;
}

.mobile-auth {
  display: flex;
  gap: var(--space-sm);
  padding-top: var(--space-md);
  margin-top: var(--space-sm);
  position: relative;
}

.mobile-auth::before {
  content: '';
  position: absolute;
  top: 0;
  left: 8px;
  right: 8px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.15) 20%,
    rgba(255, 255, 255, 0.15) 80%,
    transparent
  );
}

/* ========== 过渡动画 ========== */
.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: opacity 0.3s ease, transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.drawer-slide-enter-from,
.drawer-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

/* ========== 响应式 ========== */
@media (max-width: 1023px) {
  .nav-desktop { display: none; }
  .mobile-menu-btn { display: flex; }
  .nav-mobile { display: flex; }
  .logo-text { display: inline; }
}

@media (max-width: 767px) {
  .header-inner {
    height: 56px;
    padding: 0 var(--space-sm);
    gap: var(--space-sm);
  }
  .logo-text { display: none; }
  .logo-icon {
    width: 34px;
    height: 34px;
    font-size: var(--fs-base);
  }
  .header-actions { gap: var(--space-xs); }
  .user-nickname { display: none; }
  .user-avatar-btn { padding: 4px 6px; }
  .btn-text { padding: 3px 10px; font-size: 0.72rem; }
  .btn-primary-sm { padding: 3px 10px; font-size: 0.72rem; }
  .nav-mobile {
    max-height: calc(100vh - 56px);
    padding: var(--space-sm);
  }
  .nav-mobile .nav-link {
    padding: 10px 14px;
    font-size: 0.95rem;
  }
}

@media (max-width: 380px) {
  .header-inner { gap: 6px; }
  .btn-text, .btn-primary-sm {
    padding: 3px 8px;
    font-size: 0.7rem;
    letter-spacing: 0.02em;
  }
  .logo-icon {
    width: 30px;
    height: 30px;
    font-size: 0.9rem;
  }
}
</style>
