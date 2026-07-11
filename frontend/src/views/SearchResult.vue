<template>
  <div class="search-page">
    <BackButton />

    <div class="search-header">
      <div class="search-bar-wrap">
        <el-input
          v-model="keyword"
          placeholder="搜索潮汕美食、非遗、景点、民俗..."
          :prefix-icon="Search"
          size="large"
          clearable
          @keyup.enter="doSearch"
          @clear="doSearch"
        >
          <template #append>
            <el-button :icon="Search" :loading="loading" @click="doSearch">搜索</el-button>
          </template>
        </el-input>
      </div>
      <p v-if="searchedKeyword" class="search-meta">
        关于「{{ searchedKeyword }}」的搜索结果，共 {{ totalResults }} 条
      </p>
      <div class="section-divider section-divider--left"></div>
    </div>

    <!-- 筛选标签 -->
    <div class="filter-tabs">
      <button
        v-for="tab in filterTabs"
        :key="tab.key"
        :class="['tea-pill', { active: activeFilter === tab.key }]"
        @click="activeFilter = tab.key"
      >
        {{ tab.label }}
        <span v-if="counts[tab.key]" class="count">{{ counts[tab.key] }}</span>
      </button>
    </div>

    <!-- 加载中 -->
    <LoadingSkeleton v-if="loading" type="list" :count="5" />

    <!-- 空状态 -->
    <EmptyState
      v-else-if="!loading && searchedKeyword && totalResults === 0"
      description="没有找到相关内容，试试其他关键词"
    >
      <template #action>
        <div class="search-suggestions">
          <p>热门搜索：</p>
          <el-button v-for="t in hotTags" :key="t" size="small" round @click="keyword = t; doSearch()">
            {{ t }}
          </el-button>
        </div>
      </template>
    </EmptyState>

    <!-- 结果列表 -->
    <div v-else class="search-results">
      <!-- 美食 -->
      <template v-if="activeFilter === 'all' || activeFilter === 'food'">
        <div v-if="foodResults.length" class="result-section">
          <h3>🍲 美食</h3>
          <div class="masonry-container">
            <div
              v-for="item in foodResults"
              :key="'food-' + item.id"
              class="result-card"
              @click="$router.push(`/foods/${item.id}`)"
            >
              <el-image :src="item.image_url" fit="cover" class="result-img">
                <template #error><div class="img-placeholder">🍲</div></template>
              </el-image>
              <div class="result-body">
                <h4>{{ item.name }}</h4>
                <p class="result-desc">{{ item.description?.slice(0, 80) || '暂无描述' }}</p>
                <div class="result-meta">
                  <span>{{ item.category_name }}</span>
                  <span v-if="item.price_range">{{ item.price_range }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 非遗 -->
      <template v-if="activeFilter === 'all' || activeFilter === 'heritage'">
        <div v-if="heritageResults.length" class="result-section">
          <h3>🎭 非遗</h3>
          <div class="masonry-container">
            <div
              v-for="item in heritageResults"
              :key="'h-' + item.id"
              class="result-card"
              @click="$router.push(`/heritages/${item.id}`)"
            >
              <el-image :src="item.image_url" fit="cover" class="result-img">
                <template #error><div class="img-placeholder">🎭</div></template>
              </el-image>
              <div class="result-body">
                <h4>{{ item.name }}</h4>
                <p class="result-desc">{{ item.description?.slice(0, 80) || '暂无描述' }}</p>
                <div class="result-meta">
                  <el-tag :type="levelTag(item.category)" size="small">{{ item.category }}</el-tag>
                  <span>{{ item.region }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 活动 -->
      <template v-if="activeFilter === 'all' || activeFilter === 'event'">
        <div v-if="eventResults.length" class="result-section">
          <h3>🎊 民俗活动</h3>
          <div class="masonry-container">
            <div
              v-for="item in eventResults"
              :key="'e-' + item.id"
              class="result-card"
              @click="$router.push('/festival')"
            >
              <el-image :src="item.image_url" fit="cover" class="result-img">
                <template #error><div class="img-placeholder">🎊</div></template>
              </el-image>
              <div class="result-body">
                <h4>{{ item.name }}</h4>
                <p class="result-desc">{{ item.description?.slice(0, 80) || '暂无描述' }}</p>
                <div class="result-meta">
                  <span>{{ item.event_date }}</span>
                  <span>{{ item.region }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getFoods, getHeritages, getEvents } from '@/api'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BackButton from '@/components/common/BackButton.vue'

const keyword = ref('')
const searchedKeyword = ref('')
const loading = ref(false)
const activeFilter = ref('all')

const foodResults = ref([])
const heritageResults = ref([])
const eventResults = ref([])

const counts = reactive({ all: 0, food: 0, heritage: 0, event: 0 })

const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'food', label: '美食' },
  { key: 'heritage', label: '非遗' },
  { key: 'event', label: '民俗' },
]

const hotTags = ['牛肉火锅', '英歌舞', '工夫茶', '肠粉', '广济桥', '南澳岛']

const totalResults = computed(() => counts.all)

function levelTag(level) {
  if (level === '国家级') return 'danger'
  if (level === '省级') return 'primary'
  return 'success'
}

async function doSearch() {
  const kw = keyword.value.trim()
  if (!kw) return

  searchedKeyword.value = kw
  loading.value = true

  try {
    const [foodData, heritageData, eventData] = await Promise.all([
      getFoods({ keyword: kw, page_size: 20 }),
      getHeritages({ keyword: kw, page_size: 20 }),
      getEvents({ keyword: kw, page_size: 20 }),
    ])

    foodResults.value = foodData?.items || []
    heritageResults.value = heritageData?.items || []
    eventResults.value = eventData?.items || []

    counts.all = foodResults.value.length + heritageResults.value.length + eventResults.value.length
    counts.food = foodResults.value.length
    counts.heritage = heritageResults.value.length
    counts.event = eventResults.value.length
  } catch {
    // 搜索失败静默处理
    foodResults.value = []
    heritageResults.value = []
    eventResults.value = []
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.search-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-md);
}

.search-header {
  margin-bottom: var(--space-xl);
}

.search-bar-wrap {
  max-width: 640px;
}

.search-meta {
  color: var(--muted);
  font-size: var(--fs-sm);
  margin: var(--space-md) 0 var(--space-md);
}

.search-header .section-divider {
  margin-top: var(--space-sm);
}

.filter-tabs {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: var(--space-xl);
  flex-wrap: wrap;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-surface-alt);
  border-radius: var(--radius-lg);
}

/* tea-pill from global.css — keep .count override */
.tea-pill .count {
  font-size: var(--fs-xs);
  opacity: 0.7;
}

.result-section {
  margin-bottom: var(--space-2xl);
}

.result-section h3 {
  font-size: var(--fs-lg);
  color: var(--text-primary);
  margin: 0 0 var(--space-lg);
}

/* masonry from global.css */

.result-card {
  background: var(--surface);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.04);
}

.result-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px oklch(0 0 0 / 0.08);
}

.result-img {
  width: 100%;
  height: 160px;
}

.img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface);
  font-size: 32px;
}

.result-body {
  padding: var(--space-md);
}

.result-body h4 {
  font-size: var(--fs-base);
  color: var(--ink);
  margin: 0 0 var(--space-xs);
}

.result-desc {
  color: var(--muted);
  font-size: var(--fs-sm);
  margin: 0 0 var(--space-sm);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--fs-xs);
  color: var(--muted);
}

.search-suggestions {
  margin-top: var(--space-md);
}

.search-suggestions p {
  color: var(--muted);
  margin-bottom: var(--space-sm);
}

.search-suggestions .el-button {
  margin: 4px;
}
</style>
