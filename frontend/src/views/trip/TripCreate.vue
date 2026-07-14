<template>
  <div class="trip-full-page">
    <BackButton />
    <!-- ===== 悬浮侧边栏 ===== -->
    <aside
      class="map-sidebar"
      :class="{
        'sidebar--locked': sidebarLocked,
        'sidebar--expanded': sidebarHovered || sidebarLocked,
        'sidebar--wide': hasResult,
        'sidebar--mobile-open': mobilePanelOpen,
      }"
      @mouseenter="onSidebarEnter"
      @mouseleave="onSidebarLeave"
      @focusin="onSidebarFocusIn"
      @focusout="onSidebarFocusOut"
    >
      <!-- 收起态：图标列 -->
      <div class="sidebar-collapsed">
        <button class="pin-btn" :title="sidebarLocked ? '解锁侧边栏' : '锁定侧边栏'" @click="sidebarLocked = !sidebarLocked">
          {{ sidebarLocked ? '📌' : '📍' }}
        </button>
        <div class="collapsed-icons">
          <span class="ci-icon" title="出发地">🚗</span>
          <span class="ci-icon" title="人群">👥</span>
          <span class="ci-icon" title="偏好">🍲</span>
          <span class="ci-icon" title="生成">✨</span>
        </div>
      </div>

      <!-- 展开态：表单 + 结果 -->
      <div class="sidebar-expanded">
        <template v-if="!hasResult">
          <div class="sidebar-header">
            <button class="pin-btn" :title="sidebarLocked ? '解锁' : '锁定'" @click="sidebarLocked = !sidebarLocked">
              {{ sidebarLocked ? '📌' : '📍' }}
            </button>
            <h2>AI 智能行程规划</h2>
            <p>探索潮汕，定制你的专属旅程</p>
          </div>

          <!-- 单页滚动表单 -->
          <div class="sidebar-form">
            <div class="form-group">
              <label>📍 出发城市</label>
              <el-input v-model="form.origin" placeholder="如：深圳、广州" maxlength="20" size="large" />
            </div>

            <div class="form-group">
              <label>📅 行程天数</label>
              <el-input-number v-model="form.days" :min="1" :max="14" size="large" controls-position="right" />
              <span class="field-hint">建议 3-5 天可覆盖核心景点</span>
            </div>

            <div class="form-group">
              <label>💰 预算档位</label>
              <div class="budget-slider-wrap">
                <el-slider
                  v-model="form.budgetAmount"
                  :min="500"
                  :max="6000"
                  :step="100"
                  :marks="budgetMarks"
                  show-input
                  :format-tooltip="formatBudgetTooltip"
                  size="large"
                />
                <div class="budget-type-badge" :class="'budget-' + form.budget">
                  {{ budgetTypeLabel }}
                </div>
              </div>
              <span class="field-hint">拖动滑块调整预算，系统自动匹配档位</span>
            </div>

            <div class="form-group">
              <label>👥 出行人数</label>
              <div class="crowd-number-grid">
                <button
                  v-for="n in crowdNumberOptions" :key="n.value"
                  :class="['crowd-number-btn', { selected: form.crowd_type === n.value }]"
                  @click="form.crowd_type = n.value"
                >
                  {{ n.label }}
                </button>
              </div>
            </div>

            <div class="form-group">
              <label>🏷️ 兴趣偏好（多选）</label>
              <div class="pref-grid">
                <div
                  v-for="p in prefOptions" :key="p.value"
                  :class="['pref-card', { on: form.preferences.includes(p.value) }]"
                  @click="togglePref(p.value)"
                >
                  <span class="pref-label">{{ p.label }}</span>
                </div>
              </div>
              <div v-if="form.preferences.length === 0" class="pref-warning">
                ⚠️ 请至少选择一项偏好
              </div>
            </div>

            <div class="form-group">
              <label>📝 行程名称</label>
              <el-input v-model="form.title" placeholder="如：潮汕三日美食之旅" maxlength="100" size="large" />
            </div>

            <button
              class="generate-btn"
              :disabled="!canGenerate || generating"
              @click="generatePlan"
            >
              <el-icon v-if="generating" class="is-loading"><Loading /></el-icon>
              <span v-if="generating">AI 正在规划中...</span>
              <span v-else>✨ AI 智能规划</span>
            </button>
          </div>
        </template>

        <!-- AI 结果区 (600px 时显示) -->
        <div v-else class="sidebar-result">
          <div class="result-header">
            <button class="back-btn" @click="resetForm">
              ← 返回编辑
            </button>
          </div>

          <div class="result-map">
            <MapContainer
              ref="resultMapRef"
              height="280px"
              :center="mapResultData.center"
              :markers="mapResultData.markers"
              :heatmapData="mapResultData.heatmapData"
              :enableZoomFilter="true"
              :enableHoverInfo="true"
              :heatmapMinZoom="15"
              :interactive="true"
              :showRouteLegend="false"
              :showCongestionLegend="false"
              @plan-legend-click="onLegendClick"
              @ready="onResultMapReady"
            />
          </div>

          <!-- 流式叙述文本 -->
          <div v-if="generating && streamNarration" class="stream-narration">
            <p>{{ streamNarration }}</p>
          </div>

          <!-- 离线方案警告 -->
          <div v-if="planResult?._offline" class="offline-banner">
            ⚠️ AI 暂不可用，当前为离线演示方案，部分信息可能不准确
          </div>

          <template v-if="planResult?.plans?.length">
            <TripCard
              :plans="planResult.plans"
              :savingEnabled="savingEnabled"
              :activePlanId="activeResultPlanId"
              @save="savePlan"
              @refresh="regeneratePlan"
              @refine="openRefinePanel"
              @export="exportPlanImage"
              @plan-change="onPlanTabChange"
            />

            <!-- Refinement 调整面板（内嵌于结果区，避免破坏 v-if 链） -->
            <div v-if="showRefinePanel" class="refine-panel">
              <div class="refine-panel__header">
                <span>✏️ 调整方案</span>
                <button class="refine-close-btn" @click="closeRefinePanel">✕</button>
              </div>

              <!-- 快捷操作按钮 -->
              <div class="refine-quick-actions">
                <button
                  v-for="q in quickRefineOptions"
                  :key="q.label"
                  class="refine-quick-btn"
                  @click="fillRefineInput(q.text)"
                >{{ q.icon }} {{ q.label }}</button>
              </div>

              <!-- 自由文本输入 -->
              <div class="refine-input-row">
                <el-input
                  v-model="refineInput"
                  placeholder="试试：把第二天的酒店换成300以内的"
                  maxlength="500"
                  @keyup.enter="sendRefine"
                />
                <el-button
                  type="primary"
                  size="small"
                  :disabled="!refineInput.trim() || refining"
                  :loading="refining"
                  @click="sendRefine"
                >发送→</el-button>
              </div>

              <!-- 调整结果预览 -->
              <div v-if="refineStreamPlan" class="refine-result">
                <div class="refine-result__summary">{{ refineStreamPlan.summary || '调整完成' }}</div>
                <div class="refine-result__actions">
                  <el-button size="small" @click="undoRefine">↩ 撤销</el-button>
                  <el-button size="small" type="primary" @click="confirmRefine">✅ 确认替换</el-button>
                </div>
              </div>
            </div>
          </template>

          <div v-else-if="planResult?.days?.length" class="plan-fallback">
            <div class="plan-days-compact">
              <div v-for="day in planResult.days" :key="day.day" class="plan-day-compact">
                <div class="plan-day-head">
                  <span class="day-badge">Day {{ day.day }}</span>
                  <strong>{{ day.title }}</strong>
                </div>
                <div class="plan-day-spots">
                  <div v-for="spot in day.spots" :key="spot.name" class="plan-spot">
                    <span class="spot-dur">{{ spot.duration }}</span>
                    <span class="spot-name">{{ spot.name }}</span>
                    <el-tag size="small">{{ spot.type }}</el-tag>
                  </div>
                </div>
              </div>
            </div>
            <div class="result-actions">
              <el-button type="primary" @click="savePlan()">💾 保存行程</el-button>
              <el-button @click="regeneratePlan">🔄 重新生成</el-button>
            </div>
          </div>

          <!-- 生成中 loading 态：不显示失败提示 -->
          <div v-else-if="generating" class="plan-generating">
            <el-icon class="is-loading" :size="32"><Loading /></el-icon>
            <p>AI 正在为您生成方案，请稍候...</p>
            <p class="plan-generating__sub">{{ streamNarration || '正在连接 AI 服务...' }}</p>
          </div>
          <!-- 真正失败：生成已完成但无结果 -->
          <div v-else class="plan-empty">
            <p>😕 AI 未能成功生成方案，请重试</p>
            <el-button type="primary" @click="regeneratePlan">重新生成</el-button>
          </div>
        </div>
      </div>
    </aside>

    <!-- ===== 全屏地图 ===== -->
    <div class="map-main">
      <div v-if="discoveryLoading" class="map-loading-overlay">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>正在加载探索地图...</p>
      </div>
      <MapContainer
        v-else
        ref="discoveryMapRef"
        height="100%"
        :center="discoveryMapData.center"
        :zoom="11"
        :markers="discoveryMapData.markers"
        :heatmapData="discoveryMapData.heatmapData"
        :enableZoomFilter="true"
        :enableHoverInfo="true"
        :heatmapMinZoom="15"
        :interactive="true"
        :showRouteLegend="hasResult"
        :planRouteLegend="routeLegend"
        :highlightedPlanId="activeResultPlanId"
        :showCongestionLegend="discoveryDriving.hasCongestion.value"
        @plan-legend-click="onLegendClick" @ready="onDiscoveryMapReady"
      />

      <!-- 方案路线切换条 -->
      <div v-if="hasResult" class="route-switcher">
        <button
          v-for="item in routeLegend"
          :key="item.planId"
          :class="['rs-btn', { 'rs-btn--active': activeResultPlanId === item.planId }]"
          @click="onLegendClick(item.planId)"
        >
          <span class="rs-dot" :style="{ background: item.color }"></span>
          {{ item.label }}
        </button>
      </div>
      <!-- 底部统计栏 -->
      <div class="map-stats-bar">
        <span>🍲 {{ discoveryStats.foodCount }}家美食</span>
        <span class="stat-sep">·</span>
        <span>🏛️ {{ discoveryStats.heritageCount }}项非遗</span>
        <span class="stat-sep">·</span>
        <span>🎭 {{ discoveryStats.eventCount }}场民俗</span>
        <span class="stat-sep">·</span>
        <span>🏨 {{ discoveryStats.hotelCount }}家酒店</span>
        <span class="stat-sep">·</span>
        <span>👥 {{ discoveryStats.crowdCount }}个热门点</span>
      </div>
    </div>

    <!-- ===== 移动端底部标签栏 ===== -->
    <div class="mobile-tab-bar" @click="mobilePanelOpen = !mobilePanelOpen">
      <span>🚗 出发</span>
      <span>👥 人群</span>
      <span>🍲 偏好</span>
      <span :class="{ 'tab-generate': canGenerate }">✨ {{ generating ? '规划中' : '生成' }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { foodApi } from '@/api/food'
import { heritageApi } from '@/api/heritage'
import { eventApi } from '@/api/event'
import { hotelApi } from '@/api/hotel'
import { dashboardApi } from '@/api/dashboard'
import { tripApi } from '@/api/trip'
import { useSSE, streamFetch } from '@/composables/useSSE'
import { exportTripWithMap } from '@/composables/useExport'
import TripCard from '@/components/business/TripCard.vue'
import MapContainer from '@/components/common/MapContainer.vue'
import BackButton from '@/components/common/BackButton.vue'
import { planToMapData, platformDataToMapData, extractPlanWaypoints } from '@/utils/mapAdapter'
import { useRouteDriving, PLAN_COLORS } from '@/composables/useRouteDriving'
import { useTripStore } from '@/stores/trip'

const router = useRouter()
const tripStore = useTripStore()

// ── 侧边栏状态 ──
const sidebarHovered = ref(false)
const sidebarLocked = ref(false)
const sidebarFocused = ref(false)
const mobilePanelOpen = ref(false)

let leaveTimer = null
function onSidebarEnter() {
  clearTimeout(leaveTimer)
  sidebarHovered.value = true
}
function onSidebarLeave() {
  if (sidebarLocked.value) return
  if (sidebarFocused.value) return  // typing in sidebar: don't collapse
  leaveTimer = setTimeout(() => { sidebarHovered.value = false }, 300)
}
function onSidebarFocusIn() {
  sidebarFocused.value = true
  sidebarHovered.value = true  // ensure expanded when focusing via keyboard
}
function onSidebarFocusOut(e) {
  // Only clear if focus truly left the sidebar (not moved to another child)
  if (!e.currentTarget.contains(e.relatedTarget)) {
    sidebarFocused.value = false
  }
}

// ── 表单（从 localStorage 恢复或使用默认值）──
const form = reactive({
  title: tripStore.hasSavedPlans ? tripStore.form.title : '',
  origin: tripStore.hasSavedPlans ? tripStore.form.origin : '广州',
  days: tripStore.hasSavedPlans ? tripStore.form.days : 3,
  budgetAmount: tripStore.hasSavedPlans && tripStore.form.budgetAmount ? tripStore.form.budgetAmount : 2000,
  crowd_type: tripStore.hasSavedPlans ? tripStore.form.crowd_type : '2',
  preferences: tripStore.hasSavedPlans && tripStore.form.preferences?.length
    ? tripStore.form.preferences : ['美食', '非遗'],
  get budget() {
    if (this.budgetAmount <= 2000) return 'low'
    if (this.budgetAmount <= 4500) return 'mid'
    return 'high'
  },
})

const budgetTypeLabel = computed(() => {
  if (form.budget === 'low') return '经济型'
  if (form.budget === 'mid') return '舒适型'
  return '豪华型'
})

const budgetMarks = {
  500: '500',
  2000: '2000',
  4500: '4500',
  6000: '6000',
}

function formatBudgetTooltip(val) {
  return '¥' + val + ' / 人'
}

const canGenerate = computed(() =>
  form.days >= 1 && form.days <= 14 &&
  form.crowd_type &&
  form.preferences.length > 0 &&
  form.title.trim()
)

// ── AI 生成（SSE 流式）──
const { streamTripPlan, abort: abortSSE } = useSSE()
const discoveryMapRef = ref(null)
const discoveryMapInst = ref(null)
const resultMapInst = ref(null)
const resultMapRef = ref(null)
const tripCardRef = ref(null)
const generating = ref(false)
const streamPlans = ref(tripStore.hasSavedPlans ? [...tripStore.streamPlans] : [])
const streamNarration = ref(tripStore.streamNarration || '')
const savingEnabled = ref(false)
const hasBeenSaved = ref(false)
const draftId = ref(tripStore.draftId || null)
const offlineFallback = ref(null)
const activeResultPlanId = ref(tripStore.activeResultPlanId || null)

// ── 自动持久化：关键状态变更 → 写入 store → localStorage ──
watch(form, () => { tripStore.form = { ...form } }, { deep: true })
watch(streamPlans, () => { tripStore.streamPlans = [...streamPlans.value] }, { deep: true })
watch(streamNarration, (val) => { tripStore.streamNarration = val })
watch(activeResultPlanId, (val) => { tripStore.activeResultPlanId = val })

// ── 防御性路线恢复：streamPlans 变化时补绘遗漏路线 ──
watch(
  () => streamPlans.value.length,
  () => {
    const map = discoveryMapInst.value
    if (!map) return
    for (const plan of streamPlans.value) {
      if (plan.plan_id && !plan.error && !discoveryDriving.planRoutes.value[plan.plan_id]) {
        const waypoints = extractPlanWaypoints(plan)
        if (waypoints.length >= 2) {
          discoveryDriving.addPlanRoute(plan.plan_id, waypoints, form.origin)
        }
      }
    }
  }
)

// 路线驾驶实例（全屏地图 + 侧边栏小地图）
const discoveryDriving = useRouteDriving(discoveryMapInst)
const resultDriving = useRouteDriving(resultMapInst)

const planResult = computed(() => {
  if (offlineFallback.value) return offlineFallback.value
  if (streamPlans.value.length > 0 || generating.value) {
    // Sort by plan_id (A→B→C) so tabs always display in consistent order
    const sorted = [...streamPlans.value].sort((a, b) =>
      (a.plan_id || '').localeCompare(b.plan_id || '')
    )
    return { plans: sorted }
  }
  return null
})

const hasResult = computed(() => planResult.value !== null)

// ── 结果地图 ──
function onPlanTabChange(plan) {
  const planId = plan?.plan_id || null
  activeResultPlanId.value = planId
  // 同步路线高亮到两张地图
  if (planId) {
    discoveryDriving.highlightPlan(planId)
    resultDriving.highlightPlan(planId)
  } else {
    discoveryDriving.resetHighlight()
    resultDriving.resetHighlight()
  }
}

// 地图路线图例点击 → 同步到 TripCard Tab
function onLegendClick(planId) {
  activeResultPlanId.value = planId
  discoveryDriving.highlightPlan(planId)
  resultDriving.highlightPlan(planId)
}

// 全屏地图就绪后，保存 AMap 实例 + 恢复之前持久化的路线
function onDiscoveryMapReady(map) {
  discoveryMapInst.value = map
  console.log("[TripCreate] 全屏地图就绪，AMap 实例已保存")
  // 从持久化方案中恢复路线
  for (const plan of streamPlans.value) {
    if (plan.plan_id && !plan.error) {
      const waypoints = extractPlanWaypoints(plan)
      if (waypoints.length >= 2) {
        console.log(`[TripCreate] 恢复路线 plan=${plan.plan_id} waypoints=${waypoints.length}`)
        discoveryDriving.addPlanRoute(plan.plan_id, waypoints, form.origin)
      }
    }
  }
}

// 结果地图就绪后，保存实例并重放全屏地图已有的路线
function onResultMapReady(map) {
  resultMapInst.value = map
  const routes = discoveryDriving.planRoutes.value
  for (const [planId, route] of Object.entries(routes)) {
    if (route.waypoints && !resultDriving.planRoutes.value[planId]) {
      console.log(`[TripCreate] 结果地图就绪，重放路线 plan=${planId}`)
      resultDriving.addPlanRoute(planId, route.waypoints, form.origin)
    }
  }
}

const currentResultPlan = computed(() => {
  const plans = planResult.value?.plans
  if (!plans?.length) return null
  if (activeResultPlanId.value) {
    return plans.find(p => p.plan_id === activeResultPlanId.value) || plans[0]
  }
  return plans[0]
})

const mapResultData = computed(() => {
  if (!currentResultPlan.value) return { center: [116.68, 23.35], markers: [], routeLine: [], heatmapData: [] }
  return planToMapData(currentResultPlan.value)
})

// 路线方案图例数据
const routeLegend = computed(() => {
  return streamPlans.value
    .filter(p => p.plan_id && !p.error)
    .map(p => ({
      planId: p.plan_id,
      color: PLAN_COLORS[p.plan_id] || '#3366FF',
      label: `方案${p.plan_id}`,
    }))
})

// ── 选项数据 ──
const crowdNumberOptions = [
  { value: '1', label: '1人' },
  { value: '2', label: '2人' },
  { value: '3', label: '3人' },
  { value: '4', label: '4人' },
  { value: '5', label: '5人' },
  { value: '6', label: '6人' },
  { value: '7+', label: '7人及以上' },
]

const prefOptions = [
  { value: '美食', label: '美食探索' },
  { value: '非遗', label: '非遗文化' },
  { value: '自然', label: '自然风光' },
  { value: '历史', label: '历史古迹' },
  { value: '民俗', label: '民俗体验' },
  { value: '购物', label: '特产购物' },
]

function togglePref(val) {
  const idx = form.preferences.indexOf(val)
  if (idx > -1) form.preferences.splice(idx, 1)
  else form.preferences.push(val)
}

// ── 平台探索数据 ──
const discoveryLoading = ref(true)
const discoveryData = reactive({
  foods: [],
  heritages: [],
  events: [],
  hotels: [],
  crowd: [],
  weather: [],
})

const discoveryMapData = computed(() => platformDataToMapData(discoveryData))

const discoveryStats = computed(() => ({
  foodCount: discoveryData.foods.length,
  heritageCount: discoveryData.heritages.length + discoveryData.events.length,
  eventCount: discoveryData.events.length,
  hotelCount: discoveryData.hotels.length,
  crowdCount: discoveryData.crowd.length,
}))

// 四个城市的固定坐标（weatherGeo 不返回坐标，需前端补充）
const WEATHER_CITIES = [
  { lat: 23.3541, lng: 116.6822, name: '汕头' },
  { lat: 23.6640, lng: 116.6390, name: '潮州' },
  { lat: 23.5480, lng: 116.3700, name: '揭阳' },
  { lat: 22.7860, lng: 115.3750, name: '汕尾' },
]

onMounted(async () => {
  try {
    const [foodsRes, heritagesRes, eventsRes, hotelsRes, crowdRes,
      swRes, czRes, jyRes, sw2Res] = await Promise.all([
      foodApi.list({ page_size: 100 }),
      heritageApi.list({ page_size: 100 }),
      eventApi.list({ page_size: 100 }),
      hotelApi.list({ page_size: 100 }),
      dashboardApi.crowdGeo(),
      dashboardApi.weatherGeo({ lat: WEATHER_CITIES[0].lat, lng: WEATHER_CITIES[0].lng }),
      dashboardApi.weatherGeo({ lat: WEATHER_CITIES[1].lat, lng: WEATHER_CITIES[1].lng }),
      dashboardApi.weatherGeo({ lat: WEATHER_CITIES[2].lat, lng: WEATHER_CITIES[2].lng }),
      dashboardApi.weatherGeo({ lat: WEATHER_CITIES[3].lat, lng: WEATHER_CITIES[3].lng }),
    ])

    discoveryData.foods = foodsRes?.items || []
    discoveryData.heritages = heritagesRes?.items || []
    discoveryData.events = eventsRes?.items || []
    discoveryData.hotels = hotelsRes?.items || []
    discoveryData.crowd = crowdRes || []

    // 天气数据补充坐标
    const weatherResults = [swRes, czRes, jyRes, sw2Res]
    discoveryData.weather = weatherResults
      .map((res, i) => res ? { ...res, lat: WEATHER_CITIES[i].lat, lng: WEATHER_CITIES[i].lng } : null)
      .filter(Boolean)
  } catch (e) {
    console.warn('探索地图数据加载失败:', e)
  } finally {
    discoveryLoading.value = false
  }
})

// ── 离开确认 ──
onBeforeRouteLeave((to, from, next) => {
  // AI 生成中 → 强制阻止
  if (generating.value) {
    ElMessage.warning('AI 正在生成方案中，请等待完成后再离开')
    next(false)
    return
  }
  // 无结果或已手动保存 → 放行
  if (!hasResult.value || hasBeenSaved.value) {
    next()
    return
  }
  // 有未保存方案 → 确认
  ElMessageBox.confirm(
    '当前有未保存的 AI 行程方案，确定离开吗？（方案会自动保留，下次回来仍可查看）',
    '提示',
    { confirmButtonText: '离开', cancelButtonText: '留下', type: 'warning' }
  ).then(() => next()).catch(() => next(false))
})

// ── 清理 ──
onBeforeUnmount(() => {
  // SSE abort is handled by useSSE
})

// ── 自动保存草稿 ──
async function autoSaveDraft() {
  if (draftId.value) return  // 已存过
  const validPlans = streamPlans.value.filter(p => !p.error)
  if (validPlans.length === 0) return
  try {
    const res = await tripApi.saveDraft({
      title: form.title,
      days: form.days,
      crowd_type: form.crowd_type,
      preferences: form.preferences,
      plan_content: { plans: validPlans, origin: form.origin },
    })
    draftId.value = res.id
    tripStore.draftId = res.id
  } catch { /* 静默失败 */ }
}

// ── 生成逻辑（SSE 流式）──
async function generatePlan() {
  if (!form.title) { ElMessage.warning('请输入行程标题'); return }
  if (!form.preferences.length) { ElMessage.warning('请至少选一项偏好'); return }

  // 中断上一个 SSE 流（如果还在跑，防止并发）
  abortSSE()
  generating.value = true
  savingEnabled.value = false
  streamPlans.value = []
  streamNarration.value = ''
  offlineFallback.value = null
  activeResultPlanId.value = null
  draftId.value = null
  tripStore.draftId = null
  discoveryDriving.clearAll()
  resultDriving.clearAll()

  try {
    await streamTripPlan({
      origin: form.origin,
      days: form.days,
      crowd_type: form.crowd_type,
      interests: form.preferences,
      budget: form.budget,
    }, {
      onThinking(label) {
        // 流式追加而非覆盖，让用户看到渐进进度
        if (streamNarration.value) {
          streamNarration.value += '\n' + label
        } else {
          streamNarration.value = label
        }
      },
      onToken(content) {
        streamNarration.value += content
      },
      onTripCard(plan) {
        const planId = plan?.plan_id
        // Progressive display: if plan already exists, update with enrichment
        const idx = planId ? streamPlans.value.findIndex(p => p.plan_id === planId) : -1
        if (idx !== -1) {
          streamPlans.value[idx] = { ...streamPlans.value[idx], ...plan }
          streamPlans.value = [...streamPlans.value]  // trigger reactivity
        } else {
          streamPlans.value = [...streamPlans.value, plan]
        }
        // 当计划含 route_geo 时，增量添加路线到两张地图
        const waypoints = extractPlanWaypoints(plan)
        console.log(`[TripCreate] plan=${planId} has_route_geo=${!!plan?.route_geo} waypoints=${waypoints.length} sample=`, waypoints.slice(0, 3))
        if (waypoints.length >= 2 && planId) {
          console.log(`[TripCreate] → addPlanRoute plan=${planId} discRef=${!!discoveryMapRef.value} resRef=${!!resultMapRef.value} resMap=${!!resultMapRef.value?.map}`)
          discoveryDriving.addPlanRoute(planId, waypoints, form.origin)
          resultDriving.addPlanRoute(planId, waypoints, form.origin)
        }
      },
      onPlanFailed(data) {
        console.warn(`[TripCreate] 方案 ${data.theme_id} 生成失败:`, data.error)
        ElMessage.warning(`方案${data.theme_id}生成失败: ${data.error || '未知错误'}`)
        // 插入错误标记项，让 onDone 能正确统计失败数
        streamPlans.value = [...streamPlans.value, {
          plan_id: data.theme_id,
          theme: data.theme,
          error: true,
        }]
      },
      onDone() {
        generating.value = false
        savingEnabled.value = true
        const count = streamPlans.value.length
        const errorCount = streamPlans.value.filter(p => p.error).length
        if (count > 0 && errorCount < count) {
          ElMessage.success(`行程规划完成！共生成 ${count} 套方案`)
        } else if (errorCount === count) {
          ElMessage.warning(`行程生成遇到问题（${errorCount}/${count} 失败），可尝试重新生成`)
        } else {
          ElMessage.warning('未能生成方案，请重试')
          offlineFallback.value = mockPlan()
        }
        autoSaveDraft()
      },
      onError(msg) {
        console.error('[TripCreate] SSE error:', msg)
        // 如果已有部分方案，不降级
        if (streamPlans.value.length === 0) {
          offlineFallback.value = mockPlan()
          ElMessage.info('已生成演示行程（离线模式）')
        }
        generating.value = false
      },
    })
  } catch (e) {
    console.error('[TripCreate] generatePlan exception:', e)
    if (streamPlans.value.length === 0) {
      offlineFallback.value = mockPlan()
      ElMessage.info('已生成演示行程（离线模式）')
    }
    generating.value = false
  }
}

function regeneratePlan() {
  tripStore.clearAll()
  streamPlans.value = []
  streamNarration.value = ''
  offlineFallback.value = null
  discoveryDriving.clearAll()
  resultDriving.clearAll()
  generatePlan()
}

async function resetForm() {
  // 第一次确认：放弃当前方案
  try {
    await ElMessageBox.confirm(
      '确定要放弃当前行程方案吗？此操作不可恢复。',
      '确认返回',
      { confirmButtonText: '确定放弃', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return  // 用户取消
  }

  // 第二次确认（仅当有草稿时）：是否同步删除个人中心草稿
  if (draftId.value) {
    try {
      await ElMessageBox.confirm(
        '是否同时删除个人中心的草稿记录？选择"保留"可在个人中心继续查看。',
        '草稿处理',
        { confirmButtonText: '删除草稿', cancelButtonText: '保留草稿', type: 'warning' }
      )
      // 用户选择删除
      try { await tripApi.delete(draftId.value) } catch { /* ignore */ }
    } catch {
      // 用户选择保留 — 什么都不做，草稿留在数据库
    }
    draftId.value = null
    tripStore.draftId = null
  }

  tripStore.clearAll()
  streamPlans.value = []
  streamNarration.value = ''
  offlineFallback.value = null
  savingEnabled.value = false
  sidebarLocked.value = false
  activeResultPlanId.value = null
  showRefinePanel.value = false
  hasBeenSaved.value = false
  discoveryDriving.clearAll()
  resultDriving.clearAll()
}

// ── Refinement 调整 ──
const showRefinePanel = ref(false)
const refining = ref(false)
const refineInput = ref('')
const refineStreamPlan = ref(null)
const previousPlan = ref(null)

const quickRefineOptions = [
  { icon: '🏨', label: '换酒店', text: '把酒店换成更便宜的' },
  { icon: '📍', label: '加景点', text: '在第二天多加一个景点' },
  { icon: '💰', label: '调预算', text: '把预算降低一些' },
  { icon: '⚡', label: '更轻松', text: '行程节奏太紧了，每天减少一些活动，安排得更轻松悠闲' },
  { icon: '🏃', label: '更紧凑', text: '行程太松了，每天多安排1-2个景点' },
  { icon: '🔄', label: '调顺序', text: '重新安排每天的游览顺序，让路线更合理' },
]

function openRefinePanel(plan) {
  showRefinePanel.value = true
  refineInput.value = ''
  refineStreamPlan.value = null
  previousPlan.value = JSON.parse(JSON.stringify(plan)) // 深拷贝
}

function closeRefinePanel() {
  showRefinePanel.value = false
  refineInput.value = ''
  refineStreamPlan.value = null
  previousPlan.value = null
}

function fillRefineInput(text) {
  refineInput.value = text
}

async function sendRefine() {
  const request = refineInput.value.trim()
  if (!request) return

  const currentPlan = planResult.value?.plans?.find(
    p => p.plan_id === (previousPlan.value?.plan_id || 'A')
  )
  if (!currentPlan) { ElMessage.warning('没有可调整的方案'); return }

  refining.value = true
  refineStreamPlan.value = null

  const base = import.meta.env.VITE_API_BASE || '/api/v1'

  try {
    await streamFetch(`${base}/trip/plan/refine`, {
      plan: currentPlan,
      request,
    }, {
      onThinking(label) {
        // refinement narration
      },
      onToken(content) {
        // could show streaming thoughts
      },
      onTripCard(plan) {
        refineStreamPlan.value = plan
      },
      onDone() {
        refining.value = false
      },
      onError(msg) {
        ElMessage.error(`调整失败: ${msg}`)
        refining.value = false
      },
    })
  } catch (e) {
    ElMessage.error('调整请求失败，请重试')
    refining.value = false
  }
}

function confirmRefine() {
  if (!refineStreamPlan.value || !previousPlan.value) return
  const idx = streamPlans.value.findIndex(
    p => p.plan_id === refineStreamPlan.value.plan_id
  )
  if (idx !== -1) {
    // 浅拷贝触发 computed 重算
    const updated = [...streamPlans.value]
    updated[idx] = { ...refineStreamPlan.value }
    streamPlans.value = updated
  } else {
    // 新 plan_id → 追加
    streamPlans.value = [...streamPlans.value, refineStreamPlan.value]
  }
  previousPlan.value = null
  refineStreamPlan.value = null
  refineInput.value = ''
  ElMessage.success('方案已更新')
}

function undoRefine() {
  refineStreamPlan.value = null
  // previousPlan 保留在 streamPlans 中，未被替换
  ElMessage.info('已撤销调整')
}

async function savePlan(selectedPlan) {
  const plan = selectedPlan || (planResult.value?.plans?.[0])
  if (!plan && !planResult.value?.days) {
    ElMessage.warning('没有可保存的行程')
    return
  }
  try {
    const payload = {
      title: form.title || plan?.title || plan?.theme || 'AI 行程方案',
      days: form.days,
      crowd_type: form.crowd_type,
      preferences: form.preferences,
      plan_content: plan
        ? { plans: [plan], enrichment: plan.enrichment || null, route_geo: plan.route_geo || null }
        : { plans: [], ...planResult.value },
    }
    if (draftId.value) {
      // 升级草稿 → 正式方案
      await tripApi.updatePlan(draftId.value, { ...payload, status: 'generated' })
      draftId.value = null
      tripStore.draftId = null
    } else {
      await tripApi.importPlan(payload)
    }
    hasBeenSaved.value = true
    ElMessage.success('行程已保存！可在个人中心查看')
  } catch {
    ElMessage.error('保存失败，请重试')
  }
}

async function exportPlanImage(plan) {
  if (!plan) { ElMessage.warning('没有可导出的方案'); return }
  try {
    await exportTripWithMap(resultMapRef.value, tripCardRef.value?.$el, `潮汕行程_${plan.title || plan.plan_id || '方案'}.png`)
    ElMessage.success('行程图片已导出')
  } catch {
    ElMessage.error('导出失败，请重试')
  }
}

function mockPlan() {
  return {
    _offline: true,
    days: [
      { day: 1, title: '汕头老城 · 美食初探', spots: [
        { name: '小公园骑楼群', type: '景点', duration: '1.5小时', tip: '拍摄骑楼最佳时间在上午' },
        { name: '八合里海记牛肉火锅', type: '美食', duration: '1小时', tip: '吊龙和匙柄是必点' },
        { name: '西堤公园', type: '景点', duration: '1小时', tip: '傍晚看日落位置绝佳' },
      ]},
      { day: 2, title: '潮州古城 · 非遗之旅', spots: [
        { name: '广济桥', type: '景点', duration: '1.5小时', tip: '中国四大古桥之一' },
        { name: '工夫茶体验馆', type: '体验', duration: '1.5小时', tip: '学习二十一式冲泡法' },
        { name: '牌坊街', type: '街区', duration: '2小时', tip: '品尝地道小吃' },
      ]},
      { day: 3, title: '南澳岛 · 海岛风光', spots: [
        { name: '青澳湾', type: '景点', duration: '2小时', tip: '广东最美的海湾之一' },
        { name: '南澳总兵府', type: '历史', duration: '1小时', tip: '明清海防重地' },
        { name: '海鲜大排档', type: '美食', duration: '1.5小时', tip: '现捞现做' },
      ]},
    ],
    tips: ['潮汕秋冬季节（10月-次年4月）是最佳旅游时间', '牛肉火锅建议午餐去，牛肉最新鲜', '部分非遗体验项目需提前预约'],
    crowd_label: crowdOptions.find(c => c.value === form.crowd_type)?.label || '',
    preferences: form.preferences,
  }
}
</script>

<style scoped>
/* ==========================================
   全屏布局
   ========================================== */
.trip-full-page {
  display: flex;
  height: calc(100vh - var(--header-height, 64px));
  position: relative;
  overflow: hidden;
}

/* ==========================================
   侧边栏 — 3 态宽度过渡
   ========================================== */
.map-sidebar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 1000;
  width: 60px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid oklch(0 0 0 / 0.08);
  box-shadow: 4px 0 24px oklch(0.15 0.02 25 / 0.10);
  transition: width 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
  display: flex;
  overflow: hidden;
}

.map-sidebar.sidebar--expanded {
  width: 420px;
}

.map-sidebar.sidebar--expanded.sidebar--wide {
  width: 600px;
}

/* ── 收起态图标列 ── */
.sidebar-collapsed {
  width: 60px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 12px;
  gap: 20px;
}

.sidebar--expanded .sidebar-collapsed {
  display: none;
}

.pin-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid oklch(0 0 0 / 0.1);
  background: var(--surface, #fff);
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, border-color 0.2s;
  flex-shrink: 0;
}

.sidebar--locked .pin-btn {
  background: oklch(0.53 0.22 25 / 0.1);
  border-color: var(--brand-red, oklch(0.53 0.22 25));
}

.collapsed-icons {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  flex: 1;
}

.ci-icon {
  font-size: 20px;
  cursor: default;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.ci-icon:hover {
  opacity: 1;
}

/* ── 展开态内容区 ── */
.sidebar-expanded {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  display: none;
  padding: 20px;
}

.sidebar--expanded .sidebar-expanded {
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid oklch(0 0 0 / 0.06);
}

.sidebar-header h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--ink, #1a1a1a);
  margin: 10px 0 4px;
  font-family: var(--font-display, 'Noto Serif SC', serif);
}

.sidebar-header p {
  font-size: 0.82rem;
  color: var(--muted, #999);
  margin: 0;
}

/* ── 单页表单 ── */
.sidebar-form {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  display: block;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--ink, #1a1a1a);
  margin-bottom: 6px;
}

.field-hint {
  display: inline-block;
  font-size: 0.75rem;
  color: var(--muted, #999);
  margin-left: 10px;
  vertical-align: middle;
}

/* 预算滑块 */
.budget-slider-wrap {
  padding: 8px 4px 0;
}
.budget-type-badge {
  margin-top: 8px;
  display: inline-block;
  padding: 6px 18px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 700;
  color: #fff;
  transition: all 0.3s;
}
.budget-type-badge.budget-low {
  background: linear-gradient(135deg, #67c23a, #529b2e);
}
.budget-type-badge.budget-mid {
  background: linear-gradient(135deg, #e6a23c, #cf8e2e);
}
.budget-type-badge.budget-high {
  background: linear-gradient(135deg, #c4565d, #b03a42);
}

/* 人数选择 */
.crowd-number-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.crowd-number-btn {
  flex: 1;
  min-width: 56px;
  padding: 12px 8px;
  border: 2px solid oklch(0 0 0 / 0.08);
  border-radius: 12px;
  cursor: pointer;
  background: #fff;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--ink);
  transition: all 0.2s;
  text-align: center;
}
.crowd-number-btn:hover {
  border-color: oklch(0.55 0.18 28 / 0.3);
  background: oklch(0.55 0.18 28 / 0.03);
}
.crowd-number-btn.selected {
  border-color: var(--brand-red, oklch(0.53 0.22 25));
  background: oklch(0.53 0.22 25 / 0.06);
  color: var(--brand-red, oklch(0.53 0.22 25));
  box-shadow: 0 0 0 3px oklch(0.53 0.22 25 / 0.08);
}

/* 偏好网格 */
.pref-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.pref-card {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px 8px;
  border: 2px solid oklch(0 0 0 / 0.08);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.pref-card:hover {
  border-color: oklch(0.55 0.18 28 / 0.25);
}

.pref-card.on {
  border-color: var(--brand-red, oklch(0.53 0.22 25));
  background: oklch(0.53 0.22 25 / 0.06);
}

.pref-label { font-size: 0.95rem; font-weight: 700; color: var(--ink); }

.pref-warning {
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--accent, #f56c6c);
  text-align: center;
}

/* 生成按钮 */
.generate-btn {
  width: 100%;
  padding: 12px 20px;
  margin-top: 12px;
  border: none;
  border-radius: 12px;
  background: var(--gradient-porcelain, linear-gradient(135deg, oklch(0.53 0.22 25), oklch(0.63 0.18 35)));
  color: #fff;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: opacity 0.2s, transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 16px oklch(0.53 0.22 25 / 0.3);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 24px oklch(0.53 0.22 25 / 0.4);
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── AI 结果区 ── */
.sidebar-result {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid oklch(0 0 0 / 0.06);
}

.back-btn {
  background: none;
  border: 1px solid oklch(0 0 0 / 0.12);
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 0.85rem;
  color: var(--ink);
  cursor: pointer;
  transition: background 0.2s;
}

.back-btn:hover {
  background: oklch(0 0 0 / 0.04);
}

.result-map {
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 12px;
  box-shadow: var(--shadow-sm, 0 2px 8px oklch(0 0 0 / 0.06));
}

.plan-fallback {
  flex: 1;
  overflow-y: auto;
}

.plan-days-compact {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.plan-day-compact {
  border: 1px solid oklch(0 0 0 / 0.07);
  border-radius: 10px;
  padding: 12px;
}

.plan-day-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.day-badge {
  background: var(--brand-red, oklch(0.53 0.22 25));
  color: #fff;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
}

.plan-day-head strong {
  font-size: 0.88rem;
  color: var(--ink);
}

.plan-day-spots {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-left: 4px;
}

.plan-spot {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.78rem;
}

.spot-dur {
  color: var(--muted);
  min-width: 56px;
  font-size: 0.72rem;
}

.spot-name {
  flex: 1;
  color: var(--ink);
  font-weight: 500;
}

/* ── 离线方案警告 ── */
.offline-banner {
  margin: 0 0 12px;
  padding: 8px 14px;
  background: #FFF3E0;
  border: 1px solid #FFB74D;
  border-radius: 8px;
  font-size: 0.8rem;
  color: #E65100;
  text-align: center;
}

/* ── SSE 流式叙述 ── */
.stream-narration {
  padding: 12px 16px;
  margin-bottom: 12px;
  background: oklch(0.55 0.18 28 / 0.04);
  border-radius: 10px;
  border-left: 3px solid var(--brand-red, oklch(0.53 0.22 25));
  min-height: 40px;
}

.stream-narration p {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--ink, #1a1a1a);
  white-space: pre-wrap;
}

/* ── Refinement 调整面板 ── */
.refine-panel {
  margin-top: 12px;
  padding: 16px;
  background: var(--surface, #fff);
  border: 1px solid oklch(0.55 0.18 28 / 0.15);
  border-radius: 12px;
}

.refine-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 12px;
  color: var(--ink, #1a1a1a);
}

.refine-close-btn {
  background: none;
  border: 1px solid oklch(0 0 0 / 0.1);
  border-radius: 6px;
  width: 28px;
  height: 28px;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--muted, #999);
  display: flex;
  align-items: center;
  justify-content: center;
}

.refine-close-btn:hover {
  background: oklch(0 0 0 / 0.04);
  color: var(--ink, #1a1a1a);
}

.refine-quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.refine-quick-btn {
  padding: 5px 12px;
  border: 1px solid oklch(0 0 0 / 0.1);
  border-radius: 8px;
  background: var(--bg, #fafafa);
  font-size: 0.78rem;
  cursor: pointer;
  color: var(--ink, #333);
  transition: all 0.2s;
  white-space: nowrap;
}

.refine-quick-btn:hover {
  border-color: var(--brand-red, oklch(0.53 0.22 25));
  background: oklch(0.53 0.22 25 / 0.06);
}

.refine-input-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.refine-input-row :deep(.el-input) {
  flex: 1;
}

.refine-result {
  padding: 12px;
  background: oklch(0.53 0.22 25 / 0.04);
  border-radius: 8px;
  border-left: 3px solid var(--brand-red, oklch(0.53 0.22 25));
}

.refine-result__summary {
  font-size: 0.85rem;
  color: var(--ink, #1a1a1a);
  margin-bottom: 10px;
  line-height: 1.5;
}

.refine-result__actions {
  display: flex;
  gap: 8px;
}

.plan-empty {
  text-align: center;
  padding: 24px;
  color: var(--muted);
}

.plan-generating {
  text-align: center;
  padding: 24px;
  color: var(--muted);
}

.plan-generating p {
  margin-top: 12px;
}

.plan-generating__sub {
  font-size: 13px;
  color: oklch(0 0 0 / 0.4);
  margin-top: 6px !important;
  max-height: 80px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.result-actions {
  display: flex;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid oklch(0 0 0 / 0.06);
}

/* ==========================================
   全屏地图
   ========================================== */
.map-main {
  flex: 1;
  position: relative;
}

.map-loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: oklch(0.96 0.002 80 / 0.9);
  color: var(--muted, #999);
  font-size: 0.9rem;
}

/* ── 底部统计栏 ── */
/* ── 方案路线切换条 ── */
.route-switcher {
  position: absolute;
  bottom: 52px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 110;
  display: flex;
  gap: 0;
  background: rgba(255, 255, 255, 0.94);
  border-radius: 24px;
  padding: 4px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(8px);
}

.rs-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: none;
  background: transparent;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #666);
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
  font-family: inherit;
}

.rs-btn:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-primary, #333);
}

.rs-btn--active {
  background: rgba(0, 0, 0, 0.08);
  color: var(--text-primary, #222);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.rs-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .route-switcher {
    bottom: 36px;
  }
  .rs-btn {
    padding: 6px 12px;
    font-size: 11px;
    gap: 4px;
  }
  .rs-dot {
    width: 8px;
    height: 8px;
  }
}
.map-stats-bar {
  position: absolute;
  bottom: 12px;
  left: 0;
  right: 0;
  z-index: 900;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid oklch(0 0 0 / 0.06);
  font-size: 0.78rem;
  color: var(--muted, #999);
}

.stat-sep {
  color: oklch(0 0 0 / 0.15);
}

/* ==========================================
   移动端 (≤768px)
   ========================================== */
.mobile-tab-bar {
  display: none;
}

@media (max-width: 768px) {
  .trip-full-page {
    flex-direction: column;
  }

  .map-sidebar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    top: auto;
    width: 100% !important;
    height: 60px;
    flex-direction: row;
    border-right: none;
    border-top: 1px solid oklch(0 0 0 / 0.1);
    border-radius: 16px 16px 0 0;
    transition: height 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
    box-shadow: 0 -4px 20px oklch(0.15 0.02 25 / 0.12);
  }

  .map-sidebar.sidebar--mobile-open {
    height: 55vh;
  }

  .sidebar-collapsed {
    width: 100%;
    flex-direction: row;
    justify-content: space-around;
    align-items: center;
    padding: 0 16px;
    gap: 0;
  }

  .collapsed-icons {
    flex-direction: row;
    gap: 24px;
  }

  .sidebar--expanded .sidebar-collapsed {
    display: flex;
  }

  .sidebar-expanded {
    display: none !important;
  }

  .sidebar--mobile-open .sidebar-expanded {
    display: flex !important;
  }

  .sidebar--mobile-open .sidebar-collapsed {
    display: none;
  }

  .map-main {
    height: 100%;
  }

  .map-stats-bar {
    bottom: 60px;
  }

  .mobile-tab-bar {
    display: none;
  }
}
</style>
