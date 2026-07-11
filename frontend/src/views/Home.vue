<template>
  <div class="home-page">
    <!-- ===== Hero · 品牌认知 · 嵌瓷收边 ===== -->
    <section class="hero-section" aria-label="品牌介绍">
      <div class="hero-carousel">
        <div
          v-for="(slide, idx) in heroSlides"
          :key="idx"
          class="hero-slide"
          :class="{ active: currentHero === idx }"
          :style="{ backgroundImage: `url(${slide.image})` }"
        >
          <div class="hero-overlay"></div>
        </div>
      </div>
      <div class="hero-content">
        <span class="hero-kicker">潮汕文化一站式服务平台</span>
        <h1 class="hero-title display-text--hero">探索潮汕<br>从舌尖到非遗</h1>
        <p class="hero-sub">AI智能规划 · 美食偏好推荐 · 文化知识问答</p>
        <div class="hero-search">
          <SearchBar @search="onHeroSearch" />
        </div>
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
    </section>

    <!-- ===== AI 导览 · 紧凑横幅 ===== -->
    <section class="ai-section" aria-label="AI功能">
      <div class="ai-banner">
        <div class="ai-text">
          <h2 class="ai-title">AI 潮小助</h2>
          <p class="ai-desc">基于大语言模型的智能向导——听懂你的口味偏好，规划专属行程，解答潮汕文化的一切好奇。</p>
          <div class="ai-actions">
            <router-link to="/chat" class="ai-btn ai-btn-primary">
              <el-icon><ChatDotRound /></el-icon>
              开始对话
            </router-link>
            <router-link to="/trip/create" class="ai-btn ai-btn-secondary">
              <el-icon><Guide /></el-icon>
              智能规划行程
            </router-link>
          </div>
        </div>
        <div class="ai-visual" aria-hidden="true">
          <span class="ai-char">潮</span>
        </div>
      </div>
    </section>

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
    <section class="feed-section" aria-label="热门美食">
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
    <section class="feed-section" aria-label="热门非遗">
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

    <!-- ===== 探索地图 · 精选数据 ===== -->
    <section class="home-map-section" aria-label="探索地图">
      <div class="home-map-overlay">
        <h2 class="display-text--section">发现潮汕之美</h2>
        <p>在地图上探索地道美食、非遗传承、民俗节庆</p>
        <el-button type="primary" size="large" @click="$router.push('/trip/create')">
          定制我的行程 →
        </el-button>
      </div>
      <MapContainer
        height="450px"
        :center="discoveryMapData.center"
        :zoom="11"
        :markers="discoveryMapData.markers"
        :heatmapData="discoveryMapData.heatmapData"
        :enableZoomFilter="true"
        :enableHoverInfo="true"
        :heatmapMinZoom="15"
        :interactive="true"
      />
    </section>
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

const router = useRouter()

// --- Hero ---
const currentHero = ref(0)
const heroSlides = [
  {
    image: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=1400&h=700&fit=crop',
  },
  {
    image: 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=1400&h=700&fit=crop',
  },
  {
    image: 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=1400&h=700&fit=crop',
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
onMounted(() => {
  heroTimer = setInterval(() => {
    currentHero.value = (currentHero.value + 1) % heroSlides.length
  }, 4000)
})

onUnmounted(() => clearInterval(heroTimer))

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
})

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
   Hero · 嵌瓷收边 · 品牌认知优先
   ========================================== */
.hero-section {
  position: relative;
  height: 520px;
  border-radius: 20px 20px 0 0;
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

.hero-search {
  width: 100%;
  max-width: 440px;
  margin-bottom: var(--space-md);
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
}

.hero-dot.active {
  background: var(--text-inverse);
  border-color: var(--text-inverse);
  transform: scale(1.2);
}

/* ==========================================
   探索地图 · Hero 地图
   ========================================== */
.home-map-section {
  position: relative;
  margin-top: var(--space-2xl);
  margin-bottom: var(--space-3xl);
  border-radius: var(--radius-xl, 16px);
  overflow: hidden;
  box-shadow: var(--shadow-md, 0 4px 16px oklch(0.15 0.02 25 / 0.08));
}

.home-map-overlay {
  position: absolute;
  top: 24px;
  left: 24px;
  z-index: 10;
  max-width: 340px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 20px 24px;
  box-shadow: 0 4px 20px oklch(0.15 0.02 25 / 0.12);
}

.home-map-overlay h2 {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--ink, #1a1a1a);
  margin: 0 0 6px;
  font-family: var(--font-display, 'Noto Serif SC', serif);
}

.home-map-overlay p {
  font-size: 0.85rem;
  color: var(--muted, #999);
  margin: 0 0 14px;
  line-height: 1.4;
}

.home-map-overlay .el-button {
  font-weight: 600;
}

@media (max-width: 768px) {
  .home-map-section {
    border-radius: var(--radius-lg, 12px);
    margin-top: var(--space-lg);
    margin-bottom: var(--space-2xl);
  }

  .home-map-overlay {
    top: 12px;
    left: 12px;
    right: 12px;
    max-width: none;
    padding: 14px 18px;
    border-radius: 10px;
  }

  .home-map-overlay h2 {
    font-size: 1rem;
  }

  .home-map-overlay p {
    font-size: 0.78rem;
  }
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
  margin-bottom: var(--space-2xl);
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
    height: 420px;
    border-radius: 16px;
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
    grid-row: span 1;
  }
}

@media (max-width: 767px) {
  .hero-section {
    height: 400px;
    border-radius: 12px;
  }

  .hero-content {
    padding: var(--space-lg);
  }

  .hero-kicker {
    font-size: 0.75rem;
    margin-bottom: var(--space-sm);
  }

  .hero-title {
    font-size: 1.8rem;
  }

  .hero-sub {
    font-size: 0.9rem;
  }

  .hero-tag {
    font-size: 0.75rem;
    padding: 4px 12px;
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
    grid-row: span 1;
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
  .cat-card, .festival-card, .ai-btn { transition: none; }
  .more-arrow { transition: none; }
}
</style>
