<template>
  <div class="heritage-detail-page">
    <!-- 装饰背景 -->
    <img class="deco-bg deco-bg--1" src="/images/events/Heritage/非遗二级bg (1).jpg" alt="" />
    <img class="deco-bg deco-bg--2" src="/images/events/Heritage/非遗二级bg (2).jpg" alt="" />
    <img class="deco-bg deco-bg--3" src="/images/events/Heritage/非遗二级bg (3).jpg" alt="" />

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

      <!-- Zone 1: 标题 + 传承人 + 标签 -->
      <div class="zone-header">
        <div class="header-left">
          <div class="title-row">
            <h1 class="heritage-title">{{ heritage.name }}</h1>
            <div v-if="heritage.inheritor" class="inheritor-card">
              <span class="inheritor-icon">🧑‍🎓</span>
              <div class="inheritor-info">
                <span class="inheritor-name">{{ heritage.inheritor }}</span>
                <span class="inheritor-label">代表性传承人</span>
              </div>
            </div>
          </div>
          <div class="meta-line">
            <span class="level-tag" :class="levelClass">{{ heritage.category }}</span>
            <span class="type-tag">{{ heritage.type }}</span>
            <span class="region">📍 {{ heritage.region }}</span>
            <span class="views">👀 {{ heritage.view_count }} 次浏览</span>
          </div>
        </div>
        <div class="header-right">
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
          <!-- 主图轮播 -->
          <div class="image-card" v-if="allImages.length > 0">
            <div class="image-card__track" :style="{ transform: `translateX(-${mainImgIndex * 100}%)` }">
              <img
                v-for="(img, i) in allImages"
                :key="i"
                :src="img"
                :alt="`${heritage.name} - ${i + 1}`"
                class="main-img"
              />
            </div>
            <!-- 切换箭头 -->
            <button
              v-if="allImages.length > 1"
              class="img-arrow img-arrow--left"
              @click.stop="prevMainImg"
            >◀</button>
            <button
              v-if="allImages.length > 1"
              class="img-arrow img-arrow--right"
              @click.stop="nextMainImg"
            >▶</button>
            <!-- 图片计数器 -->
            <span v-if="allImages.length > 1" class="img-counter">{{ mainImgIndex + 1 }} / {{ allImages.length }}</span>
            <!-- 点击放大遮罩 -->
            <div class="img-overlay" @click="openViewer">
              <el-icon :size="24"><ZoomIn /></el-icon>
              <span>点击放大</span>
            </div>
          </div>
          <div v-else class="img-placeholder">🎭</div>
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

      <!-- 图片轮播 -->
      <section v-if="galleryImages.length > 0" class="zone-gallery">
        <h2>🖼️ 图片展示</h2>
        <div class="gallery-container">
          <button class="gallery-arrow gallery-arrow--left" @click="prevSlide" :disabled="galleryImages.length <= 1">
            ◀
          </button>
          <div class="gallery-viewport">
            <div
              class="gallery-track"
              :style="{ transform: `translateX(-${currentSlide * 100}%)` }"
            >
              <div
                v-for="(img, i) in galleryImages"
                :key="i"
                class="gallery-slide"
                @click="viewer.open(galleryImages, i)"
              >
                <img :src="img" :alt="`${heritage.name} - ${i + 1}`" />
              </div>
            </div>
          </div>
          <button class="gallery-arrow gallery-arrow--right" @click="nextSlide" :disabled="galleryImages.length <= 1">
            ▶
          </button>
        </div>
        <div class="gallery-dots">
          <span
            v-for="(img, i) in galleryImages"
            :key="i"
            class="gallery-dot"
            :class="{ active: i === currentSlide }"
            @click="currentSlide = i"
          />
        </div>
      </section>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, StarFilled, ArrowLeft, ZoomIn } from '@element-plus/icons-vue'
import { getHeritageDetail, addFavorite, removeFavorite, checkFavorite, getHeritageImages } from '@/api'
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

// 图片轮播
const galleryImages = ref([])
const currentSlide = ref(0)
const mainImgIndex = ref(0)

// 合并所有图片：galleryImages优先，fallback到heritage.image_url
const allImages = computed(() => {
  if (galleryImages.value.length > 0) return galleryImages.value
  if (heritage.value?.image_url) return [heritage.value.image_url]
  return []
})

function prevMainImg() {
  mainImgIndex.value = (mainImgIndex.value - 1 + allImages.value.length) % allImages.value.length
}
function nextMainImg() {
  mainImgIndex.value = (mainImgIndex.value + 1) % allImages.value.length
}
function openViewer() {
  if (allImages.value.length > 0) {
    viewer.value.open(allImages.value, mainImgIndex.value)
  }
}

function prevSlide() {
  currentSlide.value = (currentSlide.value - 1 + galleryImages.value.length) % galleryImages.value.length
}

function nextSlide() {
  currentSlide.value = (currentSlide.value + 1) % galleryImages.value.length
}

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
    await fetchImages()
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function fetchImages() {
  try {
    const res = await getHeritageImages(route.params.id)
    galleryImages.value = res || []
    currentSlide.value = 0
  } catch { /* ignore */ }
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

onMounted(() => {
  document.body.classList.add('heritage-detail-open')
  fetchDetail()
})
onBeforeUnmount(() => {
  document.body.classList.remove('heritage-detail-open')
})
</script>

<style scoped>
.heritage-detail-page {
  max-width: var(--content-wide, 1200px);
  margin: 0 auto;
  padding: var(--space-lg) var(--space-md) var(--space-xl);
  background: transparent;
}

/* ---- 装饰背景图 ---- */
.deco-bg {
  position: fixed;
  z-index: 0;
  pointer-events: none;
  opacity: 0.35;
}

.deco-bg--1 {
  bottom: 0;
  left: -100px;
  max-height: 60vh;
  object-fit: contain;
}

.deco-bg--2 {
  top: calc(50% - 200px);
  left: 0;
  transform: translateY(-50%);
  max-height: 52.5vh;
  object-fit: contain;
}

.deco-bg--3 {
  bottom: 0;
  right: 0;
  max-height: 60vh;
  object-fit: contain;
}

/* 让内部区块半透明，透出装饰背景 */
.zone-header,
.back-nav,
.desc-block,
.detail-block {
  background: rgba(255,255,255,0.5) !important;
  backdrop-filter: blur(2px);
  border-radius: var(--radius-md);
}

.zone-gallery {
  background: rgba(255,255,255,0.5) !important;
  backdrop-filter: blur(2px);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.img-placeholder,
.error-state {
  background: rgba(255,255,255,0.5) !important;
  backdrop-filter: blur(2px);
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

.title-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
  margin-bottom: var(--space-md);
}

.heritage-title {
  font-family: var(--font-display);
  font-size: 45px;
  font-weight: var(--fw-black);
  color: var(--ink);
  margin: 0;
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

/* 收藏按钮 */
.header-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

/* 传承人卡片 */

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
  aspect-ratio: 3 / 4;
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

.image-card__track {
  display: flex;
  height: 100%;
  transition: transform 0.4s ease;
}

.main-img {
  min-width: 100%;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.img-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: rgba(0,0,0,0.45);
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease, background 0.2s ease;
  z-index: 3;
}

.image-card:hover .img-arrow { opacity: 1; }
.img-arrow:hover { background: rgba(0,0,0,0.7); }
.img-arrow--left  { left: 8px; }
.img-arrow--right { right: 8px; }

.img-counter {
  position: absolute;
  bottom: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0,0,0,0.5);
  color: #fff;
  font-size: 11px;
  z-index: 3;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.image-card:hover .img-counter { opacity: 1; }

.img-placeholder {
  width: 100%;
  height: 100%;
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

/* ---- 图片轮播 ---- */
.zone-gallery {
  padding-top: var(--space-2xl);
  border-top: 1px solid oklch(0 0 0 / 0.06);
}

.zone-gallery h2 {
  font-size: var(--fs-lg);
  font-weight: var(--fw-semibold);
  color: var(--ink);
  margin: 0 0 var(--space-lg);
}

.gallery-container {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.gallery-arrow {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-surface);
  border: 1px solid oklch(0 0 0 / 0.1);
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  color: var(--ink);
  transition: all 0.2s ease;
  user-select: none;
}

.gallery-arrow:hover:not(:disabled) {
  background: var(--brand-primary);
  color: #fff;
  border-color: var(--brand-primary);
}

.gallery-arrow:disabled {
  opacity: 0.3;
  cursor: default;
}

.gallery-viewport {
  flex: 1;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.gallery-track {
  display: flex;
  transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.gallery-slide {
  min-width: 100%;
  aspect-ratio: 16 / 9;
  cursor: pointer;
}

.gallery-slide img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.gallery-dots {
  display: flex;
  justify-content: center;
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.gallery-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: oklch(0 0 0 / 0.2);
  cursor: pointer;
  transition: all 0.3s ease;
}

.gallery-dot.active {
  background: var(--brand-primary);
  width: 28px;
  border-radius: 5px;
}

.gallery-dot:hover:not(.active) {
  background: oklch(0 0 0 / 0.4);
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
}

@media (max-width: 768px) {
  .title-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .zone-header {
    flex-direction: column;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
  }

  .zone-content {
    flex-direction: column;
  }

  .content-left {
    width: 100%;
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

<style>
body.heritage-detail-open,
body.heritage-detail-open #app {
  background: transparent !important;
}
body.heritage-detail-open .app-footer {
  position: relative;
  z-index: 1;
}
</style>
