<template>
  <div class="map-wrapper" :style="{ height: height }">
    <!-- Key 未配置占位 -->
    <div v-if="!configured" class="map-placeholder">
      <el-icon :size="48"><MapLocation /></el-icon>
      <p>地图 Key 未配置</p>
      <span>请在 .env 中设置 VITE_AMAP_KEY</span>
    </div>

    <!-- 加载中 -->
    <div v-else-if="loading" class="map-placeholder">
      <el-icon :size="48" class="is-loading"><Loading /></el-icon>
      <p>地图加载中...</p>
    </div>

    <!-- 加载失败 -->
    <div v-else-if="loadError" class="map-placeholder">
      <el-icon :size="48"><WarningFilled /></el-icon>
      <p>地图加载失败</p>
      <span>{{ loadError }}</span>
      <el-button type="primary" size="small" @click="initMap">重试</el-button>
    </div>

    <!-- 地图容器 -->
    <div
      ref="mapContainer"
      class="map-container"
      :style="{ pointerEvents: interactive ? 'auto' : 'none' }"
    />

    <!-- Day 筛选栏（仅在有 routeLine 分段数据时显示） -->
    <div v-if="dayTabs.length > 1" class="map-day-tabs">
      <el-radio-group v-model="activeDayTab" size="small" @change="onDayChange">
        <el-radio-button :value="0">全部</el-radio-button>
        <el-radio-button v-for="d in dayTabs" :key="d" :value="d">
          第{{ d }}天
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- 图例 -->
    <div v-if="legendItems.length > 0" class="map-legend">
      <div v-for="item in legendItems" :key="item.type" class="legend-item">
        <span class="legend-dot" :style="{ background: item.color }" />
        <span>{{ item.label }}</span>
      </div>
    </div>

    <!-- 路线方案图例（行程规划三方案） -->
    <div v-if="showRouteLegend && planRouteLegend.length > 0" class="map-route-legend">
      <div
        v-for="item in planRouteLegend"
        :key="item.planId"
        :class="['route-legend-item', { 'route-legend-item--active': highlightedPlanId === item.planId }]"
        @click.stop="$emit('plan-legend-click', item.planId)"
      >
        <span
          class="route-legend-line"
          :style="{
            background: item.color,
            opacity: highlightedPlanId && highlightedPlanId !== item.planId ? 0.3 : 0.85,
            height: highlightedPlanId === item.planId ? '4px' : '3px',
          }"
        />
        <span class="route-legend-label">{{ item.label }}</span>
      </div>
    </div>

    <!-- 拥堵图例（仅在有拥堵段时显示） -->
    <div v-if="showCongestionLegend" class="map-congestion-legend">
      <div class="congestion-item">
        <span class="congestion-swatch" style="background:#FFD700" />
        <span>缓行</span>
      </div>
      <div class="congestion-item">
        <span class="congestion-swatch" style="background:#FF4444" />
        <span>拥堵</span>
      </div>
      <div class="congestion-item">
        <span class="congestion-swatch" style="background:#1A1A1A" />
        <span>严重</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { WarningFilled, Loading, MapLocation } from '@element-plus/icons-vue'
import { loadAMap, isAMapConfigured } from '@/utils/loadAmap'
import { ZOOM_THRESHOLDS } from '@/utils/mapAdapter'

// ── Props ──
const props = defineProps({
  /** 地图中心点 [lng, lat] */
  center: { type: Array, default: () => [116.68, 23.35] },
  /** 缩放级别 */
  zoom: { type: Number, default: 11 },
  /** POI 标记点数组 */
  markers: { type: Array, default: () => [] },
  /** 路线坐标数组 [[lng, lat], ...] */
  routeLine: { type: Array, default: () => [] },
  /** 分段路线 { day: number, coords: [[lng, lat], ...] }[] */
  routeSegments: { type: Array, default: () => [] },
  /** 人流热力图数据 [{lng, lat, count}, ...] */
  heatmapData: { type: Array, default: () => [] },
  /** 地图高度 */
  height: { type: String, default: '500px' },
  /** 是否允许交互 */
  interactive: { type: Boolean, default: true },
  /** 缩略模式（隐藏控件 + 小字号） */
  thumbnail: { type: Boolean, default: false },
  /** 是否启用缩放级别过滤 markers */
  enableZoomFilter: { type: Boolean, default: false },
  /** 是否启用 hover 弹出 infoWindow（桌面端） */
  enableHoverInfo: { type: Boolean, default: false },
  /** 热力图在缩放到此级别以上时才显示 */
  heatmapMinZoom: { type: Number, default: 14 },
  /** 是否显示实时交通图层 */
  showTraffic: { type: Boolean, default: false },
  /** 路线方案图例 [{planId, color, label}] */
  planRouteLegend: { type: Array, default: () => [] },
  /** 当前高亮的方案 ID */
  highlightedPlanId: { type: String, default: null },
  /** 是否显示路线方案图例 */
  showRouteLegend: { type: Boolean, default: false },
  /** 是否显示拥堵图例 */
  showCongestionLegend: { type: Boolean, default: false },
})

// ── Emits ──
const emit = defineEmits(['marker-click', 'ready', 'plan-legend-click'])

// ── State ──
const configured = isAMapConfigured()
const loading = ref(false)
const loadError = ref('')
const mapContainer = ref(null)
const activeDayTab = ref(0)

let AMapInstance = null
let map = null
let markerLayer = []   // 当前显示的 markers
let routePolyline = null
let heatmap = null
let infoWindow = null
let trafficLayer = null

// ── Computed ──
const dayTabs = computed(() => {
  if (props.routeSegments.length > 0) {
    return props.routeSegments.map(s => s.day)
  }
  return []
})

// 当前地图缩放级别（由 zoomend 事件实时更新）
const currentZoom = ref(props.zoom)

// 根据 zoom 过滤 markers — 缩放渐进式展示的核心
const visibleMarkers = computed(() => {
  if (!props.enableZoomFilter) return props.markers
  const zoom = currentZoom.value
  return props.markers.filter(m => {
    const minZ = m.minZoom ?? ZOOM_THRESHOLDS[m.type] ?? 0
    return zoom >= minZ
  })
})

const legendItems = computed(() => {
  const types = new Set(visibleMarkers.value.map(m => m.type))
  const items = []
  const colorMap = {
    food: { color: '#E6A23C', label: '美食' },
    heritage: { color: '#F56C6C', label: '非遗' },
    hotel: { color: '#409EFF', label: '酒店' },
    weather: { color: '#67C23A', label: '天气' },
    interest: { color: '#909399', label: '兴趣点' },
    transport: { color: '#36CFC9', label: '交通' },
    default: { color: '#A0A0A0', label: '其他' },
  }
  for (const t of types) {
    items.push(colorMap[t] || { color: colorMap.default.color, label: t })
  }
  return items
})

// ── 初始化地图 ──
async function initMap() {
  if (!configured || !mapContainer.value) return

  loading.value = true
  loadError.value = ''

  try {
    AMapInstance = await loadAMap()
    const [lng, lat] = props.center

    map = new AMapInstance.Map(mapContainer.value, {
      center: [lng, lat],
      zoom: props.zoom,
      resizeEnable: true,
      dragEnable: props.interactive,
      zoomEnable: props.interactive,
      scrollWheel: props.interactive,
      doubleClickZoom: props.interactive,
      touchZoom: props.interactive,
    })

    // 异步加载 UI 控件 + InfoWindow + HeatMap 插件
    await new Promise((resolve) => {
      AMapInstance.plugin(
        ['AMap.Scale', 'AMap.ToolBar', 'AMap.InfoWindow', 'AMap.HeatMap', 'AMap.TileLayer.Traffic'],
        resolve
      )
    })

    if (!props.thumbnail) {
      map.addControl(new AMapInstance.Scale({ position: 'LB' }))
      map.addControl(new AMapInstance.ToolBar({ position: 'RT' }))
    }

    infoWindow = new AMapInstance.InfoWindow({ offset: [0, -30] })

    // 监听缩放事件 — 更新 visibleMarkers + 热力图显隐
    map.on('zoomend', () => {
      currentZoom.value = map.getZoom()
      if (heatmap) {
        if (currentZoom.value >= props.heatmapMinZoom) {
          heatmap.show()
        } else {
          heatmap.hide()
        }
      }
    })

    // 注入 infoWindow 全局样式（AMap infoWindow 内容渲染在 DOM 中，不受 scoped 限制）
    if (props.enableHoverInfo && !document.getElementById('map-iw-styles')) {
      const style = document.createElement('style')
      style.id = 'map-iw-styles'
      style.textContent = `
        .info-window-card { min-width:180px; max-width:260px; font-size:13px; line-height:1.5; }
        .iw-header { display:flex; align-items:center; gap:8px; padding:8px 12px; background:#fafafa; border-left:3px solid #666; border-radius:4px 4px 0 0; }
        .iw-type-badge { font-size:11px; color:#fff; padding:1px 6px; border-radius:3px; white-space:nowrap; }
        .iw-title { color:#333; font-size:14px; }
        .iw-body { padding:8px 12px; }
        .iw-field { display:flex; justify-content:space-between; align-items:center; padding:3px 0; border-bottom:1px solid #f0f0f0; }
        .iw-field:last-child { border-bottom:none; }
        .iw-key { color:#999; font-size:12px; }
        .iw-val { color:#333; font-weight:500; font-size:12px; }
      `
      document.head.appendChild(style)
    }

    // 渲染初始数据（使用 filtered markers）
    renderMarkers(visibleMarkers.value)
    renderRouteLine(props.routeLine)
    renderHeatmap(props.heatmapData)

    loading.value = false
    emit('ready', map)
  } catch (e) {
    loading.value = false
    loadError.value = e.message || '未知错误'
  }
}

// ── Markers 渲染 ──
function renderMarkers(markers) {
  clearMarkers()
  if (!map || !AMapInstance || !markers.length) return

  markerLayer = markers.map(m => {
    const content = createMarkerContent(m)
    const marker = new AMapInstance.Marker({
      position: [m.lng, m.lat],
      content,
      anchor: 'bottom-center',
      offset: [0, 0],
      zIndex: 100,
    })

    // 🆕 hover 事件（桌面端主交互）
    if (props.enableHoverInfo) {
      marker.on('mouseover', () => showInfoWindow(m, marker))
      marker.on('mouseout', () => { if (infoWindow) infoWindow.close() })
    }

    // 保留 click 事件（移动端 fallback + 未来扩展如滚动到卡片）
    marker.on('click', () => {
      showInfoWindow(m, marker)
      emit('marker-click', m)
    })

    marker._markerData = m
    marker.setMap(map)
    return marker
  })
}

function createMarkerContent(marker) {
  const colors = {
    food: '#E6A23C', heritage: '#F56C6C', hotel: '#409EFF',
    weather: '#67C23A', interest: '#909399', transport: '#36CFC9',
    default: '#A0A0A0',
  }
  const icons = {
    food: '🍲', heritage: '🏛️', hotel: '🏨',
    weather: '🌤️', interest: '📍', transport: '🚗',
    default: '📌',
  }
  const color = colors[marker.type] || colors.default
  const icon = marker.icon || icons[marker.type] || icons.default

  return `<div style="text-align:center">
    <div style="
      background:${color}; color:#fff; width:32px; height:32px;
      border-radius:50%; display:flex; align-items:center; justify-content:center;
      font-size:16px; box-shadow:0 2px 6px rgba(0,0,0,.3); border:2px solid #fff;
    ">${icon}</div>
    ${marker.temp ? `<div style="font-size:10px;color:#333;white-space:nowrap;margin-top:2px;background:rgba(255,255,255,.85);border-radius:4px;padding:1px 4px;">${marker.temp}</div>` : ''}
  </div>`
}

function clearMarkers() {
  if (markerLayer.length) {
    markerLayer.forEach(m => m.setMap(null))
    markerLayer = []
  }
}

// ── InfoWindow ──
function showInfoWindow(data, markerInstance) {
  if (!infoWindow || !map) return
  const html = buildInfoWindowContent(data)
  infoWindow.setContent(html)
  infoWindow.open(map, markerInstance.getPosition())
}

function buildInfoWindowContent(data) {
  const detail = data.detail
  if (!detail?.fields?.length) {
    // fallback: 简单格式（兼容无 detail 字段的旧 marker）
    return `<div style="padding:8px 12px;max-width:200px">
      <strong>${data.title || data.name || ''}</strong>
      ${data.subtitle ? `<br/><span style="color:#666;font-size:12px">${data.subtitle}</span>` : ''}
    </div>`
  }

  const colorMap = {
    '天气': '#67C23A', '美食': '#E6A23C', '非遗': '#F56C6C',
    '酒店': '#409EFF', '人流': '#909399', '途经点': '#36CFC9',
  }
  const color = colorMap[detail.label] || '#666'

  const fieldsHtml = detail.fields
    .filter(f => f.val && f.val !== '—' && f.val !== '')
    .map(f => `<div class="iw-field">
      <span class="iw-key">${f.key}</span>
      <span class="iw-val">${f.val}</span>
    </div>`)
    .join('')

  return `<div class="info-window-card">
    <div class="iw-header" style="border-left-color:${color}">
      <span class="iw-type-badge" style="background:${color}">${detail.label}</span>
      <strong class="iw-title">${data.title || data.name || ''}</strong>
    </div>
    <div class="iw-body">${fieldsHtml}</div>
  </div>`
}

// ── 路线 Polyline ──
function renderRouteLine(coords) {
  if (routePolyline) {
    routePolyline.setMap(null)
    routePolyline = null
  }
  if (!map || !AMapInstance || !coords.length) return

  routePolyline = new AMapInstance.Polyline({
    path: coords,
    strokeColor: '#3366FF',
    strokeWeight: 4,
    strokeOpacity: 0.7,
    strokeStyle: 'dashed',
    lineJoin: 'round',
    showDir: true,
  })
  routePolyline.setMap(map)
  map.setFitView([routePolyline])
}

// ── 热力图 ──
function renderHeatmap(data) {
  if (heatmap) {
    heatmap.setMap(null)
    heatmap = null
  }
  if (!map || !AMapInstance || !data.length) return

  // 高德热力图需要加载插件
  AMapInstance.plugin(['AMap.HeatMap'], () => {
    heatmap = new AMapInstance.HeatMap(map, {
      radius: 30,
      opacity: [0, 0.7],
      gradient: {
        0.2: 'blue',
        0.4: 'cyan',
        0.6: 'lime',
        0.8: 'yellow',
        1.0: 'red',
      },
    })
    heatmap.setDataSet({
      data: data.map(d => ({ lng: d.lng, lat: d.lat, count: d.count || 1 })),
      max: 100,
    })
    // 异步加载完成时，检查当前 zoom 是否需要隐藏热力图
    if (currentZoom.value < props.heatmapMinZoom) {
      heatmap.hide()
    }
  })
}

// ── Day 切换 ──
function onDayChange(day) {
  if (day === 0) {
    renderMarkers(visibleMarkers.value)
    renderRouteLine(props.routeLine)
  } else {
    const seg = props.routeSegments.find(s => s.day === day)
    const filteredMarkers = visibleMarkers.value.filter(m => m.day === day)
    renderMarkers(filteredMarkers)
    if (seg) renderRouteLine(seg.coords)
  }
}

// ── 暴露 API ──
function setCenter(lng, lat) {
  if (map) map.setCenter([lng, lat])
}
function setZoom(level) {
  if (map) map.setZoom(level)
}
function fitView(overlays) {
  if (map) map.setFitView(overlays)
}

defineExpose({ map, setCenter, setZoom, fitView, refresh: initMap, getMapCanvas: () => map?.getCanvas?.() })

// ── 生命周期 ──
onMounted(() => {
  nextTick(() => initMap())
})

// ── Traffic 图层 ──
function renderTraffic(show) {
  if (!map || !AMapInstance) return
  if (show && !trafficLayer) {
    trafficLayer = new AMapInstance.TileLayer.Traffic({
      autoRefresh: true,
      interval: 180,
      zIndex: 10,
    })
    trafficLayer.setMap(map)
  } else if (!show && trafficLayer) {
    trafficLayer.setMap(null)
    trafficLayer = null
  }
}

onBeforeUnmount(() => {
  clearMarkers()
  if (routePolyline) routePolyline.setMap(null)
  if (heatmap) heatmap.setMap(null)
  if (trafficLayer) { trafficLayer.setMap(null); trafficLayer = null }
  if (infoWindow) infoWindow.close()
  if (map) {
    map.destroy()
    map = null
  }
})

// ── Watchers ──
watch(visibleMarkers, (val) => { if (map) { activeDayTab.value = 0; renderMarkers(val) } }, { deep: true })
watch(() => props.routeLine, (val) => { if (map) renderRouteLine(val) }, { deep: true })
watch(() => props.heatmapData, (val) => { if (map) renderHeatmap(val) }, { deep: true })
watch(() => props.center, ([lng, lat]) => { if (map) map.setCenter([lng, lat]) })
watch(() => props.zoom, (z) => { if (map) map.setZoom(z) })
watch(() => props.showTraffic, (val) => { renderTraffic(val) })
</script>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}

.map-container {
  width: 100%;
  height: 100%;
}

.map-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #999;
  background: #fafafa;
}
.map-placeholder p {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #666;
}
.map-placeholder span {
  font-size: 12px;
  color: #bbb;
}

.map-day-tabs {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.map-legend {
  position: absolute;
  bottom: 12px;
  left: 12px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ── 路线方案图例 ── */
.map-route-legend {
  position: absolute;
  bottom: 12px;
  right: 12px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 10px;
  padding: 8px 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 100px;
}

.route-legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 6px;
  transition: background 0.2s;
}

.route-legend-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.route-legend-item--active {
  background: rgba(0, 0, 0, 0.06);
}

.route-legend-line {
  display: inline-block;
  width: 24px;
  border-radius: 2px;
  flex-shrink: 0;
  transition: height 0.2s, opacity 0.2s;
}

.route-legend-label {
  font-size: 12px;
  color: #333;
  font-weight: 500;
  white-space: nowrap;
}

/* ── 拥堵图例 ── */
.map-congestion-legend {
  position: absolute;
  bottom: 12px;
  right: 12px;
  z-index: 100;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 6px 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 10px;
}

.congestion-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #666;
}

.congestion-swatch {
  width: 14px;
  height: 4px;
  border-radius: 2px;
  flex-shrink: 0;
}
</style>
