<template>
  <div class="food-detail-page">
    <BackButton />
    <!-- 加载中 -->
    <LoadingSkeleton v-if="loading" type="detail" />

    <!-- 错误 -->
    <div v-else-if="error" class="error-state">
      <el-result icon="error" :title="error" sub-title="请检查网络连接后重试">
        <template #extra>
          <el-button type="primary" @click="fetchDetail">重新加载</el-button>
          <el-button @click="$router.back()">返回</el-button>
        </template>
      </el-result>
    </div>

    <!-- 内容 -->
    <template v-else-if="food">
      <!-- 图片区域 -->
      <div class="hero-image" @click="food.image_url && viewer.open([food.image_url])">
        <el-image v-if="food.image_url" :src="food.image_url" fit="cover" class="cover-img" />
        <div v-else class="cover-placeholder">🍲</div>
        <div class="hero-overlay">
          <el-tag v-if="food.is_recommended" type="danger" effect="dark">🔥 推荐</el-tag>
          <span class="type-badge">{{ food.type === 'shop' ? '店铺' : '菜品' }}</span>
        </div>
      </div>
      <ImageViewer ref="viewer" />

      <!-- 基本信息 -->
      <div class="info-section">
        <div class="info-header">
          <div>
            <h1 class="display-text--section">{{ food.name }}</h1>
            <div class="info-meta">
              <span class="category">{{ food.category_name }}</span>
              <span
                v-if="food.price_range"
                class="price"
              >{{ food.type === 'shop' ? '人均: ' : '均价: ' }}{{ food.price_range }}</span>
              <span v-else class="price price--muted">暂无相关信息</span>
              <span class="rating" v-if="food.rating">⭐ {{ food.rating.toFixed(1) }} 分</span>
              <span class="views">👀 {{ food.view_count }} 次浏览</span>
            </div>
          </div>
          <el-button
            :type="isFavorited ? 'danger' : 'default'"
            :icon="isFavorited ? StarFilled : Star"
            round
            @click="toggleFavorite"
          >
            {{ isFavorited ? '已收藏' : '收藏' }}
          </el-button>
        </div>

        <!-- 描述 -->
        <div class="desc-block">
          <h3>📝 介绍</h3>
          <p>{{ food.description || '暂无详细介绍' }}</p>
        </div>

        <!-- 标签 -->
        <div v-if="food.tags && food.tags.length" class="tags-block">
          <h3>🏷️ 标签</h3>
          <div class="tag-list">
            <el-tag v-for="tag in food.tags" :key="tag" round>{{ tag }}</el-tag>
          </div>
        </div>

        <!-- 地址信息 -->
        <div v-if="food.address" class="address-block">
          <h3>📍 地址</h3>
          <p>{{ food.address }}</p>
        </div>
      </div>

      <!-- AI 推荐相关美食 -->
      <div class="recommend-section">
        <div class="section-divider section-divider--left"></div>
        <h3>🤖 AI 相关推荐</h3>
        <p class="section-desc">根据您的浏览，智能推荐以下美食</p>
        <div v-if="relatedFoods.length" class="related-grid">
          <FoodCard
            v-for="item in relatedFoods"
            :key="item.id"
            :food="item"
            @click="$router.push(`/foods/${item.id}`)"
          />
        </div>
        <div v-else-if="!loadingRelated" class="no-related">
          <p>暂无相关推荐</p>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'
import { getFoodDetail, getFoods, addFavorite, removeFavorite } from '@/api'
import FoodCard from '@/components/business/FoodCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ImageViewer from '@/components/common/ImageViewer.vue'
import BackButton from '@/components/common/BackButton.vue'

const route = useRoute()

const viewer = ref(null)
const food = ref(null)
const loading = ref(true)
const error = ref('')
const isFavorited = ref(false)
const relatedFoods = ref([])
const loadingRelated = ref(true)

async function fetchDetail() {
  loading.value = true
  error.value = ''
  try {
    const id = route.params.id
    food.value = await getFoodDetail(id)
    document.title = `${food.value.name} - 潮汕文化宣传平台`

    // 获取相关推荐
    fetchRelated(food.value.category_id, food.value.id)
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function fetchRelated(categoryId, excludeId) {
  loadingRelated.value = true
  try {
    const data = await getFoods({ category_id: categoryId, page_size: 4 })
    relatedFoods.value = (data.items || []).filter(f => f.id !== Number(excludeId)).slice(0, 3)
  } catch {
    relatedFoods.value = []
  } finally {
    loadingRelated.value = false
  }
}

async function toggleFavorite() {
  try {
    if (isFavorited.value) {
      await removeFavorite(food.value.id)
      isFavorited.value = false
      ElMessage.success('已取消收藏')
    } else {
      await addFavorite({ item_type: 'food', item_id: food.value.id })
      isFavorited.value = true
      ElMessage.success('已收藏')
    }
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

onMounted(() => fetchDetail())
</script>

<style scoped>
.food-detail-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 var(--space-md) var(--space-3xl);
}

.hero-image {
  position: relative;
  width: 100%;
  height: 400px;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: var(--space-2xl);
}

/* 底部渐变叠层 — 让标题区更有层次 */
.hero-image::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: var(--gradient-card-overlay);
  pointer-events: none;
  z-index: 1;
}

.cover-img {
  width: 100%;
  height: 100%;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface);
  font-size: 64px;
}

.hero-overlay {
  position: absolute;
  top: var(--space-md);
  right: var(--space-md);
  display: flex;
  gap: var(--space-sm);
  z-index: 2;
}

.type-badge {
  background: oklch(0 0 0 / 0.6);
  color: #fff;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: var(--fs-sm);
}

/* Info */
.info-section {
  margin-bottom: var(--space-2xl);
}

.info-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
}

.info-header h1 {
  font-size: var(--fs-3xl);
  color: var(--ink);
  margin: 0 0 var(--space-sm);
}

.info-meta {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  color: var(--muted);
  font-size: var(--fs-sm);
}

.price {
  color: var(--accent);
  font-weight: 600;
}

.price--muted {
  color: var(--text-muted);
  font-weight: var(--fw-normal);
}

.rating {
  color: var(--brand-amber);
  font-weight: var(--fw-medium);
}

.desc-block,
.tags-block,
.address-block {
  margin-bottom: var(--space-xl);
}

.desc-block h3,
.tags-block h3,
.address-block h3 {
  font-size: var(--fs-base);
  color: var(--ink);
  margin: 0 0 var(--space-sm);
}

.desc-block p,
.address-block p {
  color: var(--muted);
  line-height: 1.8;
  margin: 0;
}

.tag-list {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

/* Related */
.recommend-section {
  padding-top: var(--space-md);
}

.recommend-section .section-divider {
  margin-bottom: var(--space-lg);
}

.recommend-section h3 {
  font-size: var(--fs-xl);
  color: var(--ink);
  margin: 0 0 var(--space-xs);
}

.section-desc {
  color: var(--muted);
  font-size: var(--fs-sm);
  margin: 0 0 var(--space-xl);
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-lg);
}

.no-related {
  text-align: center;
  color: var(--muted);
  padding: var(--space-2xl);
}

.error-state {
  padding: var(--space-3xl);
}

@media (max-width: 640px) {
  .hero-image {
    height: 240px;
    border-radius: 0;
    margin: 0 calc(-1 * var(--space-md)) var(--space-xl);
  }

  .info-header {
    flex-direction: column;
  }

  .info-header h1 {
    font-size: var(--fs-2xl);
  }
}
</style>
