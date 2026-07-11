<template>
  <div class="home-page">
    <!-- ===== Hero · 全屏轮播 · 品牌认知 ===== -->
    <section
      class="hero-section"
      aria-label="品牌介绍"
      @touchstart.passive="onTouchStart"
      @touchend.passive="onTouchEnd"
    >
      <div class="hero-carousel">
        <div
          v-for="(slide, idx) in heroSlides"
          :key="idx"
          class="hero-slide"
          :class="{ active: currentHero === idx }"
          :style="{ backgroundImage: `url(${slide.image})` }"
        >
          <div class="hero-overlay"></div>
          <div class="hero-slide-caption">
            <h2 class="slide-caption-title">{{ slide.title }}</h2>
            <p class="slide-caption-desc">{{ slide.desc }}</p>
          </div>
        </div>
      </div>
      <div class="hero-content">
        <span class="hero-kicker">潮汕文化一站式服务平台</span>
        <h1 class="hero-title display-text--hero">探索潮汕<br>从舌尖到非遗</h1>
        <p class="hero-sub">AI智能规划 · 美食偏好推荐 · 文化知识问答</p>
        <div class="hero-tags">
          <button
            v-for="tag in hotTags"
            :key="tag"
            class="hero-tag"
            @click="onHeroSearch(tag)"
          >{{ tag }}</button>
        </div>
      </div>
      <!-- 嵌瓷色条收边 -->
      <div class="hero-porcelain-bar" aria-hidden="true"></div>
      <div class="hero-dots" v-if="heroSlides.length > 1">
        <button
          v-for="(_, idx) in heroSlides"
          :key="idx"
          :class="['hero-dot', { active: currentHero === idx }]"
          @click="currentHero = idx"
          :aria-label="`第${idx + 1}张`"
        />
      </div>
      <!-- 向下滚动提示 -->
      <div class="hero-scroll-hint" aria-hidden="true">
        <span class="scroll-arrow"></span>
      </div>
    </section>

    <!-- ===== 以下内容区 · 潮汕风景照背景 ===== -->
    <div class="content-with-bg">
      <!-- ===== 分类导航 · 不对称网格 ===== -->
      <section class="category-section" aria-label="分类导航">
      <div class="section-header">
        <h2 class="section-title display-text--section">
          <span class="title-accent">探索</span>潮汕
        </h2>
      </div>
      <div class="section-divider section-divider--left"></div>
      <div class="category-grid">
        <router-link
          v-for="(cat, idx) in categories"
          :key="cat.path"
          :to="cat.path"
          :class="['cat-card', { 'cat-card--featured': idx === 0 }]"
          :style="{ backgroundImage: `url(${cat.image})` }"
        >
          <div class="cat-overlay"></div>
          <div class="cat-body">
            <span class="cat-name">{{ cat.label }}</span>
            <span class="cat-sub">{{ cat.desc }}</span>
          </div>
        </router-link>
      </div>
    </section>

    <!-- ===== 热门美食 · 精选大卡 + 网格 ===== -->
    <section class="feed-section feed-section--foods" aria-label="热门美食">
      <div class="section-header">
        <h2 class="section-title display-text--section">
          <span class="title-accent">热门</span>美食
        </h2>
        <router-link to="/foods" class="section-more">
          查看全部 <el-icon class="more-arrow"><ArrowRight /></el-icon>
        </router-link>
      </div>

      <div v-if="foodsLoading" class="feed-grid-skeleton">
        <LoadingSkeleton v-for="i in 5" :key="i" type="card" :count="1" />
      </div>
      <div v-else-if="foodsError" class="feed-error">
        <span class="error-msg">加载失败</span>
        <el-button size="small" @click="loadFoods">重新加载</el-button>
      </div>
      <div v-else-if="!foods.length" class="feed-empty">
        <p>还没有美食推荐，我们的编辑正在狂吃测评中…</p>
      </div>
      <div v-else class="feed-grid">
        <FoodCard v-if="foods[0]" :food="foods[0]" class="feed-featured" />
        <FoodCard v-for="food in foods.slice(1, 5)" :key="food.id" :food="food" />
      </div>
    </section>

    <!-- ===== 热门非遗 · 精选大卡 + 网格 ===== -->
    <section class="feed-section feed-section--heritages" aria-label="热门非遗">
      <div class="section-header">
        <h2 class="section-title display-text--section">
          <span class="title-accent">热门</span>非遗
        </h2>
        <router-link to="/heritages" class="section-more">
          查看全部 <el-icon class="more-arrow"><ArrowRight /></el-icon>
        </router-link>
      </div>

      <div v-if="heritagesLoading" class="feed-grid-skeleton">
        <LoadingSkeleton v-for="i in 5" :key="i" type="card" :count="1" />
      </div>
      <div v-else-if="heritagesError" class="feed-error">
        <span class="error-msg">加载失败</span>
        <el-button size="small" @click="loadHeritages">重新加载</el-button>
      </div>
      <div v-else-if="!heritages.length" class="feed-empty">
        <p>非遗项目整理中，精彩即将呈现</p>
      </div>
      <div v-else class="feed-grid">
        <HeritageCard v-if="heritages[0]" :item="heritages[0]" class="feed-featured" />
        <HeritageCard v-for="item in heritages.slice(1, 5)" :key="item.id" :item="item" />
      </div>
    </section>

    <!-- ===== 民俗活动预告 · 琥珀底色区块 ===== -->
    <section class="festival-teaser" aria-label="民俗活动">
      <div class="festival-teaser-inner">
        <div class="section-header">
          <h2 class="section-title display-text--section">
            <span class="title-accent">近期</span>民俗
          </h2>
          <router-link to="/festival" class="section-more">
            查看日历 <el-icon class="more-arrow"><ArrowRight /></el-icon>
          </router-link>
        </div>
        <div class="festival-list">
          <router-link
            v-for="(evt, idx) in upcomingEvents"
            :key="idx"
            :to="evt.link || '/festival'"
            class="festival-card"
          >
            <div class="festival-date">
              <span class="date-month">{{ evt.month }}</span>
              <span class="date-day">{{ evt.day }}</span>
            </div>
            <div class="festival-info">
              <strong>{{ evt.name }}</strong>
              <span>{{ evt.location }}</span>
            </div>
            <el-icon class="festival-arrow"><ArrowRight /></el-icon>
          </router-link>
        </div>
      </div>
    </section>

    <!-- ===== 智慧出行 · 探索地图 ===== -->
    <section class="map-section" aria-label="智慧出行">
      <div class="section-header">
        <h2 class="section-title display-text--section">
          <span class="title-accent">智慧</span>出行
        </h2>
        <router-link to="/trip/create" class="section-more">
          定制行程 <el-icon class="more-arrow"><ArrowRight /></el-icon>
        </router-link>
      </div>
      <div class="map-section-inner">
        <MapContainer
          height="480px"
          :center="discoveryMapData.center"
          :zoom="11"
          :markers="discoveryMapData.markers"
          :heatmapData="discoveryMapData.heatmapData"
          :enableZoomFilter="true"
          :enableHoverInfo="true"
          :heatmapMinZoom="15"
          :interactive="true"
        />
      </div>
    </section>
    </div><!-- /content-with-bg -->
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChatDotRound, Guide, ArrowRight,
} from '@element-plus/icons-vue'
import FoodCard from '@/components/business/FoodCard.vue'
import HeritageCard from '@/components/business/HeritageCard.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import MapContainer from '@/components/common/MapContainer.vue'
import { getFoods, getHeritages } from '@/api'
import { foodApi } from '@/api/food'
import { heritageApi } from '@/api/heritage'
import { hotelApi } from '@/api/hotel'
import { dashboardApi } from '@/api/dashboard'
import { platformDataToMapData } from '@/utils/mapAdapter'
import { useMusic } from '@/composables/useMusic'

const router = useRouter()
const { init: initMusic } = useMusic()

// --- Hero ---
const currentHero = ref(0)
const heroSlides = [
  {
    image: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=1400&h=700&fit=crop',
    title: '潮汕美食',
    desc: '牛肉火锅、生腌海鲜、粿品小吃——舌尖上的潮汕，是千年闽粤文化的味觉沉淀，每一口都是时光的馈赠。',
  },
  {
    image: 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=1400&h=700&fit=crop',
    title: '非遗传承',
    desc: '英歌舞的豪迈、工夫茶的从容、潮剧的婉转——这些活着的文化遗产，至今仍在潮汕大地上生生不息。',
  },
  {
    image: 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=1400&h=700&fit=crop',
    title: '岁时节庆',
    desc: '营老爷巡游、元宵灯会、端午赛龙舟——潮汕人用最热烈的方式，守护着一方水土的信仰与温情。',
  },
]

const hotTags = ['牛肉火锅', '英歌舞', '工夫茶', '嵌瓷', '生腌']

function onHeroSearch(keyword) {
  if (keyword && keyword.trim()) {
    router.push({ path: '/search', query: { keyword: keyword.trim() } })
  }
}

// Auto-rotate hero
let heroTimer = null

// ── 触摸滑动 ──
let touchStartX = 0
let touchStartY = 0

function onTouchStart(e) {
  touchStartX = e.touches[0].clientX
  touchStartY = e.touches[0].clientY
}

function onTouchEnd(e) {
  const dx = e.changedTouches[0].clientX - touchStartX
  const dy = e.changedTouches[0].clientY - touchStartY
  // 水平滑动超过 50px 且大于垂直滑动
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
    if (dx < 0) {
      currentHero.value = (currentHero.value + 1) % heroSlides.length
    } else {
      currentHero.value = (currentHero.value - 1 + heroSlides.length) % heroSlides.length
    }
    resetHeroTimer()
  }
}

function resetHeroTimer() {
  clearInterval(heroTimer)
  heroTimer = setInterval(() => {
    currentHero.value = (currentHero.value + 1) % heroSlides.length
  }, 4000)
}

// ── 探索地图（精选推荐数据）──
const discoveryData = reactive({
  foods: [],
  heritages: [],
  hotels: [],
  crowd: [],
  weather: [],
})

const discoveryMapData = computed(() => platformDataToMapData(discoveryData))

async function loadDiscoveryMap() {
  try {
    const [foodsRes, heritagesRes, hotelsRes, crowdRes] = await Promise.all([
      foodApi.list({ is_recommended: true, page_size: 20 }),
      heritageApi.list({ is_recommended: true, page_size: 20 }),
      hotelApi.list({ is_recommended: true, page_size: 20 }),
      dashboardApi.crowdGeo(),
    ])
    discoveryData.foods = foodsRes?.items || []
    discoveryData.heritages = heritagesRes?.items || []
    discoveryData.hotels = hotelsRes?.items || []
    discoveryData.crowd = crowdRes || []
  } catch (e) {
    console.warn('首页探索地图加载失败:', e)
  }
}

// --- Categories ---
const categories = [
  {
    path: '/foods', label: '美食推荐', desc: '牛肉火锅 · 粿品 · 生腌',
    image: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&h=400&fit=crop',
  },
  {
    path: '/heritages', label: '非遗民俗', desc: '英歌舞 · 工夫茶 · 潮剧',
    image: 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=600&h=400&fit=crop',
  },
  {
    path: '/festival', label: '岁时节庆', desc: '营老爷 · 灯会 · 龙舟',
    image: 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=600&h=400&fit=crop',
  },
  {
    path: '/trip/create', label: '行程规划', desc: 'AI定制 · 三日经典路线',
    image: 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=600&h=400&fit=crop',
  },
  {
    path: '/community', label: '社区动态', desc: '探店笔记 · 文化讨论',
    image: 'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=600&h=400&fit=crop',
  },
  {
    path: '/dashboard', label: '数据大屏', desc: '实时人流 · 热门排行',
    image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&h=400&fit=crop',
  },
]

// --- Foods ---
const foods = ref([])
const foodsLoading = ref(false)
const foodsError = ref(false)

async function loadFoods() {
  foodsLoading.value = true
  foodsError.value = false
  try {
    const res = await getFoods({ is_recommended: true, page_size: 8, sort: 'view_count' })
    foods.value = res?.items || res?.data?.items || []
  } catch {
    foodsError.value = true
    foods.value = MOCK_FOODS
  } finally {
    foodsLoading.value = false
  }
}

// --- Heritages ---
const heritages = ref([])
const heritagesLoading = ref(false)
const heritagesError = ref(false)

async function loadHeritages() {
  heritagesLoading.value = true
  heritagesError.value = false
  try {
    const res = await getHeritages({ is_recommended: true, page_size: 8, sort: 'view_count' })
    heritages.value = res?.items || res?.data?.items || []
  } catch {
    heritagesError.value = true
    heritages.value = MOCK_HERITAGES
  } finally {
    heritagesLoading.value = false
  }
}

// --- Upcoming Events ---
const upcomingEvents = [
  { month: '正月', day: '初四', name: '营老爷巡游', location: '汕头澄海', link: '/festival' },
  { month: '正月', day: '十五', name: '元宵灯会', location: '潮州古城', link: '/festival' },
  { month: '五月', day: '初五', name: '端午赛龙舟', location: '汕头南澳', link: '/festival' },
  { month: '八月', day: '十五', name: '中秋烧塔', location: '揭阳普宁', link: '/festival' },
]

onMounted(() => {
  loadFoods()
  loadHeritages()
  loadDiscoveryMap()
  initMusic()
  resetHeroTimer()
})

onUnmounted(() => clearInterval(heroTimer))

// --- Mock data ---
const MOCK_FOODS = [
  { id: 1, name: '八合里海记牛肉火锅', category_name: '牛肉火锅', price_range: '¥¥', view_count: 12580, image_url: '' },
  { id: 2, name: '老四粿条汤', category_name: '小吃', price_range: '¥', view_count: 8320, image_url: '' },
  { id: 3, name: '建业酒家卤鹅', category_name: '卤味', price_range: '¥¥', view_count: 6780, image_url: '' },
  { id: 4, name: '老妈宫粽球', category_name: '小吃', price_range: '¥', view_count: 5400, image_url: '' },
  { id: 5, name: '杏花吴记牛肉火锅', category_name: '牛肉火锅', price_range: '¥¥¥', view_count: 9200, image_url: '' },
  { id: 6, name: '富苑饮食生腌', category_name: '海鲜', price_range: '¥¥', view_count: 7500, image_url: '' },
]

const MOCK_HERITAGES = [
  { id: 1, name: '潮州音乐', category: '国家级', type: '传统音乐', inheritor: '黄义孝', view_count: 9200, image_url: '' },
  { id: 2, name: '英歌舞', category: '国家级', type: '传统舞蹈', inheritor: '陈来发', view_count: 15800, image_url: '' },
  { id: 3, name: '潮剧', category: '国家级', type: '传统戏剧', inheritor: '姚璇秋', view_count: 11200, image_url: '' },
  { id: 4, name: '潮汕工夫茶', category: '国家级', type: '传统技艺', inheritor: '陈香白', view_count: 8900, image_url: '' },
  { id: 5, name: '嵌瓷', category: '国家级', type: '传统美术', inheritor: '卢芝高', view_count: 4300, image_url: '' },
  { id: 6, name: '潮汕木雕', category: '国家级', type: '传统美术', inheritor: '陈舜羌', view_count: 6100, image_url: '' },
]
</script>

<style scoped>
/* ==========================================
   Hero · 全屏轮播 · 嵌瓷收边 · 品牌认知优先
   ========================================== */
.hero-section {
  position: relative;
  width: 100vw;
  margin-left: calc(-50vw + 50%);
  margin-right: calc(-50vw + 50%);
  height: calc(100vh - 60px);
  overflow: hidden;
  margin-bottom: 0;
}

.hero-carousel {
  position: absolute;
  inset: 0;
}

.hero-slide {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  opacity: 0;
  transition: opacity 1.2s ease;
}

.hero-slide.active {
  opacity: 1;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    160deg,
    oklch(0.18 0.05 20 / 0.70) 0%,
    oklch(0.22 0.04 30 / 0.40) 50%,
    oklch(0.12 0.02 60 / 0.55) 100%
  );
}

/* 轮播图左下角文字说明 · 占屏约 1/4 */
.hero-slide-caption {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 25vh;
  min-height: 25%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 0 8vw 5vh 8vw;
  z-index: 3;
  background: linear-gradient(
    to top,
    oklch(0.08 0.02 20 / 0.65) 0%,
    oklch(0.10 0.02 25 / 0.30) 40%,
    transparent 100%
  );
  pointer-events: none;
}

.slide-caption-title {
  font-size: clamp(1.3rem, 2.5vw, 2.2rem);
  font-weight: var(--fw-black, 800);
  color: oklch(1 0 0 / 0.95);
  margin: 0 0 8px;
  letter-spacing: 0.03em;
  line-height: 1.2;
  text-shadow: 0 2px 12px oklch(0 0 0 / 0.5);
}

.slide-caption-desc {
  font-size: clamp(0.82rem, 1.2vw, 1.02rem);
  color: oklch(1 0 0 / 0.78);
  margin: 0;
  line-height: 1.7;
  max-width: 600px;
  text-shadow: 0 1px 6px oklch(0 0 0 / 0.4);
  text-wrap: balance;
}

/* 嵌瓷色条 — Hero 底部收边 */
.hero-porcelain-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient-porcelain);
  z-index: 4;
}

.hero-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: var(--space-2xl);
  max-width: 680px;
  margin: 0 auto;
}

.hero-kicker {
  font-size: 0.85rem;
  font-weight: 500;
  letter-spacing: 0.12em;
  color: var(--brand-amber-light);
  margin-bottom: var(--space-lg);
  text-transform: uppercase;
}

.hero-title {
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: var(--fw-black);
  line-height: var(--lh-tight);
  color: var(--text-inverse);
  margin: 0 0 var(--space-md);
  text-wrap: balance;
}

.hero-sub {
  font-size: 1.05rem;
  color: oklch(1 0 0 / 0.80);
  margin: 0 0 var(--space-xl);
  line-height: 1.5;
  max-width: 480px;
}

.hero-tags {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
  justify-content: center;
}

.hero-tag {
  padding: 5px 16px;
  font-size: 0.8rem;
  font-weight: 500;
  color: oklch(1 0 0 / 0.85);
  background: oklch(1 0 0 / 0.12);
  border: 1px solid oklch(1 0 0 / 0.18);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, transform 0.2s;
  backdrop-filter: blur(4px);
}

.hero-tag:hover {
  background: oklch(1 0 0 / 0.22);
  border-color: oklch(1 0 0 / 0.35);
  transform: translateY(-1px);
}

/* Hero dots */
.hero-dots {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 3;
}

.hero-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1.5px solid oklch(1 0 0 / 0.5);
  background: transparent;
  cursor: pointer;
  padding: 0;
  transition: background 0.3s, border-color 0.3s, transform 0.3s;
  -webkit-tap-highlight-color: transparent;
}

.hero-dot.active {
  background: var(--text-inverse);
  border-color: var(--text-inverse);
  transform: scale(1.2);
}

/* 移动端放大触摸区域 */
@media (max-width: 767px) {
  .hero-dot {
    width: 12px;
    height: 12px;
    padding: 8px;
    background-clip: content-box;
  }
}

/* Hero 向下滚动提示 */
.hero-scroll-hint {
  position: absolute;
  bottom: 36px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3;
}

.scroll-arrow {
  display: block;
  width: 24px;
  height: 24px;
  border-right: 2px solid oklch(1 0 0 / 0.6);
  border-bottom: 2px solid oklch(1 0 0 / 0.6);
  transform: rotate(45deg);
  animation: hero-scroll-bounce 2s ease-in-out infinite;
}

@keyframes hero-scroll-bounce {
  0%, 100% { transform: rotate(45deg) translateY(0); opacity: 0.6; }
  50% { transform: rotate(45deg) translateY(6px); opacity: 1; }
}

/* ==========================================
   智慧出行 · 探索地图
   ========================================== */
.map-section {
  margin-bottom: var(--space-3xl);
}

.map-section-inner {
  border-radius: var(--radius-xl, 16px);
  overflow: hidden;
  box-shadow: var(--shadow-md, 0 4px 16px oklch(0.15 0.02 25 / 0.08));
}

@media (max-width: 768px) {
  .map-section {
    margin-bottom: var(--space-2xl);
  }

  .map-section-inner {
    border-radius: var(--radius-lg, 12px);
  }
}

/* ==========================================
   内容背景区 · 潮汕风景照（层1 — 最亮的暖色底）
   ========================================== */
.content-with-bg {
  position: relative;
  margin-left: calc(-50vw + 50%);
  margin-right: calc(-50vw + 50%);
  padding-left: calc(50vw - 50% + 45px);
  padding-right: calc(50vw - 50% + 45px);
  padding-top: var(--space-2xl);
  padding-bottom: 0;
  background: var(--bg-page);
}

/* 内容区内各 section 全宽铺满 */
.content-with-bg > section {
  width: 100%;
}

/* ── 各板块微妙区分 ── */
/* 分类导航 — 无额外底色，利用最外层亮底 */
.category-section {
  position: relative;
}

/* 美食板块 — 食物暖色微染 */
.feed-section--foods {
  background: linear-gradient(180deg, oklch(0.95 0.018 80 / 0.45) 0%, oklch(0.93 0.022 78 / 0.35) 100%);
  border-radius: var(--radius-xl, 16px);
  padding: var(--space-xl);
}

/* 非遗板块 — 深沉文化暖色微染 */
.feed-section--heritages {
  background: linear-gradient(180deg, oklch(0.92 0.022 75 / 0.50) 0%, oklch(0.89 0.028 70 / 0.40) 100%);
  border-radius: var(--radius-xl, 16px);
  padding: var(--space-xl);
}

/* ==========================================
   AI 横幅 · 紧凑琥珀 accent
   ========================================== */
.ai-section {
  margin-bottom: var(--space-3xl);
  margin-top: var(--space-2xl);
}

.ai-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-xl);
  padding: var(--space-xl) var(--space-2xl);
  background: var(--bg-surface-alt);
  border-left: 4px solid var(--brand-amber);
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
}

.ai-text {
  flex: 1;
}

.ai-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 var(--space-sm);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.ai-title::after {
  content: 'AI';
  display: inline-block;
  padding: 1px 8px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--brand-red);
  background: var(--brand-red-muted);
  border-radius: 4px;
}

.ai-desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 var(--space-md);
  max-width: 520px;
}

.ai-actions {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.ai-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  font-size: 0.9rem;
  font-weight: 600;
  border-radius: 10px;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s;
}

.ai-btn:hover {
  transform: translateY(-2px);
}

.ai-btn-primary {
  color: var(--text-inverse);
  background: var(--brand-red);
  box-shadow: 0 4px 16px oklch(0.53 0.22 25 / 0.3);
}

.ai-btn-primary:hover {
  box-shadow: 0 6px 24px oklch(0.53 0.22 25 / 0.4);
}

.ai-btn-secondary {
  color: var(--text-primary);
  background: var(--bg-page);
  border: 1px solid var(--border-default);
}

.ai-btn-secondary:hover {
  background: var(--bg-surface);
  box-shadow: var(--shadow-sm);
}

.ai-visual {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ai-char {
  font-size: 56px;
  font-weight: 900;
  color: var(--brand-amber);
  opacity: 0.25;
  font-family: var(--font-display);
}

/* ==========================================
   Section Header · 编辑感标题
   ========================================== */
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
}

.section-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.01em;
}

.title-accent {
  color: var(--primary);
  font-weight: 400;
}

.section-more {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--muted);
  text-decoration: none;
  transition: color 0.2s;
}

.section-more:hover { color: var(--primary); }

.more-arrow { transition: transform 0.25s ease; }
.section-more:hover .more-arrow { transform: translateX(3px); }

/* ==========================================
   Category Grid · 图片目的地卡片 3×2
   ========================================== */
.category-section {
  margin-bottom: var(--space-3xl);
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.cat-card {
  position: relative;
  aspect-ratio: 3 / 2;
  border-radius: 14px;
  overflow: hidden;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: flex-end;
  cursor: pointer;
  text-decoration: none;
  transition: transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1),
              box-shadow 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.cat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px oklch(0.20 0.03 25 / 0.18);
}

.cat-card:hover .cat-overlay {
  background: linear-gradient(to top, oklch(0.15 0.02 25 / 0.85) 0%, oklch(0.15 0.02 25 / 0.25) 60%, transparent 100%);
}

.cat-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, oklch(0.15 0.02 25 / 0.75) 0%, oklch(0.15 0.02 25 / 0.15) 50%, transparent 100%);
  transition: background 0.4s;
}

.cat-body {
  position: relative;
  z-index: 2;
  padding: 20px;
  color: #fff;
}

.cat-name {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.cat-sub {
  display: block;
  font-size: 0.78rem;
  opacity: 0.8;
  line-height: 1.3;
}

/* 精选大卡 — 首项跨 2 列形成不对称节奏 */
.cat-card--featured {
  grid-column: span 2;
  grid-row: span 2;
  aspect-ratio: auto;
}

/* ── 嵌瓷分隔线间距 ── */
.category-section .section-divider {
  margin-bottom: var(--space-lg);
}

/* ==========================================
   Feed Sections · 精选大卡 + 网格布局
   ========================================== */
.feed-section {
  margin-bottom: var(--space-3xl);
}

.feed-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.feed-featured {
  grid-column: span 2;
  grid-row: span 2;
}

.feed-grid-skeleton {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.feed-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-2xl) 0;
}

.error-msg {
  color: var(--muted);
  font-size: 0.9rem;
}

.feed-empty {
  text-align: center;
  padding: var(--space-2xl) 0;
}

.feed-empty p {
  color: var(--muted);
  font-size: 0.9rem;
  margin: 0;
}

/* ==========================================
   Festival Teaser · 活动时间线卡片
   ========================================== */
.festival-teaser {
  margin-bottom: 0;
  padding-bottom: var(--space-2xl);
}

.festival-teaser-inner {
  background: var(--brand-amber-wash);
  border-radius: var(--radius-xl);
  padding: var(--space-2xl);
}

.festival-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

.festival-card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: 16px 20px;
  background: oklch(0.98 0.004 70);
  border: 1px solid oklch(0.90 0.01 70);
  border-radius: 14px;
  text-decoration: none;
  color: var(--ink);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s;
}

.festival-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px oklch(0.20 0.03 25 / 0.08);
  border-color: oklch(0.78 0.04 75);
}

.festival-date {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  height: 52px;
  background: var(--brand-red);
  color: #fff;
  border-radius: 10px;
  flex-shrink: 0;
}

.date-month {
  font-size: 0.7rem;
  font-weight: 500;
  line-height: 1.2;
  opacity: 0.85;
}

.date-day {
  font-size: 1.1rem;
  font-weight: 800;
  line-height: 1.2;
}

.festival-info {
  flex: 1;
  min-width: 0;
}

.festival-info strong {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 2px;
}

.festival-info span {
  font-size: 0.78rem;
  color: var(--muted);
}

.festival-arrow {
  color: var(--muted);
  flex-shrink: 0;
  transition: transform 0.25s ease;
}

.festival-card:hover .festival-arrow {
  transform: translateX(3px);
  color: var(--primary);
}

/* ==========================================
   Responsive
   ========================================== */
@media (max-width: 1023px) {
  .hero-section {
    height: calc(100vh - 56px);
  }

  /* 平板：缩小 caption 高度 */
  .hero-slide-caption {
    height: 20vh;
    padding: 0 6vw 3vh 6vw;
  }

  .slide-caption-title {
    font-size: clamp(1.1rem, 2vw, 1.6rem);
  }

  .slide-caption-desc {
    font-size: clamp(0.75rem, 1vw, 0.9rem);
    max-width: 480px;
  }

  .category-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .cat-card--featured {
    grid-column: span 2;
    grid-row: span 2;
  }

  .ai-visual {
    display: none;
  }

  .festival-list {
    grid-template-columns: 1fr;
  }

  .feed-grid,
  .feed-grid-skeleton {
    grid-template-columns: repeat(2, 1fr);
  }

  .feed-featured {
    grid-column: span 2;
    grid-row: span 2;
  }
}

@media (max-width: 767px) {
  .hero-section {
    height: 100vh;
    height: 100dvh;
    /* iPhone 刘海 / 灵动岛安全区 */
    padding-top: env(safe-area-inset-top);
  }

  /* 横屏手机：限制最大高度，防止轮播过高 */
  @media (orientation: landscape) {
    .hero-section {
      height: auto;
      min-height: 100dvh;
    }

    .hero-content {
      padding: max(12dvh, 60px) 5vw var(--space-xl);
    }
  }

  /* 中间主文案：上移以避免与底部说明重叠 */
  .hero-content {
    justify-content: flex-start;
    padding: 18vh 5vw 0;
    height: 100%;
  }

  .hero-kicker {
    font-size: 0.72rem;
    margin-bottom: var(--space-sm);
    letter-spacing: 0.1em;
  }

  .hero-title {
    font-size: clamp(1.6rem, 7vw, 2.2rem);
    margin-bottom: var(--space-sm);
    line-height: 1.25;
  }

  .hero-sub {
    font-size: 0.82rem;
    margin-bottom: var(--space-lg);
    max-width: 320px;
    line-height: 1.4;
  }

  .hero-tags {
    gap: 6px;
  }

  .hero-tag {
    font-size: 0.72rem;
    padding: 4px 12px;
  }

  /* 底部说明：自适应高度，不再固定 25vh */
  .hero-slide-caption {
    height: auto;
    min-height: unset;
    padding: 16px 5vw 20px;
    padding-bottom: max(20px, env(safe-area-inset-bottom, 0px));
    background: linear-gradient(
      to top,
      oklch(0.08 0.02 20 / 0.75) 0%,
      oklch(0.10 0.02 25 / 0.35) 55%,
      transparent 100%
    );
  }

  .slide-caption-title {
    font-size: 1.05rem;
    margin-bottom: 4px;
    letter-spacing: 0.02em;
  }

  .slide-caption-desc {
    font-size: 0.76rem;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    max-width: 100%;
  }

  /* 轮播圆点：移到说明文字上方 */
  .hero-dots {
    bottom: auto;
    top: calc(100% - 80px);
  }

  /* 隐藏滚动提示箭头 */
  .hero-scroll-hint {
    display: none;
  }

  .category-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-sm);
  }

  .cat-card--featured {
    grid-column: span 2;
    grid-row: span 1;
  }

  .cat-card {
    aspect-ratio: 4 / 3;
    border-radius: 10px;
  }

  .cat-body {
    padding: 14px;
  }

  .cat-name {
    font-size: 0.95rem;
  }

  .cat-sub {
    font-size: 0.7rem;
  }

  .ai-banner {
    flex-direction: column;
    padding: var(--space-lg);
  }

  .ai-title {
    font-size: 1.15rem;
  }

  .ai-desc {
    font-size: 0.82rem;
  }

  .ai-actions {
    flex-direction: column;
  }

  .ai-visual {
    display: none;
  }

  .feed-grid,
  .feed-grid-skeleton {
    grid-template-columns: 1fr;
  }

  .feed-featured {
    grid-column: span 1;
    grid-row: span 2;
  }

  .festival-teaser-inner {
    padding: var(--space-lg);
  }

  .section-title {
    font-size: 1.15rem;
  }
}

/* ==========================================
   Motion respect
   ========================================== */
@media (prefers-reduced-motion: reduce) {
  .hero-slide { transition: none; }
  .scroll-arrow { animation: none; }
  .cat-card, .festival-card, .ai-btn { transition: none; }
  .more-arrow { transition: none; }
}
</style>
