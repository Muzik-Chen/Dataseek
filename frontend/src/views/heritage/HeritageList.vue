<template>
  <div class="heritage-list-page">
    <!-- 背景轮播 -->
    <div class="bg-carousel">
      <img
        v-for="(bg, i) in bgImages"
        :key="i"
        :src="bg"
        class="bg-slide"
        :class="{ active: currentBg === i }"
        alt=""
      />
      <div class="bg-overlay" />
    </div>

    <div class="content-box">
      <BackButton />
    <!-- 页面标题 · 不对称左对齐 -->
    <div class="page-hero">
      <h1 class="display-text--section">非遗文化</h1>
      <p>探索潮汕千年传承的非物质文化遗产</p>
      <div class="section-divider section-divider--left"></div>
    </div>

    <!-- 筛选 + 排序 -->
    <div class="filter-bar">
      <div class="filter-row">
        <span class="filter-label">级别</span>
        <button
          :class="['tea-pill', { active: !filterCategory }]"
          @click="filterCategory = ''; fetchData()"
        >全部</button>
        <button
          v-for="lv in levels"
          :key="lv"
          :class="['tea-pill', { active: filterCategory === lv }]"
          @click="filterCategory = lv; fetchData()"
        >{{ lv }}</button>
      </div>
      <div class="filter-row">
        <span class="filter-label">类型</span>
        <button
          :class="['tea-pill', { active: !filterType }]"
          @click="filterType = ''; fetchData()"
        >全部</button>
        <button
          v-for="t in types"
          :key="t"
          :class="['tea-pill', { active: filterType === t }]"
          @click="filterType = t; fetchData()"
        >{{ t }}</button>
      </div>
      <div class="search-row">
        <el-input
          v-model="keyword"
          placeholder="搜索非遗项目..."
          :prefix-icon="Search"
          clearable
          class="search-inline"
          @keyup.enter="fetchData"
          @clear="fetchData"
        />
        <SortDropdown v-model="sort" :options="sortOptions" width="150px" @change="fetchData" />
      </div>
    </div>

    <!-- 加载中 -->
    <LoadingSkeleton v-if="loading" type="card" :count="6" />

    <!-- 空 -->
    <EmptyState v-else-if="!loading && items.length === 0" description="暂无非遗项目" />

    <!-- 非遗瀑布流 -->
    <div v-else class="masonry-container">
      <HeritageCard
        v-for="item in items"
        :key="item.id"
        :item="item"
        @favorite="handleFavorite"
      />
    </div>

    <!-- 分页 -->
    <Pagination
      v-model:page="page"
      :total="total"
      :page-size="pageSize"
      @change="fetchData"
    />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getHeritages, addFavorite, removeFavorite } from '@/api'
import { useUserStore } from '@/stores/user'
import HeritageCard from '@/components/business/HeritageCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import Pagination from '@/components/common/Pagination.vue'
import SortDropdown from '@/components/common/SortDropdown.vue'
import BackButton from '@/components/common/BackButton.vue'

const router = useRouter()
const userStore = useUserStore()

// 背景轮播
const bgImages = [
  '/images/events/非遗bg3.jpg',
  '/images/events/非遗bg1.jpg',
  '/images/events/非遗bg2.jpg',
]
const currentBg = ref(0)
let bgTimer = null

function startBgCarousel() {
  bgTimer = setInterval(() => {
    currentBg.value = (currentBg.value + 1) % bgImages.length
  }, 5000)
}

const loading = ref(true)
const items = ref([])
const filterCategory = ref('')
const filterType = ref('')
const keyword = ref('')
const sort = ref('created_at')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const levels = ['国家级', '省级', '市级']
const types = ['传统戏剧', '传统舞蹈', '传统美术', '传统技艺', '民俗', '传统音乐']

const sortOptions = [
  { label: '🕐 最新', value: 'created_at' },
  { label: '📛 名称', value: 'name' },
  { label: '🏛 级别', value: 'category' },
]

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize, sort: sort.value }
    if (filterCategory.value) params.category = filterCategory.value
    if (filterType.value) params.type = filterType.value
    if (keyword.value) params.keyword = keyword.value

    const data = await getHeritages(params)
    items.value = data.items || []
    total.value = data.total || 0
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

async function handleFavorite(item) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再收藏')
    router.push('/login')
    return
  }
  try {
    await addFavorite({ item_type: 'heritage', item_id: item.id })
    ElMessage.success('已收藏')
  } catch (e) {
    ElMessage.error(e.message || '收藏失败')
  }
}

onMounted(() => {
  fetchData()
  startBgCarousel()
  document.body.classList.add('heritage-list-open')
})

onBeforeUnmount(() => {
  clearInterval(bgTimer)
  document.body.classList.remove('heritage-list-open')
})
</script>

<style scoped>
/* ---- 背景轮播 ---- */
.bg-carousel {
  position: fixed;
  inset: 0;
  z-index: -1;
}

.bg-slide {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 1.5s ease;
}

.bg-slide.active {
  opacity: 1;
}

.bg-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0.35) 0%,
    rgba(0, 0, 0, 0.1) 50%,
    rgba(0, 0, 0, 0.35) 100%
  );
  pointer-events: none;
}

.heritage-list-page {
  position: relative;
  z-index: 1;
  min-height: 100vh;
}

.content-box {
  margin: 50px 100px;
  padding: var(--space-2xl) var(--space-md);
  background: rgba(255, 255, 255, 0.45);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(4px);
}

@media (max-width: 640px) {
  .content-box {
    margin: 16px 12px;
    padding: var(--space-lg) var(--space-sm);
  }
  .page-hero h1 {
    font-size: 32px;
  }
}

.page-hero {
  text-align: left;
  padding: var(--space-2xl) 0;
}

.page-hero h1 {
  font-size: 64px;
  color: var(--ink);
  margin: 0 0 var(--space-sm);
}

.page-hero p {
  color: var(--muted);
  font-size: 1.5rem;
  margin: 0 0 var(--space-md);
}

.filter-bar {
  background: var(--bg-surface-alt);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  margin-bottom: var(--space-xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.filter-label {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--ink);
  min-width: 48px;
}

.search-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.search-inline {
  max-width: 320px;
}

/* Masonry is provided by global .masonry-container */
</style>

<style>
body.heritage-list-open,
body.heritage-list-open #app {
  background: transparent !important;
}
</style>
