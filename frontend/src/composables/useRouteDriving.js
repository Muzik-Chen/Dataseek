/**
<<<<<<< HEAD
 * useRouteDriving.js — 高德地图路线绘制 + 起终点标记 + 方案色区分
 *
 * 核心职责：
 *   1. 用双层 Polyline（outline + core）连接 waypoints，模仿高德原生路线风格
 *   2. 创建起点/终点 Marker（起点=出发城市，终点=最后一个 waypoint）
 *   3. 管理地图上的 Polyline + Marker 图层（逐方案增量添加）
=======
 * useRouteDriving.js — 高德驾车路线 + TMC 拥堵分段着色
 *
 * 核心职责：
 *   1. 封装 AMap.Driving 调用（policy=0 最快捷 + extensions='all' 获取 TMC）
 *   2. 解析 TMC 拥堵数据 → 按 status 分段着色
 *   3. 管理地图上的 Polyline 图层（逐方案增量添加）
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
 *   4. 路线高亮/半透明切换（选中方案 vs 其他方案）
 *
 * 使用方式：
 *   const { addPlanRoute, highlightPlan, resetHighlight, clearAll, planRoutes, highlightedPlanId } = useRouteDriving(mapRef)
 *
 *   // SSE 逐方案到达时：
<<<<<<< HEAD
 *   await addPlanRoute('A', waypointsA, '深圳')  // 画出绿色路线 + 起终点标记
 *   await addPlanRoute('B', waypointsB, '深圳')
 *   await addPlanRoute('C', waypointsC, '深圳')
=======
 *   await addPlanRoute('A', waypointsA)  // 立即画出绿色路线
 *   await addPlanRoute('B', waypointsB)  // 立即画出橙色路线
 *   await addPlanRoute('C', waypointsC)  // 立即画出蓝色路线
 *
 *   // 用户交互：
 *   highlightPlan('A')   // 方案A高亮，B/C半透明
 *   resetHighlight()     // 恢复全部默认样式
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
 */

import { ref, computed } from 'vue'
import { loadAMap } from '@/utils/loadAmap'

<<<<<<< HEAD
// ── 模块级单例（AMap 实例共享）──
let _AMapInstance = null
let _amapPromise = null

async function _ensureAMap() {
  if (_AMapInstance) return _AMapInstance
  if (!_amapPromise) {
    _amapPromise = loadAMap().then(amap => {
      _AMapInstance = amap
      return amap
    })
  }
  return _amapPromise
=======
// ── 模块级单例（插件 + AMap 实例共享）──
let _AMapInstance = null
let _drivingPluginReady = false
let _drivingPluginPromise = null

async function _ensureAMapDriving() {
  if (!_AMapInstance) {
    _AMapInstance = await loadAMap()
  }

  if (_drivingPluginReady) return _AMapInstance

  if (!_drivingPluginPromise) {
    _drivingPluginPromise = new Promise((resolve) => {
      _AMapInstance.plugin('AMap.Driving', () => {
        _drivingPluginReady = true
        resolve(_AMapInstance)
      })
      // 兜底超时
      setTimeout(() => {
        if (!_drivingPluginReady) {
          _drivingPluginReady = true
          resolve(_AMapInstance)
        }
      }, 5000)
    })
  }

  return _drivingPluginPromise
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
}

// ── 方案基线色 ──
export const PLAN_COLORS = {
  A: '#28C76F', // 活力绿 — 美食
  B: '#FF9F43', // 琥珀橙 — 文化
  C: '#0091FF', // 科技蓝 — 综合
}

<<<<<<< HEAD
// ── 双层样式预设（高德原生路线风格）──
const DEFAULT_STYLE = {
  outline: { strokeWeight: 8, strokeOpacity: 0.35, lineJoin: 'round', lineCap: 'round' },
  core:   { strokeWeight: 5, strokeOpacity: 0.9,  lineJoin: 'round', lineCap: 'round', showDir: true },
}
const HIGHLIGHTED_STYLE = {
  outline: { strokeWeight: 10, strokeOpacity: 0.45 },
  core:   { strokeWeight: 6,  strokeOpacity: 1.0 },
}
const DIMMED_STYLE = {
  outline: { strokeWeight: 4, strokeOpacity: 0.12 },
  core:   { strokeWeight: 2, strokeOpacity: 0.25 },
}

// ── 出发城市坐标映射表（免地理编码 API 调用）──
const CITY_COORDS = {
  '深圳': [114.0579, 22.5431],
  '广州': [113.2644, 23.1291],
  '厦门': [118.0894, 24.4798],
  '福州': [119.2965, 26.0745],
  '汕头': [116.6822, 23.3541],
  '潮州': [116.6390, 23.6640],
  '揭阳': [116.3700, 23.5480],
  '汕尾': [115.3750, 22.7860],
  '珠海': [113.5767, 22.2707],
  '东莞': [113.7519, 23.0208],
  '惠州': [114.4168, 23.1120],
  '佛山': [113.1219, 23.0219],
  '中山': [113.3926, 22.5160],
  '江门': [113.0816, 22.5791],
  '肇庆': [112.4650, 23.0471],
  '梅州': [116.1223, 24.2886],
  '泉州': [118.6758, 24.8741],
  '漳州': [117.6475, 24.5130],
  '香港': [114.1734, 22.3193],
  '澳门': [113.5491, 22.1987],
}

// ── 获取出发城市的坐标 ──
async function _geocodeCity(cityName) {
  if (!cityName) return null

  // 先查映射表
  const shortName = cityName.replace(/市|省|自治区/g, '').trim()
  for (const [key, coords] of Object.entries(CITY_COORDS)) {
    if (cityName.includes(key) || key.includes(shortName) || shortName.includes(key)) {
      return { lng: coords[0], lat: coords[1], name: key }
    }
  }

  // 映射表未命中 → 尝试 AMap.Geocoder
  const AMap = await _ensureAMap()
  return new Promise((resolve) => {
    try {
      const geocoder = new AMap.Geocoder({ city: '全国' })
      geocoder.getLocation(cityName, (status, result) => {
        if (status === 'complete' && result.info === 'OK') {
          const pos = result.geocodes?.[0]?.location
          if (pos) {
            resolve({ lng: pos.getLng(), lat: pos.getLat(), name: cityName })
            return
          }
        }
        resolve(null)
      })
    } catch {
      resolve(null)
    }
  })
}

// ── AMap.Marker 自定义内容工厂 ──
function _createMarkerContent(label, color) {
  return `<div style="
    display:flex;align-items:center;gap:4px;
    background:rgba(0,0,0,0.72);color:#fff;
    padding:3px 10px 3px 6px;border-radius:16px;
    font-size:12px;font-weight:600;white-space:nowrap;
    box-shadow:0 2px 8px rgba(0,0,0,0.3);
    border-left:3px solid ${color};
  "><span style="
    display:inline-block;width:10px;height:10px;
    border-radius:50%;background:${color};flex-shrink:0;
  "></span>${label}</div>`
}

// 辅助：对一对 {outline, core} Polyline 应用样式
function _applyPairStyle(pair, style) {
  try { pair.outline.setOptions(style.outline) } catch { /* ignore */ }
  try { pair.core.setOptions(style.core) } catch { /* ignore */ }
}
=======
// ── 拥堵路段覆盖色 ──
const CONGESTION_COLORS = {
  '畅通': null,        // null → 沿用方案基线色
  '缓行': '#FFD700',   // 黄色
  '拥堵': '#FF4444',   // 红色
  '严重拥堵': '#1A1A1A', // 黑色
  '未知': '#AAAAAA',    // 灰色
}

// ── 样式预设 ──
const DEFAULT_STYLE = { strokeWeight: 4, strokeOpacity: 0.7 }
const HIGHLIGHTED_STYLE = { strokeWeight: 6, strokeOpacity: 0.9 }
const DIMMED_STYLE = { strokeWeight: 2, strokeOpacity: 0.25 }
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22

export function useRouteDriving(mapRef) {
  // ── 响应式状态 ──
  const planRoutes = ref({})
  const highlightedPlanId = ref(null)
  const loading = ref(false)

<<<<<<< HEAD
  const hasCongestion = computed(() => false)
=======
  // 是否有任何路线包含拥堵段
  const hasCongestion = computed(() => {
    return Object.values(planRoutes.value).some(r => r._hasCongestion)
  })

  // ── 内部状态 ──
  let driving = null
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22

  // ── 获取地图实例 ──
  function getMap() {
    if (!mapRef) return null
<<<<<<< HEAD
    const v = mapRef.value
    if (v && typeof v.add === 'function') return v
    if (v?.map && typeof v.map.add === 'function') return v.map
    console.log(`[useRouteDriving] getMap: no valid AMap instance (ref has value=${!!v})`)
    return null
=======
    // 支持 MapContainer 的 ref（暴露 .map）或直接 AMap 实例
    return mapRef.value?.map || mapRef.value || mapRef
  }

  // ── 确保 AMap.Driving 插件已加载 ──
  async function ensureDriving() {
    if (driving) return driving

    const AMap = await _ensureAMapDriving()

    if (!driving) {
      driving = new AMap.Driving({
        policy: 0,          // LEAST_TIME — 自动考虑实时交通
        extensions: 'all',  // 获取 TMC 拥堵数据
        ferry: 1,           // 允许轮渡（南澳岛场景）
      })
    }

    return driving
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
  }

  // ── 添加单个方案的路线（增量调用）──
  /**
<<<<<<< HEAD
   * @param {string} planId       'A' | 'B' | 'C'
   * @param {Array}  waypoints     [{lng, lat, name?}, ...]  所有途经点（含首尾）
   * @param {string} originCity    出发城市名称（用于起点标记）
   */
  async function addPlanRoute(planId, waypoints, originCity) {
    if (!waypoints || waypoints.length < 2) {
      console.log(`[useRouteDriving] addPlanRoute plan=${planId} SKIP: waypoints=${waypoints?.length || 0}`)
      return
    }

    const map = getMap()
    if (!map) {
      console.log(`[useRouteDriving] addPlanRoute plan=${planId} SKIP: map is null`)
      return
    }

    const color = PLAN_COLORS[planId] || '#3366FF'
    loading.value = true

    try {
      await _ensureAMap()

      // 地理编码出发城市
      let originCoord = null
      if (originCity) {
        originCoord = await _geocodeCity(originCity)
        if (originCoord) {
          console.log(`[useRouteDriving] plan=${planId} origin geocoded: ${originCity} → [${originCoord.lng}, ${originCoord.lat}]`)
        } else {
          console.log(`[useRouteDriving] plan=${planId} origin geocode failed for: ${originCity}`)
        }
      }

      drawDirectLine(planId, waypoints, color, map, originCoord)
      console.log(`[useRouteDriving] plan=${planId} drawn: waypoints=${waypoints.length} markers=${originCoord ? 2 : 1}`)
    } catch (e) {
      console.warn(`[useRouteDriving] Plan ${planId} 绘制失败:`, e.message)
=======
   * @param {string} planId   'A' | 'B' | 'C'
   * @param {Array}  waypoints [{lng, lat, name?}, ...]  所有途经点（含首尾）
   */
  async function addPlanRoute(planId, waypoints) {
    if (!waypoints || waypoints.length < 2) return

    const map = getMap()
    if (!map) { return }

    const color = PLAN_COLORS[planId] || '#3366FF'

    loading.value = true

    try {
      await ensureDriving()

      // 构建坐标数组 [lng, lat]
      const coords = waypoints.map(w => [w.lng, w.lat])
      const origin = coords[0]
      const destination = coords[coords.length - 1]
      const viaPoints = coords.length > 2 ? coords.slice(1, -1) : []

      // 调用 AMap.Driving.search
      const result = await new Promise((resolve, reject) => {
        driving.search(
          origin,
          destination,
          { waypoints: viaPoints, extensions: 'all' },
          (status, res) => {
            if (status === 'complete') resolve(res)
            else reject(new Error(`AMap.Driving 规划失败: ${status}`))
          }
        )
      })

      const route = result.routes?.[0]
      if (!route?.steps?.length) {
        // 无路线 → 降级为直线
        drawFallback(planId, waypoints, color, map)
        loading.value = false
        return
      }

      // ── 解析 TMC 拥堵数据 → 分段 Polyline ──
      const { segments, hasAnyCongestion } = await buildCongestionSegments(
        route.steps, color
      )

      // ── 清理旧路线（方案更新时）──
      const oldRoute = planRoutes.value[planId]
      if (oldRoute?.polylines) {
        oldRoute.polylines.forEach(p => {
          try { p.setMap(null) } catch { /* ignore */ }
        })
      }

      // 创建 Polylines
      const polylines = segments.map(seg => {
        const poly = new _AMapInstance.Polyline({
          path: seg.path,
          strokeColor: seg.strokeColor,
          strokeWeight: DEFAULT_STYLE.strokeWeight,
          strokeOpacity: DEFAULT_STYLE.strokeOpacity,
          lineJoin: 'round',
          lineCap: 'round',
          zIndex: 50,
        })
        poly.setMap(map)
        return poly
      })

      // 存储
      planRoutes.value = {
        ...planRoutes.value,
        [planId]: { color, polylines, waypoints, _hasCongestion: hasAnyCongestion }
      }

      // 自适应视野
      const allPolylines = Object.values(planRoutes.value)
        .flatMap(r => r.polylines)
      if (allPolylines.length > 0) {
        map.setFitView(allPolylines, false, [60, 60, 60, 60])
      }

    } catch (e) {
      console.warn(`[useRouteDriving] Plan ${planId} Driving 失败，降级为直线:`, e.message)
      drawFallback(planId, waypoints, color, map)
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    } finally {
      loading.value = false
    }
  }

<<<<<<< HEAD
  // ── 主力：双层实线连接 waypoints + 起终点 Marker ──
  function drawDirectLine(planId, waypoints, color, map, originCoord) {
    if (!map || !_AMapInstance) return

    // ── 清理旧图层 ──
    _clearPlanLayers(planId)

    const coords = waypoints.map(w => [w.lng, w.lat])

    // ── 1. 创建双层实线 ──
    const outline = new _AMapInstance.Polyline({
      path: coords, strokeColor: color,
      ...DEFAULT_STYLE.outline, zIndex: 49,
    })
    const core = new _AMapInstance.Polyline({
      path: coords, strokeColor: color,
      ...DEFAULT_STYLE.core, zIndex: 50,
    })
    outline.setMap(map)
    core.setMap(map)

    // ── 2. 创建终点 Marker（最后一个 waypoint）──
    const endPoint = waypoints[waypoints.length - 1]
    const endLabel = endPoint.name || '目的地'
    const endMarker = new _AMapInstance.Marker({
      position: [endPoint.lng, endPoint.lat],
      content: _createMarkerContent(endLabel, '#F56C6C'),
      offset: new _AMapInstance.Pixel(0, -32),
      zIndex: 80,
    })
    endMarker.setMap(map)

    const markers = [endMarker]

    // ── 3. 创建起点 Marker（出发城市）──
    if (originCoord) {
      // 如果有出发城市坐标，放在路线起点的上游方向
      const startLabel = originCoord.name || '出发'
      const startMarker = new _AMapInstance.Marker({
        position: [originCoord.lng, originCoord.lat],
        content: _createMarkerContent(startLabel, '#28C76F'),
        offset: new _AMapInstance.Pixel(0, -32),
        zIndex: 80,
      })
      startMarker.setMap(map)
      markers.unshift(startMarker)

      // 如果出发城市坐标与第一个 waypoint 不同，画一条虚线连接
      const firstWp = waypoints[0]
      const dist = Math.abs(originCoord.lng - firstWp.lng) + Math.abs(originCoord.lat - firstWp.lat)
      if (dist > 0.05) {
        const approachLine = new _AMapInstance.Polyline({
          path: [[originCoord.lng, originCoord.lat], [firstWp.lng, firstWp.lat]],
          strokeColor: color,
          strokeWeight: 2, strokeOpacity: 0.35, strokeStyle: 'dashed',
          lineJoin: 'round', lineCap: 'round', zIndex: 45,
        })
        approachLine.setMap(map)
        // 存储额外 polyline 以便清理
        planRoutes.value = {
          ...planRoutes.value,
          [planId]: {
            color,
            polylines: [{ outline, core }],
            extraPolylines: [approachLine],
            markers,
            waypoints,
            _hasCongestion: false,
          }
        }
        // 自适应视野
        _fitAllRoutes(map)
        return
      }
    }

    // 存储
    planRoutes.value = {
      ...planRoutes.value,
      [planId]: { color, polylines: [{ outline, core }], markers, waypoints, _hasCongestion: false }
    }

    _fitAllRoutes(map)
  }

  // ── 自适应视野 ──
  function _fitAllRoutes(map) {
    const allOutlines = Object.values(planRoutes.value)
      .flatMap(r => r.polylines.map(p => p.outline))
    if (allOutlines.length > 0) {
      map.setFitView(allOutlines, false, [60, 60, 60, 60])
    }
  }

  // ── 清理单个方案的图层 ──
  function _clearPlanLayers(planId) {
    const oldRoute = planRoutes.value[planId]
    if (!oldRoute) return

    // 清理 polylines
    if (oldRoute.polylines) {
      oldRoute.polylines.forEach(pair => {
        try { pair.outline?.setMap(null) } catch { /* ignore */ }
        try { pair.core?.setMap(null) } catch { /* ignore */ }
      })
    }
    // 清理额外 polylines（出发城市连线等）
    if (oldRoute.extraPolylines) {
      oldRoute.extraPolylines.forEach(p => {
        try { p.setMap(null) } catch { /* ignore */ }
      })
    }
    // 清理 markers
    if (oldRoute.markers) {
      oldRoute.markers.forEach(m => {
        try { m.setMap(null) } catch { /* ignore */ }
      })
=======
  // ── TMC 分段构建 ──
  async function buildCongestionSegments(steps, baselineColor) {
    const segments = []
    let hasAnyCongestion = false

    // Step 1: 并行加载各 step 的 TMC 数据
    const stepsWithTMC = await Promise.all(
      steps.map(async (step) => {
        let tmcs = step.tmcs || []

        // 如果没有 tmcs 且有 loadDetail 方法，尝试加载
        if ((!tmcs || tmcs.length === 0) && typeof step.loadDetail === 'function') {
          try {
            await new Promise((resolve) => {
              step.loadDetail(() => resolve())
            })
            tmcs = step.tmcs || []
          } catch {
            // loadDetail 失败，保持 tmcs 为空
          }
        }

        return { step, tmcs }
      })
    )

    // Step 2: 按 TMC 分段切片坐标
    for (const { step, tmcs } of stepsWithTMC) {
      const path = step.path || []
      if (path.length < 2) continue

      if (!tmcs || tmcs.length === 0) {
        // 无 TMC → 整段用基线色
        segments.push({ path: [...path], strokeColor: baselineColor })
        continue
      }

      // 计算总距离（优先用 step.distance，否则用 TMC 累加）
      const totalDist = step.distance || tmcs.reduce((s, t) => s + (t.distance || 0), 0)
      if (totalDist <= 0) {
        segments.push({ path: [...path], strokeColor: baselineColor })
        continue
      }

      // 按 TMC 距离占比切片 path
      let pathCursor = 0
      const pathLen = path.length

      for (const tmc of tmcs) {
        const segDist = tmc.distance || 0
        const ratio = Math.min(segDist / totalDist, 1.0)
        const segPathLen = Math.max(2, Math.round(ratio * pathLen))
        const endIdx = Math.min(pathCursor + segPathLen, pathLen)
        const segPath = path.slice(pathCursor, endIdx)

        if (segPath.length >= 2) {
          const tmcStatus = tmc.status || '未知'
          const segColor = CONGESTION_COLORS[tmcStatus] || baselineColor
          if (tmcStatus !== '畅通' && tmcStatus !== '未知') {
            hasAnyCongestion = true
          }
          segments.push({
            path: segPath,
            strokeColor: segColor,
          })
        }

        pathCursor = endIdx
        if (pathCursor >= pathLen) break
      }

      // 剩余坐标（TMC 分段未覆盖的部分）→ 基线色
      if (pathCursor < pathLen - 1) {
        const remaining = path.slice(pathCursor)
        if (remaining.length >= 2) {
          segments.push({ path: remaining, strokeColor: baselineColor })
        }
      }
    }

    return { segments, hasAnyCongestion }
  }

  // ── 降级：直线连接 ──
  function drawFallback(planId, waypoints, color, map) {
    if (!map || !_AMapInstance) return

    // 清理旧路线
    const oldRoute = planRoutes.value[planId]
    if (oldRoute?.polylines) {
      oldRoute.polylines.forEach(p => {
        try { p.setMap(null) } catch { /* ignore */ }
      })
    }

    const coords = waypoints.map(w => [w.lng, w.lat])
    const poly = new _AMapInstance.Polyline({
      path: coords,
      strokeColor: color,
      strokeWeight: DEFAULT_STYLE.strokeWeight,
      strokeOpacity: DEFAULT_STYLE.strokeOpacity,
      strokeStyle: 'dashed',
      lineJoin: 'round',
      showDir: true,
      zIndex: 50,
    })
    poly.setMap(map)

    planRoutes.value = {
      ...planRoutes.value,
      [planId]: { color, polylines: [poly], waypoints, _hasCongestion: false }
    }

    const allPolylines = Object.values(planRoutes.value)
      .flatMap(r => r.polylines)
    if (allPolylines.length > 0) {
      map.setFitView(allPolylines, false, [60, 60, 60, 60])
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    }
  }

  // ── 高亮 / 半透明 ──
  function highlightPlan(planId) {
<<<<<<< HEAD
=======
    // Toggle: 同一方案再次点击 → 取消选中
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    if (highlightedPlanId.value === planId) {
      resetHighlight()
      return
    }

    highlightedPlanId.value = planId

    for (const [pid, route] of Object.entries(planRoutes.value)) {
      const style = pid === planId ? HIGHLIGHTED_STYLE : DIMMED_STYLE
<<<<<<< HEAD
      route.polylines.forEach(pair => _applyPairStyle(pair, style))

      // 同步 Marker 透明度
      if (route.markers) {
        const opacity = pid === planId ? 1.0 : 0.35
        route.markers.forEach(m => {
          try {
            const el = m.getContent?.()
            if (typeof el === 'string') {
              m.setContent(el.replace(/opacity:[0-9.]+/, `opacity:${opacity}`))
            }
          } catch { /* ignore */ }
        })
      }

      // 同步额外 polyline 透明度
      if (route.extraPolylines) {
        route.extraPolylines.forEach(p => {
          try { p.setOptions({ strokeOpacity: pid === planId ? 0.5 : 0.12 }) } catch { /* ignore */ }
        })
      }
=======
      route.polylines.forEach(p => {
        try { p.setOptions(style) } catch { /* ignore */ }
      })
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    }
  }

  function resetHighlight() {
    highlightedPlanId.value = null
    for (const route of Object.values(planRoutes.value)) {
<<<<<<< HEAD
      route.polylines.forEach(pair => _applyPairStyle(pair, DEFAULT_STYLE))

      if (route.markers) {
        route.markers.forEach(m => {
          try {
            const el = m.getContent?.()
            if (typeof el === 'string') {
              m.setContent(el.replace(/opacity:[0-9.]+/, 'opacity:1.0'))
            }
          } catch { /* ignore */ }
        })
      }

      if (route.extraPolylines) {
        route.extraPolylines.forEach(p => {
          try { p.setOptions({ strokeOpacity: 0.35 }) } catch { /* ignore */ }
        })
      }
    }
  }

  // ── 清理全部 ──
  function clearAll() {
    for (const planId of Object.keys(planRoutes.value)) {
      _clearPlanLayers(planId)
=======
      route.polylines.forEach(p => {
        try { p.setOptions(DEFAULT_STYLE) } catch { /* ignore */ }
      })
    }
  }

  // ── 清理 ──
  function clearAll() {
    for (const route of Object.values(planRoutes.value)) {
      route.polylines.forEach(p => {
        try { p.setMap(null) } catch { /* ignore */ }
      })
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    }
    planRoutes.value = {}
    highlightedPlanId.value = null
  }

  // ── 公开 API ──
  return {
    planRoutes,
    highlightedPlanId,
    loading,
    hasCongestion,
    addPlanRoute,
    highlightPlan,
    resetHighlight,
    clearAll,
    PLAN_COLORS,
  }
}
