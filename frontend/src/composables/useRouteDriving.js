/**
 * useRouteDriving.js — 高德驾车路线 + TMC 拥堵分段着色
 *
 * 核心职责：
 *   1. 封装 AMap.Driving 调用（policy=0 最快捷 + extensions='all' 获取 TMC）
 *   2. 解析 TMC 拥堵数据 → 按 status 分段着色
 *   3. 管理地图上的 Polyline 图层（逐方案增量添加）
 *   4. 路线高亮/半透明切换（选中方案 vs 其他方案）
 *
 * 使用方式：
 *   const { addPlanRoute, highlightPlan, resetHighlight, clearAll, planRoutes, highlightedPlanId } = useRouteDriving(mapRef)
 *
 *   // SSE 逐方案到达时：
 *   await addPlanRoute('A', waypointsA)  // 立即画出绿色路线
 *   await addPlanRoute('B', waypointsB)  // 立即画出橙色路线
 *   await addPlanRoute('C', waypointsC)  // 立即画出蓝色路线
 *
 *   // 用户交互：
 *   highlightPlan('A')   // 方案A高亮，B/C半透明
 *   resetHighlight()     // 恢复全部默认样式
 */

import { ref, computed } from 'vue'
import { loadAMap } from '@/utils/loadAmap'

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
}

// ── 方案基线色 ──
export const PLAN_COLORS = {
  A: '#28C76F', // 活力绿 — 美食
  B: '#FF9F43', // 琥珀橙 — 文化
  C: '#0091FF', // 科技蓝 — 综合
}

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

export function useRouteDriving(mapRef) {
  // ── 响应式状态 ──
  const planRoutes = ref({})
  const highlightedPlanId = ref(null)
  const loading = ref(false)

  // 是否有任何路线包含拥堵段
  const hasCongestion = computed(() => {
    return Object.values(planRoutes.value).some(r => r._hasCongestion)
  })

  // ── 内部状态 ──
  let driving = null

  // ── 获取地图实例 ──
  function getMap() {
    if (!mapRef) return null
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
  }

  // ── 添加单个方案的路线（增量调用）──
  /**
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
    } finally {
      loading.value = false
    }
  }

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
    }
  }

  // ── 高亮 / 半透明 ──
  function highlightPlan(planId) {
    // Toggle: 同一方案再次点击 → 取消选中
    if (highlightedPlanId.value === planId) {
      resetHighlight()
      return
    }

    highlightedPlanId.value = planId

    for (const [pid, route] of Object.entries(planRoutes.value)) {
      const style = pid === planId ? HIGHLIGHTED_STYLE : DIMMED_STYLE
      route.polylines.forEach(p => {
        try { p.setOptions(style) } catch { /* ignore */ }
      })
    }
  }

  function resetHighlight() {
    highlightedPlanId.value = null
    for (const route of Object.values(planRoutes.value)) {
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
