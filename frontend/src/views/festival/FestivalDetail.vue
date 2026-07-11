<template>
  <div class="festival-detail-wrapper">
    <!-- 两侧底色装饰 -->
    <div class="side-decorations" aria-hidden="true">
      <img src="/images/events/decorations/祥云1.png" class="side-deco side-left-1" />
      <img src="/images/events/decorations/祥云4.png" class="side-deco side-left-2" />
      <img src="/images/events/decorations/直纹1.png" class="side-deco side-left-3" />
      <img src="/images/events/decorations/祥云2.png" class="side-deco side-right-1" />
      <img src="/images/events/decorations/祥云3.png" class="side-deco side-right-2" />
      <img src="/images/events/decorations/直纹2.png" class="side-deco side-right-3" />
    </div>

    <div class="festival-detail-page">
      <BackButton />
      <div class="page-hero">
        <h1 class="display-text--section">{{ event?.name || '民俗活动详情' }}</h1>
        <p v-if="slogan" class="festival-slogan">{{ slogan }}</p>
        <div class="section-divider section-divider--left"></div>
      </div>

      <LoadingSkeleton v-if="loading" type="detail" />
      <EmptyState v-else-if="!event" description="活动不存在或已删除" />

      <div v-else class="detail-content">
        <!-- 图片轮播区域 · 左浮动，文字环绕 -->
        <div class="image-carousel">
          <div class="carousel-viewport">
            <img
              :src="images[currentIndex]"
              :alt="event.name"
              class="carousel-image"
              @error="onImageError"
            />
            <button
              v-if="images.length > 1"
              class="carousel-btn carousel-btn--prev"
              @click="prevImage"
            >&#10094;</button>
            <button
              v-if="images.length > 1"
              class="carousel-btn carousel-btn--next"
              @click="nextImage"
            >&#10095;</button>
          </div>
          <div v-if="images.length > 1" class="carousel-dots">
            <span
              v-for="(_, i) in images"
              :key="i"
              class="dot"
              :class="{ active: i === currentIndex }"
              @click="currentIndex = i"
            ></span>
          </div>
        </div>

        <div class="text-body">
          <p>{{ event?.description || '暂无描述' }}</p>
        </div>
      </div>

      <!-- 装饰图层 -->
      <div class="decorations" aria-hidden="true">
        <img src="/images/events/decorations/祥云1.png" class="deco deco-cloud1" />
        <img src="/images/events/decorations/祥云2.png" class="deco deco-cloud2" />
        <img src="/images/events/decorations/祥云3.png" class="deco deco-cloud3" />
        <img src="/images/events/decorations/祥云4.png" class="deco deco-cloud4" />
        <img src="/images/events/decorations/云纹1.png" class="deco deco-pattern1" />
        <img src="/images/events/decorations/云纹2.png" class="deco deco-pattern2" />
        <img src="/images/events/decorations/直纹1.png" class="deco deco-stripe1" />
        <img src="/images/events/decorations/直纹2.png" class="deco deco-stripe2" />
        <img src="/images/events/decorations/直纹3.png" class="deco deco-stripe3" />
        <img src="/images/events/decorations/直纹4.png" class="deco deco-stripe4" />
        <img src="/images/events/decorations/直纹5.png" class="deco deco-stripe5" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { eventApi } from '@/api/event'
import BackButton from '@/components/common/BackButton.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const route = useRoute()
const loading = ref(true)
const event = ref(null)
const currentIndex = ref(0)
const brokenImages = ref(new Set())

const SLOGANS = {
  '营老爷巡游': '老爷出巡保安宁，风调雨顺合境兴',
  '元宵灯会': '花灯如昼映古城，人月两圆庆良宵',
  '端午节赛龙舟': '龙舟竞渡鼓声急，万众欢腾庆端阳',
  '出花园': '七夕花开别稚气，少年立志闯四方',
  '中秋烧塔': '砖塔火光照夜空，红红火火好年丰',
  '冬至祭祖': '冬大过年聚满堂，祭祖搓丸庆团圆',
  '游神赛会': '锣鼓喧天英歌起，万众同游贺新春',
  '潮汕侨批文化展': '一封侨批万种情，天涯游子寄乡心',
}

const slogan = computed(() => event.value ? SLOGANS[event.value.name] || '' : '')

const images = computed(() => {
  if (!event.value?.image_url) return []
  try {
    const parsed = JSON.parse(event.value.image_url)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return event.value.image_url ? [event.value.image_url] : []
  }
})

function onImageError() {
  brokenImages.value.add(currentIndex.value)
  if (brokenImages.value.size >= images.value.length) return
  let next = (currentIndex.value + 1) % images.value.length
  while (brokenImages.value.has(next) && next !== currentIndex.value) {
    next = (next + 1) % images.value.length
  }
  currentIndex.value = next
}

function prevImage() {
  if (images.value.length <= 1) return
  let idx = currentIndex.value
  do {
    idx = (idx - 1 + images.value.length) % images.value.length
  } while (brokenImages.value.has(idx) && idx !== currentIndex.value)
  currentIndex.value = idx
}

function nextImage() {
  if (images.value.length <= 1) return
  let idx = currentIndex.value
  do {
    idx = (idx + 1) % images.value.length
  } while (brokenImages.value.has(idx) && idx !== currentIndex.value)
  currentIndex.value = idx
}

onMounted(async () => {
  try {
    const data = await eventApi.detail(route.params.id)
    event.value = data
  } catch {
    event.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* 外层全宽容器 · 承载两侧底色装饰 */
.festival-detail-wrapper {
  width: 100%;
  position: relative;
  overflow: hidden;
}

/* 两侧底色装饰 */
.side-decorations {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.side-deco {
  position: absolute;
  opacity: 0.3;
  pointer-events: none;
}

.side-left-1 { left: 2%; top: 5%; width: 140px; }
.side-left-2 { left: 2%; top: 45%; width: 130px; }
.side-left-3 { left: 1%; top: 20%; width: 30px; height: 60%; object-fit: contain; }
.side-right-1 { right: 2%; top: 10%; width: 140px; }
.side-right-2 { right: 2%; top: 50%; width: 130px; }
.side-right-3 { right: 1%; top: 20%; width: 30px; height: 60%; object-fit: contain; }

.festival-detail-page {
  max-width: 900px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-md);
  position: relative;
}

.page-hero {
  text-align: left;
  padding: var(--space-2xl) 0;
}

.page-hero h1 {
  font-size: 4rem;
  color: var(--ink);
  margin: 0 0 var(--space-sm);
}

.page-hero p {
  color: var(--muted);
  font-size: var(--fs-lg);
  margin: 0 0 var(--space-md);
  font-style: italic;
  letter-spacing: 0.05em;
}

.detail-content {
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* 装饰图层 · 30%透明 */
.decorations {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.deco {
  position: absolute;
  opacity: 0.3;
  pointer-events: none;
}

/* 祥云 · 左右两侧 */
.deco-cloud1 { left: 70px; top: 0; width: 160px; }
.deco-cloud2 { right: 70px; top: 60px; width: 160px; }
.deco-cloud3 { left: 90px; top: 320px; width: 140px; }
.deco-cloud4 { right: 90px; top: 380px; width: 140px; }

/* 云纹 · 上下点缀 */
.deco-pattern1 { left: 50%; transform: translateX(-50%); top: 110px; width: 120px; }
.deco-pattern2 { left: 50%; transform: translateX(-50%); bottom: 110px; width: 120px; }

/* 直纹 · 四边 + 左侧额外 */
.deco-stripe1 { left: 120px; top: 10%; width: 60px; height: 80%; object-fit: contain; }
.deco-stripe2 { right: 120px; top: 10%; width: 60px; height: 80%; object-fit: contain; }
.deco-stripe3 { left: 0; top: 200px; width: 100%; height: 40px; object-fit: contain; }
.deco-stripe4 { left: 0; bottom: 200px; width: 100%; height: 40px; object-fit: contain; }
.deco-stripe5 { left: 100px; top: 160px; width: 100px; }

/* 图片轮播区域 · 左浮动 */
.image-carousel {
  float: left;
  width: 540px;
  margin-right: var(--space-xl);
  margin-bottom: var(--space-lg);
}

.carousel-viewport {
  position: relative;
  width: 540px;
  height: 405px;
  overflow: hidden;
  border-radius: 8px;
  background: var(--bg-surface);
}

.carousel-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.carousel-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.4);
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.carousel-btn:hover {
  background: rgba(0, 0, 0, 0.65);
}
.carousel-btn--prev { left: 8px; }
.carousel-btn--next { right: 8px; }

.carousel-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 8px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--muted);
  cursor: pointer;
  transition: background 0.2s;
}
.dot.active {
  background: var(--primary);
}

.text-body {
  color: var(--ink);
  font-size: var(--fs-base);
  line-height: 2;
  text-align: justify;
}

@media (max-width: 640px) {
  .image-carousel {
    float: none;
    width: 100%;
    margin-right: 0;
  }
  .carousel-viewport {
    width: 100%;
    height: 330px;
  }
  .page-hero h1 {
    font-size: 2rem;
  }
}
</style>
