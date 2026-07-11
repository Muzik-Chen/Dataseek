<template>
  <div class="heritage-detail-page">
    <LoadingSkeleton v-if="loading" type="detail" />

    <div v-else-if="error" class="error-state">
      <el-result icon="error" :title="error" sub-title="请重试">
        <template #extra>
          <el-button type="primary" @click="fetchDetail">重新加载</el-button>
          <el-button @click="$router.back()">返回</el-button>
        </template>
      </el-result>
    </div>

    <template v-else-if="heritage">
      <!-- 返回导航 -->
      <div class="back-nav">
        <el-button text @click="$router.push('/heritages')">
          <el-icon><ArrowLeft /></el-icon> 返回非遗列表
        </el-button>
      </div>

      <!-- Zone 1: 标题 + 传承人卡片 + 标签 -->
      <div class="zone-header">
        <div class="header-left">
          <h1 class="heritage-title">{{ heritage.name }}</h1>
          <div class="meta-line">
            <span class="level-tag" :class="levelClass">{{ heritage.category }}</span>
            <span class="type-tag">{{ heritage.type }}</span>
            <span class="region">📍 {{ heritage.region }}</span>
            <span class="views">👀 {{ heritage.view_count }} 次浏览</span>
          </div>
        </div>
        <div class="header-right">
          <div v-if="heritage.inheritor" class="inheritor-card">
            <span class="inheritor-icon">🧑‍🎓</span>
            <div class="inheritor-info">
              <span class="inheritor-name">{{ heritage.inheritor }}</span>
              <span class="inheritor-label">代表性传承人</span>
            </div>
          </div>
          <el-button
            :type="isFavorited ? 'danger' : 'default'"
            :icon="isFavorited ? StarFilled : Star"
            round
            class="fav-btn"
            @click="toggleFavorite"
          >
            {{ isFavorited ? '已收藏' : '收藏' }}
          </el-button>
        </div>
      </div>

      <!-- Zone 2: 左图右文 -->
      <div class="zone-content">
        <div class="content-left">
          <div class="image-card" @click="heritage.image_url && viewer.open([heritage.image_url])">
            <el-image v-if="heritage.image_url" :src="heritage.image_url" fit="cover" class="main-img" />
            <div v-else class="img-placeholder">🎭</div>
            <div v-if="heritage.image_url" class="img-overlay">
              <el-icon :size="24"><ZoomIn /></el-icon>
              <span>点击放大</span>
            </div>
          </div>
          <!-- 非遗印章 -->
          <div class="seal-badge" aria-hidden="true">
            <span>非遗<br>传承</span>
          </div>
        </div>

        <div class="content-right">
          <section class="desc-block">
            <h2>📖 项目介绍</h2>
            <p>{{ heritage.description || '暂无详细介绍' }}</p>
          </section>

          <section class="detail-block">
            <h2>📋 详细信息</h2>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">保护级别</span>
                <span class="detail-value">{{ heritage.category }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">项目类型</span>
                <span class="detail-value">{{ heritage.type }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">所属地区</span>
                <span class="detail-value">{{ heritage.region }}</span>
              </div>
            </div>
          </section>
        </div>
      </div>

      <ImageViewer ref="viewer" />

      <!-- Zone 3: 视频 -->
      <section v-if="heritage.video_url" class="zone-video">
        <h2>🎬 视频资料</h2>
        <div class="video-wrap">
          <video :src="heritage.video_url" controls class="heritage-video">
            您的浏览器不支持视频播放
          </video>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, StarFilled, ArrowLeft, ZoomIn } from '@element-plus/icons-vue'
import { getHeritageDetail, addFavorite, removeFavorite, checkFavorite } from '@/api'
import { useUserStore } from '@/stores/user'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ImageViewer from '@/components/common/ImageViewer.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const viewer = ref(null)
const heritage = ref(null)
const loading = ref(true)
const error = ref('')
const isFavorited = ref(false)
const favoriteId = ref(null)

const levelClass = computed(() => {
  const cat = heritage.value?.category || ''
  if (cat.includes('国家')) return 'national'
  if (cat.includes('省级')) return 'province'
  if (cat.includes('市级')) return 'city'
  return 'default'
})

async function fetchDetail() {
  loading.value = true
  error.value = ''
  try {
    heritage.value = await getHeritageDetail(route.params.id)
    document.title = `${heritage.value.name} - 潮汕文化宣传平台`
    if (userStore.isLoggedIn) {
      await checkFavoriteStatus()
    }
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function checkFavoriteStatus() {
  try {
    const res = await checkFavorite({ item_type: 'heritage', item_id: heritage.value.id })
    isFavorited.value = res.is_favorited
    favoriteId.value = res.favorite_id
  } catch { /* ignore */ }
}

async function toggleFavorite() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再收藏')
    router.push('/login')
    return
  }
  try {
    if (isFavorited.value) {
      await removeFavorite(favoriteId.value)
      isFavorited.value = false
      favoriteId.value = null
      ElMessage.success('已取消收藏')
    } else {
      const res = await addFavorite({ item_type: 'heritage', item_id: heritage.value.id })
      isFavorited.value = true
      favoriteId.value = res.id
      ElMessage.success('已收藏')
    }
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

onMounted(() => fetchDetail())
</script>

<style scoped>
.heritage-detail-page {
  max-width: var(--content-wide, 1200px);
  margin: 0 auto;
  padding: var(--space-lg) var(--space-md) var(--space-xl);
}

/* ---- 返回导航 ---- */
.back-nav {
  margin-bottom: var(--space-lg);
}

/* ---- Zone 1: 标题区 ---- */
.zone-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-xl);
  margin-bottom: var(--space-2xl);
  padding-bottom: var(--space-xl);
  border-bottom: 1px solid oklch(0 0 0 / 0.08);
}

.header-left {
  flex: 1;
  min-width: 0;
}

.heritage-title {
  font-family: var(--font-display);
  font-size: var(--fs-3xl);
  font-weight: var(--fw-black);
  color: var(--ink);
  margin: 0 0 var(--space-md);
  line-height: 1.3;
}

.meta-line {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.level-tag {
  font-size: var(--fs-xs);
  font-weight: var(--fw-semibold);
  padding: 2px 10px;
  border-radius: var(--radius-full);
  color: var(--status-error);
  background: var(--status-error-bg);
}
.level-tag.province {
  color: var(--brand-amber, #b45309);
  background: var(--brand-amber-wash, #fef3c7);
}
.level-tag.city {
  color: var(--brand-green, #166534);
  background: var(--brand-green-wash, #dcfce7);
}
.level-tag.default {
  color: var(--text-muted);
  background: var(--bg-surface-alt);
}

.type-tag {
  color: var(--text-muted);
  font-size: var(--fs-sm);
  padding: 2px 10px;
  border-radius: var(--radius-full);
  background: var(--bg-surface-alt);
}

.region, .views {
  color: var(--text-muted);
  font-size: var(--fs-sm);
}

/* 传承人卡片 */
.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--space-md);
  flex-shrink: 0;
}

.inheritor-card {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--brand-amber-wash, #fef3c7);
  border-left: 3px solid var(--brand-amber, #b45309);
  border-radius: var(--radius-md);
}

.inheritor-icon {
  font-size: 24px;
}

.inheritor-info {
  display: flex;
  flex-direction: column;
}

.inheritor-name {
  font-weight: var(--fw-semibold);
  color: var(--ink);
  font-size: var(--fs-base);
}

.inheritor-label {
  font-size: var(--fs-xs);
  color: var(--text-muted);
}

.fav-btn {
  flex-shrink: 0;
}

/* ---- Zone 2: 左图右文 ---- */
.zone-content {
  display: flex;
  gap: var(--space-2xl);
  margin-bottom: var(--space-3xl);
}

.content-left {
  position: relative;
  width: 380px;
  flex-shrink: 0;
}

.image-card {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.image-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.main-img {
  width: 100%;
  height: 320px;
  display: block;
}

.img-placeholder {
  width: 100%;
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-surface);
  font-size: 48px;
}

.img-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: var(--space-md);
  background: linear-gradient(transparent, rgba(0,0,0,0.55));
  color: #fff;
  font-size: var(--fs-sm);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-card:hover .img-overlay {
  opacity: 1;
}

/* 印章角标 */
.seal-badge {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--brand-red, #dc2626);
  border-radius: var(--radius-sm);
  color: var(--brand-red, #dc2626);
  font-size: 10px;
  font-weight: var(--fw-bold);
  text-align: center;
  line-height: 1.3;
  writing-mode: vertical-rl;
  transform: rotate(8deg);
  background: var(--bg-primary);
  z-index: 2;
}

.content-right {
  flex: 1;
  min-width: 0;
}

.desc-block h2,
.detail-block h2 {
  font-size: var(--fs-lg);
  font-weight: var(--fw-semibold);
  color: var(--ink);
  margin: 0 0 var(--space-md);
}

.desc-block p {
  color: var(--text-muted);
  line-height: 1.9;
  font-size: var(--fs-base);
  margin: 0;
}

.detail-block {
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px dashed oklch(0 0 0 / 0.12);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: var(--fs-xs);
  color: var(--text-muted);
}

.detail-value {
  font-size: var(--fs-base);
  color: var(--ink);
  font-weight: var(--fw-medium);
}

/* ---- Zone 3: 视频 ---- */
.zone-video {
  padding-top: var(--space-2xl);
  border-top: 1px solid oklch(0 0 0 / 0.06);
}

.zone-video h2 {
  font-size: var(--fs-lg);
  font-weight: var(--fw-semibold);
  color: var(--ink);
  margin: 0 0 var(--space-md);
}

.video-wrap {
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.heritage-video {
  width: 100%;
  border-radius: var(--radius-lg);
}

/* ---- 错误状态 ---- */
.error-state {
  padding: var(--space-3xl);
}

/* ---- 响应式 ---- */
@media (max-width: 1024px) {
  .content-left {
    width: 280px;
  }

  .main-img, .img-placeholder {
    height: 260px;
  }
}

@media (max-width: 768px) {
  .zone-header {
    flex-direction: column;
  }

  .header-right {
    flex-direction: row;
    align-items: center;
    width: 100%;
    flex-wrap: wrap;
  }

  .zone-content {
    flex-direction: column;
  }

  .content-left {
    width: 100%;
  }

  .main-img, .img-placeholder {
    height: 240px;
  }

  .detail-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 480px) {
  .seal-badge {
    width: 36px;
    height: 36px;
    font-size: 8px;
    top: -8px;
    right: -8px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
