<template>
  <div class="festival-page">
    <BackButton />
    <!-- 页面标题 · 不对称左对齐 -->
    <div class="page-hero">
      <h1 class="display-text--section">🎊 民俗节日日历</h1>
      <p>了解潮汕一年四季的重要民俗活动和节日</p>
      <div class="section-divider section-divider--left"></div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <button
        :class="['tea-pill', { active: !activeType }]"
        @click="activeType = ''; fetchEvents()"
      >全部</button>
      <button
        v-for="t in eventTypes"
        :key="t.value"
        :class="['tea-pill', { active: activeType === t.value }]"
        @click="activeType = t.value; fetchEvents()"
      >{{ t.label }}</button>

      <el-input
        v-model="keyword"
        placeholder="搜索活动..."
        :prefix-icon="Search"
        clearable
        class="search-inline"
        @keyup.enter="fetchEvents"
        @clear="fetchEvents"
      />
    </div>

    <!-- 加载中 -->
    <LoadingSkeleton v-if="loading" type="list" :count="5" />

    <!-- 空 -->
    <EmptyState v-else-if="!loading && events.length === 0" description="暂无活动数据" />

    <!-- 活动时间线 -->
    <div v-else class="event-timeline">
      <div v-for="event in events" :key="event.id" class="event-card" @click="$router.push(`/festival/${event.id}`)">
        <div class="event-date-badge">
          <span class="date-day">{{ formatLunarMonth(event.lunar_date) }}</span>
          <span class="date-month">{{ formatLunarDay(event.lunar_date) }}</span>
        </div>

        <div class="event-body">
          <el-image
            v-if="firstImageUrl(event.image_url)"
            :src="firstImageUrl(event.image_url)"
            fit="cover"
            class="event-thumb"
          />
          <div class="event-info">
            <h3>{{ event.name }}</h3>
            <p class="event-desc">{{ event.description?.slice(0, 120) || '暂无描述' }}</p>
            <div class="event-meta">
              <span v-if="event.event_date">📅 {{ formatGregorian(event.event_date) }}</span>
              <span>📍 {{ event.region }}</span>
              <el-tag :type="eventTypeTag(event.event_type)" size="small">
                {{ eventTypeLabel(event.event_type) }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        background
        @current-change="fetchEvents"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getEvents } from '@/api'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BackButton from '@/components/common/BackButton.vue'

const loading = ref(true)
const events = ref([])
const activeType = ref('')
const keyword = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const eventTypes = [
  { value: 'festival', label: '🎉 节日' },
  { value: 'event', label: '📅 活动' },
  { value: 'custom', label: '🏮 民俗' },
]

function formatLunarDay(lunarDate) {
  if (!lunarDate) return ''
  const parts = lunarDate.split('月')
  return parts.length > 1 ? parts[1] : lunarDate
}

function formatLunarMonth(lunarDate) {
  if (!lunarDate) return ''
  const parts = lunarDate.split('月')
  return parts.length > 1 ? parts[0] + '月' : lunarDate
}

function formatGregorian(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

<<<<<<< HEAD
=======
function eventTypeLabel(type) {
  return { festival: '节日', event: '活动', custom: '民俗' }[type] || type
}

function eventTypeTag(type) {
  return { festival: 'danger', event: 'primary', custom: 'success' }[type] || 'info'
}

>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
function firstImageUrl(imageUrl) {
  if (!imageUrl) return ''
  try {
    const parsed = JSON.parse(imageUrl)
    return Array.isArray(parsed) && parsed.length > 0 ? parsed[0] : imageUrl
  } catch {
    return imageUrl
  }
}

<<<<<<< HEAD
function eventTypeLabel(type) {
  return { festival: '节日', event: '活动', custom: '民俗' }[type] || type
}

function eventTypeTag(type) {
  return { festival: 'danger', event: 'primary', custom: 'success' }[type] || 'info'
}

=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
async function fetchEvents() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (activeType.value) params.event_type = activeType.value
    if (keyword.value) params.keyword = keyword.value

    const data = await getEvents(params)
    events.value = data.items || []
    total.value = data.total || 0
  } catch {
    events.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchEvents())
</script>

<style scoped>
.festival-page {
  max-width: 900px;
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
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-xl);
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-surface-alt);
  border-radius: var(--radius-lg);
}

/* tea-pill styles from global.css */

.search-inline { max-width: 240px; margin-left: auto; }

.event-timeline {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.event-card {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  background: var(--surface);
  border-radius: 12px;
  padding: var(--space-lg);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
<<<<<<< HEAD
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.event-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px oklch(0 0 0 / 0.08);
=======
  transition: transform 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94), box-shadow 0.35s ease,
    padding 0.35s ease, background 0.5s ease;
  cursor: pointer;
  position: relative;
  z-index: 1;
}

.event-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--brand-red) 0%, #e8905c 50%, var(--brand-red) 100%);
  opacity: 0;
  transition: opacity 0.5s ease;
  z-index: -1;
}

.event-card:hover {
  transform: scale(1.06);
  box-shadow: 0 12px 36px oklch(0 0 0 / 0.12);
  z-index: 10;
  padding-top: calc(var(--space-lg) * 1.3);
  padding-bottom: calc(var(--space-lg) * 1.3);
  background: linear-gradient(135deg, #fff 0%, #fff8f2 50%, #fff 100%);
}

.event-card:hover::before {
  opacity: 0.08;
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
}

.event-date-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 64px;
  height: 64px;
  background: var(--brand-red);
  color: #fff;
  border-radius: 12px;
  flex-shrink: 0;
}

.date-day { font-size: var(--fs-xl); font-weight: 700; line-height: 1; }
.date-month { font-size: var(--fs-xs); opacity: 0.85; }

.event-body {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex: 1;
  min-width: 0;
}

.event-thumb {
  width: 120px;
  height: 90px;
  border-radius: 8px;
  flex-shrink: 0;
}

.event-info { flex: 1; min-width: 0; }

.event-info h3 {
  font-size: var(--fs-lg);
  color: var(--ink);
  margin: 0 0 var(--space-xs);
}

.event-desc {
  color: var(--muted);
  font-size: var(--fs-sm);
  margin: 0 0 var(--space-sm);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.event-meta {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  font-size: var(--fs-xs);
  color: var(--muted);
  flex-wrap: wrap;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: var(--space-2xl);
}

@media (max-width: 640px) {
  .event-card { flex-direction: column; }
  .event-date-badge { flex-direction: row; gap: 4px; height: auto; padding: 8px 16px; width: auto; }
  .event-body { flex-direction: column; }
  .event-thumb { width: 100%; height: 160px; }
}
</style>
