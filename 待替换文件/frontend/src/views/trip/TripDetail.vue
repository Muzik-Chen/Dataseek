<template>
  <div class="trip-detail-page">
    <LoadingSkeleton v-if="loading" type="detail" />

    <div v-else-if="error" class="error-state">
      <el-result icon="error" :title="error">
        <template #extra>
          <el-button type="primary" @click="fetchDetail">重新加载</el-button>
          <el-button @click="$router.push('/profile')">返回</el-button>
        </template>
      </el-result>
    </div>

    <template v-else-if="trip">
      <div class="trip-hero">
        <h1>{{ trip.title }}</h1>
        <div class="trip-meta">
          <span>{{ trip.days }}天行程</span>
          <el-tag>{{ trip.crowd_type }}</el-tag>
          <el-tag :type="trip.status === 'draft' ? 'warning' : trip.status === 'generated' ? 'success' : 'info'">
            {{ trip.status === 'draft' ? '草稿' : trip.status === 'generated' ? '已生成' : '生成中' }}
          </el-tag>
        </div>
      </div>

      <!-- 🆕 Phase 3: 路线地图 -->
      <div v-if="hasGeoData" class="trip-map-section">
        <MapContainer
          height="400px"
          :center="mapData.center"
          :markers="mapData.markers"
          :routeLine="mapData.routeLine"
          :heatmapData="mapData.heatmapData"
          :enableZoomFilter="true"
          :enableHoverInfo="true"
          :heatmapMinZoom="15"
        />
      </div>

      <!-- 内容区：保持 800px 阅读宽度 -->
      <div class="content-wrapper">
        <!-- 新格式：plans[] → 复用 TripCard 组件（含 enrichment 展示） -->
        <div v-if="planFormat === 'plans'" class="plan-content">
          <el-tabs v-if="trip.plan_content.plans.length > 1" v-model="activePlanTab">
            <el-tab-pane
              v-for="plan in trip.plan_content.plans"
              :key="plan.plan_id"
              :label="'方案' + plan.plan_id + ': ' + (plan.theme || plan.title?.slice(0, 8) || '')"
              :name="plan.plan_id"
            />
          </el-tabs>
          <TripCard
            v-if="currentPlan"
            :plans="[currentPlan]"
            @save="() => {}"
          />
        </div>

        <!-- 旧格式兼容：days[].spots[] -->
        <div v-else-if="planFormat === 'days'" class="plan-content">
          <div v-for="day in trip.plan_content.days" :key="day.day" class="plan-day">
            <div class="day-header">
              <span class="day-badge">Day {{ day.day }}</span>
              <h2>{{ day.title }}</h2>
            </div>
            <div class="spot-timeline">
              <div v-for="spot in day.spots" :key="spot.name" class="spot-card">
                <div class="spot-marker" />
                <div class="spot-body">
                  <div class="spot-top">
                    <strong>{{ spot.name }}</strong>
                    <el-tag size="small">{{ spot.type }}</el-tag>
                  </div>
                  <p>{{ spot.tip }}</p>
                  <span class="spot-duration">⏱ {{ spot.duration }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="trip.plan_content.tips" class="trip-tips">
            <h3>💡 出行贴士</h3>
            <ul>
              <li v-for="tip in trip.plan_content.tips" :key="tip">{{ tip }}</li>
            </ul>
          </div>
        </div>

        <!-- 无内容 -->
        <div v-else-if="trip.plan_content" class="plan-content">
          <el-empty description="暂无行程内容" />
        </div>

        <div class="trip-actions">
          <el-button @click="$router.push('/trip/create')">创建新行程</el-button>
          <el-button type="danger" plain @click="deleteTrip">删除此行程</el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTripPlanDetail, deleteTripPlan } from '@/api'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import TripCard from '@/components/business/TripCard.vue'
import MapContainer from '@/components/common/MapContainer.vue'
import { planToMapData } from '@/utils/mapAdapter'

const route = useRoute()
const router = useRouter()

const trip = ref(null)
const loading = ref(true)
const error = ref('')
const activePlanTab = ref('A')

// Detect plan format: 'plans' (new AI format) vs 'days' (old/template format)
const planFormat = computed(() => {
  const pc = trip.value?.plan_content
  if (!pc) return 'none'
  if (pc.plans?.length > 0) return 'plans'
  if (pc.days?.length > 0) return 'days'
  return 'none'
})

const currentPlan = computed(() => {
  if (planFormat.value === 'plans') {
    return trip.value.plan_content.plans.find(p => p.plan_id === activePlanTab.value)
      || trip.value.plan_content.plans[0]
  }
  return null
})

// Phase 3: 地图数据
const mapData = computed(() => {
  if (!currentPlan.value) return { center: [116.68, 23.35], markers: [], routeLine: [], heatmapData: [] }
  return planToMapData(currentPlan.value)
})

const hasGeoData = computed(() => {
  return mapData.value.routeLine.length > 0 || mapData.value.markers.length > 0
})

async function fetchDetail() {
  loading.value = true
  error.value = ''
  try {
    trip.value = await getTripPlanDetail(route.params.id)
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function deleteTrip() {
  try {
    await ElMessageBox.confirm('确定删除此行程？', '提示', { type: 'warning' })
    await deleteTripPlan(route.params.id)
    ElMessage.success('行程已删除')
    router.push('/profile')
  } catch { /* 取消 */ }
}

onMounted(() => fetchDetail())
</script>

<style scoped>
.trip-detail-page { max-width: var(--content-wide, 1200px); margin: 0 auto; padding: var(--space-2xl) var(--space-md); }

.trip-hero { max-width: var(--content-narrow, 800px); margin: 0 auto var(--space-2xl); text-align: center; }
.trip-hero h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-md); }
.trip-meta { display: flex; gap: var(--space-sm); justify-content: center; align-items: center; color: var(--muted); }

/* Phase 3: 地图区块 */
.trip-map-section {
  margin-bottom: var(--space-2xl);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.content-wrapper {
  max-width: var(--content-narrow, 800px);
  margin: 0 auto;
}

.plan-content { display: flex; flex-direction: column; gap: var(--space-xl); }

.plan-day {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-xl);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
}

.day-header { display: flex; align-items: center; gap: var(--space-md); margin-bottom: var(--space-lg); }
.day-badge { background: var(--primary); color: #fff; padding: 4px 14px; border-radius: 12px; font-weight: 600; font-size: var(--fs-sm); }
.day-header h2 { font-size: var(--fs-xl); color: var(--ink); margin: 0; }

.spot-timeline { display: flex; flex-direction: column; gap: var(--space-sm); }

.spot-card { display: flex; gap: var(--space-md); }

.spot-marker {
  width: 10px; height: 10px;
  background: var(--primary);
  border-radius: 50%;
  margin-top: 8px;
  flex-shrink: 0;
  position: relative;
}

.spot-body {
  flex: 1;
  padding-bottom: var(--space-md);
  border-bottom: 1px solid oklch(0 0 0 / 0.05);
}

.spot-top { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: 4px; }
.spot-top strong { color: var(--ink); }
.spot-body p { color: var(--muted); font-size: var(--fs-sm); margin: 0 0 4px; }
.spot-duration { color: var(--muted); font-size: var(--fs-xs); }

.trip-tips {
  background: oklch(0.55 0.18 28 / 0.06);
  border-radius: 12px;
  padding: var(--space-lg);
}

.trip-tips h3 { margin: 0 0 var(--space-sm); color: var(--ink); }
.trip-tips ul { margin: 0; padding-left: var(--space-lg); }
.trip-tips li { color: var(--muted); font-size: var(--fs-sm); margin-bottom: 4px; }

.trip-actions { display: flex; gap: var(--space-md); margin-top: var(--space-2xl); padding-top: var(--space-xl); border-top: 1px solid oklch(0 0 0 / 0.06); }

.error-state { padding: var(--space-3xl); }

/* 移动端：地图缩小间距 */
@media (max-width: 640px) {
  .trip-map-section { margin-bottom: var(--space-lg); }
}
</style>
