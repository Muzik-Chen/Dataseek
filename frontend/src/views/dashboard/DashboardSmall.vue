<template>
  <div class="dashboard-page">
    <!-- 页面标题 · 不对称左对齐 -->
    <div class="page-header">
      <h1 class="display-text--section">📊 数据大屏</h1>
      <p>潮汕文化平台实时数据概览</p>
      <div class="section-divider section-divider--left"></div>
    </div>

    <!-- 概览卡片 -->
    <div v-if="overviewError" class="dash-error">
      <el-alert type="error" title="概览数据加载失败" :closable="false" show-icon />
      <el-button size="small" @click="loadOverview" class="retry-btn">重新加载</el-button>
    </div>
    <div v-else class="overview-cards">
      <div class="ov-card">
        <span class="ov-icon">👥</span>
        <div class="ov-info">
          <strong>{{ overview.total_users }}</strong>
          <span>注册用户</span>
        </div>
      </div>
      <div class="ov-card">
        <span class="ov-icon">🍲</span>
        <div class="ov-info">
          <strong>{{ overview.total_foods }}</strong>
          <span>美食条目</span>
        </div>
      </div>
      <div class="ov-card">
        <span class="ov-icon">🎭</span>
        <div class="ov-info">
          <strong>{{ overview.total_heritages }}</strong>
          <span>非遗项目</span>
        </div>
      </div>
      <div class="ov-card">
        <span class="ov-icon">💬</span>
        <div class="ov-info">
          <strong>{{ overview.total_posts }}</strong>
          <span>社区动态</span>
        </div>
      </div>
      <div class="ov-card">
        <span class="ov-icon">🤖</span>
        <div class="ov-info">
          <strong>{{ overview.today_chats }}</strong>
          <span>今日咨询</span>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- 热门区域 -->
      <section class="dash-section">
        <h3>🔥 热门区域</h3>
        <div class="region-list">
          <div
            v-for="(region, i) in overview.hot_regions"
            :key="i"
            class="region-item"
          >
            <span class="region-rank">{{ i + 1 }}</span>
            <div class="region-info">
              <strong>{{ region.region }}</strong>
              <span>{{ region.location_name }}</span>
            </div>
            <div class="region-stats">
              <span class="crowd-level">
                人流 {{ '🟢🟡🔴'[region.crowd_level - 1] || '🟢' }}
              </span>
              <span v-if="region.temperature">{{ region.temperature }}°C</span>
            </div>
          </div>
          <div v-if="!overview.hot_regions?.length" class="empty-row">
            <p>暂无数据</p>
          </div>
        </div>
      </section>

      <!-- 天气 -->
      <section class="dash-section">
        <h3>🌤️ 天气数据</h3>
        <div v-if="weatherData.length" class="weather-list">
          <div v-for="w in weatherData.slice(0, 8)" :key="w.id" class="weather-item">
            <span class="weather-region">{{ w.region }}</span>
            <span class="weather-temp">{{ w.temperature }}°C</span>
            <span class="weather-desc">{{ w.weather_desc }}</span>
            <span class="weather-humidity">💧 {{ w.humidity }}%</span>
          </div>
        </div>
        <div v-else-if="weatherError" class="dash-error">
          <el-alert type="error" title="天气数据加载失败" :closable="false" show-icon />
          <el-button size="small" @click="loadWeather" class="retry-btn">重新加载</el-button>
        </div>
        <div v-else class="empty-row">
          <p>暂无天气数据</p>
        </div>
      </section>

      <!-- 人流 -->
      <section class="dash-section">
        <h3>👥 实时人流</h3>
        <div v-if="crowdData.length" class="crowd-list">
          <div v-for="c in crowdData.slice(0, 8)" :key="c.id" class="crowd-item">
            <div class="crowd-location">
              <strong>{{ c.location_name }}</strong>
              <span>{{ c.region }}</span>
            </div>
            <el-progress
              :percentage="c.crowd_level * 20"
              :color="crowdColor(c.crowd_level)"
              :show-text="false"
              style="flex:1"
            />
            <span class="crowd-label">{{ crowdLabel(c.crowd_level) }}</span>
          </div>
        </div>
        <div v-else-if="crowdError" class="dash-error">
          <el-alert type="error" title="人流数据加载失败" :closable="false" show-icon />
          <el-button size="small" @click="loadCrowd" class="retry-btn">重新加载</el-button>
        </div>
        <div v-else class="empty-row">
          <p>暂无人流数据</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getWeather, getCrowd } from '@/api'

const overview = ref({
  total_users: 0,
  total_foods: 0,
  total_heritages: 0,
  total_posts: 0,
  today_chats: 0,
  hot_regions: [],
})

const weatherData = ref([])
const crowdData = ref([])

/* Error state tracking — was silent catch{} before */
const overviewError = ref(false)
const weatherError = ref(false)
const crowdError = ref(false)

function crowdColor(level) {
  if (level <= 2) return '#52c41a'
  if (level <= 3) return '#faad14'
  return '#f5222d'
}

function crowdLabel(level) {
  if (level <= 2) return '舒适'
  if (level <= 3) return '较挤'
  return '拥挤'
}

async function loadOverview() {
  overviewError.value = false
  try {
    const resp = await fetch('/api/v1/dashboard/overview')
    const data = await resp.json()
    if (data.code === 0) overview.value = data.data
  } catch {
    overviewError.value = true
  }
}

async function loadWeather() {
  weatherError.value = false
  try {
    const data = await getWeather({ limit: 24 })
    weatherData.value = Array.isArray(data) ? data : (data.items || [])
  } catch {
    weatherError.value = true
  }
}

async function loadCrowd() {
  crowdError.value = false
  try {
    const data = await getCrowd({ limit: 24 })
    crowdData.value = Array.isArray(data) ? data : (data.items || [])
  } catch {
    crowdError.value = true
  }
}

onMounted(() => {
  loadOverview()
  loadWeather()
  loadCrowd()
})
</script>

<style scoped>
.dashboard-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-md);
}

.page-header { margin-bottom: var(--space-2xl); }

.page-header h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-xs); }
.page-header p { color: var(--muted); margin: 0 0 var(--space-md); }

/* Overview cards */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-lg);
  margin-bottom: var(--space-2xl);
}

.ov-card {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-xl);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
}

.ov-icon { font-size: 32px; }

.ov-info strong { display: block; font-size: var(--fs-2xl); color: var(--ink); }
.ov-info span { font-size: var(--fs-sm); color: var(--muted); }

/* Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--space-xl);
}

.dash-section {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-xl);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
}

.dash-section h3 {
  font-size: var(--fs-lg);
  color: var(--ink);
  margin: 0 0 var(--space-lg);
}

.region-list, .weather-list, .crowd-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.region-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
}

.region-rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--brand-red);
  color: #fff;
  border-radius: 50%;
  font-size: var(--fs-xs);
  font-weight: 700;
}

.region-info { flex: 1; }
.region-info strong { display: block; color: var(--ink); font-size: var(--fs-sm); }
.region-info span { color: var(--muted); font-size: var(--fs-xs); }

.region-stats { display: flex; gap: var(--space-md); font-size: var(--fs-xs); color: var(--muted); }

.weather-item, .crowd-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  font-size: var(--fs-sm);
}

.weather-region, .crowd-location strong { color: var(--ink); font-weight: 500; min-width: 60px; }
.weather-desc { flex: 1; color: var(--muted); }
.crowd-location span { font-size: var(--fs-xs); color: var(--muted); display: block; }
.crowd-label { font-size: var(--fs-xs); color: var(--muted); min-width: 32px; text-align: right; }

.dash-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-xl);
}

.retry-btn { margin-top: var(--space-sm); }

.empty-row { text-align: center; color: var(--muted); padding: var(--space-xl); font-size: var(--fs-sm); }

@media (max-width: 768px) {
  .overview-cards { grid-template-columns: repeat(2, 1fr); }
  .dashboard-grid { grid-template-columns: 1fr; }
}
</style>
