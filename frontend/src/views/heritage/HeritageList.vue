<template>
  <div class="heritage-list-page">
    <BackButton />
    <!-- 页面标题 · 不对称左对齐 -->
    <div class="page-hero">
      <h1 class="display-text--section">🎭 非遗民俗</h1>
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
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

onMounted(() => fetchData())
</script>

<style scoped>
.heritage-list-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-md);
}

.page-hero {
  text-align: left;
  padding: var(--space-2xl) 0;
}

.page-hero h1 {
  font-size: var(--fs-3xl);
  color: var(--ink);
  margin: 0 0 var(--space-sm);
}

.page-hero p {
  color: var(--muted);
  font-size: var(--fs-base);
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
