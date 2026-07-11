<template>
  <div class="food-list-page">
    <BackButton />
    <!-- 页面标题 · 不对称左对齐 -->
    <div class="page-hero">
      <h1 class="display-text--section">🍲 潮汕美食</h1>
      <p>从街头小吃到老字号，品味最地道的潮汕味道</p>
      <div class="section-divider section-divider--left"></div>
    </div>

    <!-- 分类筛选 — 茶渍按钮 -->
    <div class="category-bar">
      <button
        :class="['tea-pill', { active: !activeCategory }]"
        @click="activeCategory = null; fetchFoods()"
      >
        全部
      </button>
      <button
        v-for="cat in categories"
        :key="cat.id"
        :class="['tea-pill', { active: activeCategory === cat.id }]"
        @click="activeCategory = cat.id; fetchFoods()"
      >
        {{ cat.icon }} {{ cat.name }}
      </button>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="搜索美食..."
        :prefix-icon="Search"
        clearable
        class="search-input"
        @keyup.enter="fetchFoods"
        @clear="fetchFoods"
      />
      <div class="toolbar-actions">
        <el-select v-model="foodType" placeholder="类型" clearable style="width:120px" @change="fetchFoods">
          <el-option label="菜品" value="dish" />
          <el-option label="店铺" value="shop" />
        </el-select>
        <el-select v-model="sort" style="width:130px" @change="fetchFoods">
          <el-option label="🔥 最热门" value="view_count" />
          <el-option label="🕐 最新" value="created_at" />
          <el-option label="💰 价格" value="price_range" />
        </el-select>
      </div>
    </div>

    <!-- 加载中 -->
    <LoadingSkeleton v-if="loading" type="card" :count="8" />

    <!-- 空状态 -->
    <EmptyState v-else-if="!loading && foods.length === 0" description="暂无美食数据" />

    <!-- 美食瀑布流 — 韩信点兵 -->
    <div v-else class="masonry-container">
      <FoodCard
        v-for="food in foods"
        :key="food.id"
        :food="food"
        @click="$router.push(`/foods/${food.id}`)"
      />
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        background
        @current-change="fetchFoods"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getFoods, getFoodCategories } from '@/api'
import FoodCard from '@/components/business/FoodCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import BackButton from '@/components/common/BackButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const loading = ref(true)
const foods = ref([])
const categories = ref([])
const activeCategory = ref(null)
const keyword = ref('')
const foodType = ref('')
const sort = ref('view_count')
const page = ref(1)
const pageSize = 20
const total = ref(0)

async function fetchFoods() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize,
      sort: sort.value,
    }
    if (activeCategory.value) params.category_id = activeCategory.value
    if (keyword.value) params.keyword = keyword.value
    if (foodType.value) params.type = foodType.value

    const data = await getFoods(params)
    foods.value = data.items || []
    total.value = data.total || 0
  } catch {
    foods.value = []
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  try {
    const data = await getFoodCategories()
    categories.value = data || []
  } catch { /* 静默失败 */ }
}

onMounted(() => {
  fetchCategories()
  fetchFoods()
})
</script>

<style scoped>
.food-list-page {
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

.category-bar {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-xl);
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-surface-alt);
  border-radius: var(--radius-lg);
}

.toolbar {
  display: flex;
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.search-input {
  flex: 1;
  max-width: 360px;
}

.toolbar-actions {
  display: flex;
  gap: var(--space-sm);
  margin-left: auto;
}

/* Masonry is provided by global .masonry-container */

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: var(--space-2xl);
  padding-top: var(--space-xl);
}

@media (max-width: 639px) {
  .toolbar {
    flex-direction: column;
  }
  .search-input {
    max-width: none;
  }
  .toolbar-actions {
    margin-left: 0;
  }
}
</style>
