/**
 * mapAdapter.js — plan 数据 → MapContainer props 转换器
 *
 * 坐标约定：AMap 原生 [lng, lat] 顺序
 * enrichment 中的 {lat, lng} 字段直接映射为 marker {lng, lat}
 *
 * 每个 marker 携带 minZoom（缩放阈值）和 detail（悬浮详情字段），
 * 供 MapContainer 实现缩放渐进式展示 + 悬浮 infoWindow。
 */

// ── 缩放阈值常量 ──
export const ZOOM_THRESHOLDS = {
  transport: 0,    // waypoint 始终可见
  weather: 11,
  food: 11,
  heritage: 13,
  hotel: 13,
  interest: 15,    // crowd 复用
}

// ── 内部 helper：key 规范化（兼容 route_ 前缀旧数据） ──
function getEnrichmentArray(enrichment, baseKey) {
  if (!enrichment) return []
  // 1. 短 key（标准化格式）
  if (Array.isArray(enrichment[baseKey])) return enrichment[baseKey]
  // 2. route_ 前缀（旧数据兼容）
  const routeKey = 'route_' + baseKey
  if (Array.isArray(enrichment[routeKey])) return enrichment[routeKey]
  // 3. 单复数 fallback
  const singular = baseKey.replace(/s$/, '')
  if (Array.isArray(enrichment[singular])) return enrichment[singular]
  if (Array.isArray(enrichment['route_' + singular])) return enrichment['route_' + singular]
  return []
}

// ── 坐标安全转换 ──
function toLngLatArray(coords) {
  if (!coords?.length) return []
  // 自动检测：纬度范围 -90~90，经度范围 -180~180
  // 如果 coords[0][0] > 90，说明已经是 [lng, lat]，直接返回
  if (Math.abs(coords[0][0]) > 90) return coords
  // 否则是 [lat, lng]，需要翻转
  return coords.map(([a, b]) => [b, a])
}

// ── 中心计算 ──
function computeCenter(waypoints) {
  if (!waypoints?.length) return [116.68, 23.35]  // 默认：汕头
  const n = waypoints.length
  return [
    waypoints.reduce((s, w) => s + w.lng, 0) / n,
    waypoints.reduce((s, w) => s + w.lat, 0) / n,
  ]
}

// ── Marker 工厂 ──
const T = { WAYPOINT: 'transport', WEATHER: 'weather', FOOD: 'food', HERITAGE: 'heritage', HOTEL: 'hotel', CROWD: 'interest' }

function mk(lat, lng, type, opts) {
  if (lat == null || lng == null) return null
  const minZoom = ZOOM_THRESHOLDS[type] ?? 0
  return { lng, lat, type, minZoom, ...opts }
}

// ── 公开 API ──

export function planToMapData(plan, opts = {}) {
  const { maxPerType = 10 } = opts
  const geo = plan?.route_geo
  const enr = plan?.enrichment
  const waypoints = geo?.waypoints || []

  const markers = [
    ...waypointsToMarkers(waypoints),
    ...enrichmentToMarkers(enr, maxPerType),
  ].filter(Boolean)

  return {
    center: computeCenter(waypoints),
    markers,
    routeLine: toLngLatArray(geo?.route_line || []),
    heatmapData: crowdToHeatmap(getEnrichmentArray(enr, 'crowd')),
  }
}

export function waypointsToMarkers(waypoints) {
  return waypoints.map((wp, i) => mk(wp.lat, wp.lng, T.WAYPOINT, {
    title: wp.name,
    subtitle: `第${i + 1}站`,
    detail: {
      label: '途经点',
      fields: [
        { key: '名称', val: wp.name },
        { key: '序号', val: `第${i + 1}站` },
      ],
    },
  }))
}

export function enrichmentToMarkers(enrichment, maxPerType = 10) {
  const markers = []

  // ── 天气 ──
  getEnrichmentArray(enrichment, 'weather').slice(0, maxPerType).forEach(w => {
    if (w.lat == null || w.lng == null) return
    markers.push(mk(w.lat, w.lng, T.WEATHER, {
      title: `${w.city || w.name || ''} ${w.temperature ?? ''}℃`,
      subtitle: w.weather_desc || '',
      temp: w.temperature != null ? `${w.temperature}℃` : '',
      detail: {
        label: '天气',
        fields: [
          { key: '城市', val: w.city || w.name || '—' },
          { key: '温度', val: w.temperature != null ? `${w.temperature}℃` : '—' },
          { key: '天气', val: w.weather_desc || '—' },
          { key: '湿度', val: w.humidity != null ? `${w.humidity}%` : '—' },
          { key: '风力', val: w.wind_level != null ? `${w.wind_level}级` : '—' },
        ].filter(f => f.val && f.val !== '—'),
      },
    }))
  })

  // ── 美食 ──
  getEnrichmentArray(enrichment, 'foods').slice(0, maxPerType).forEach(f => {
    markers.push(mk(f.lat, f.lng, T.FOOD, {
      title: f.name,
      subtitle: f.distance_km != null ? `${f.distance_km.toFixed(1)}km · ${f.price_range || ''}` : '',
      detail: {
        label: '美食',
        fields: [
          { key: '名称', val: f.name },
          { key: '类型', val: f.type || '—' },
          { key: '距离', val: f.distance_km != null ? `${f.distance_km.toFixed(1)}km` : '—' },
          { key: '价格', val: f.price_range || '—' },
        ],
      },
    }))
  })

  // ── 非遗 ──
  getEnrichmentArray(enrichment, 'heritages').slice(0, maxPerType).forEach(h => {
    markers.push(mk(h.lat, h.lng, T.HERITAGE, {
      title: h.name,
      subtitle: h.distance_km != null ? `${h.distance_km.toFixed(1)}km · ${h.category || ''}` : '',
      detail: {
        label: '非遗',
        fields: [
          { key: '名称', val: h.name },
          { key: '类别', val: h.category || '—' },
          { key: '类型', val: h.type || '—' },
          { key: '距离', val: h.distance_km != null ? `${h.distance_km.toFixed(1)}km` : '—' },
        ],
      },
    }))
  })

  // ── 酒店 ──
  getEnrichmentArray(enrichment, 'hotels').slice(0, maxPerType).forEach(h => {
    markers.push(mk(h.lat, h.lng, T.HOTEL, {
      title: h.name,
      subtitle: `${'⭐'.repeat(h.stars || 0)} ¥${h.price_min ?? '—'}/晚`,
      detail: {
        label: '酒店',
        fields: [
          { key: '名称', val: h.name },
          { key: '星级', val: '⭐'.repeat(h.stars || 0) || '—' },
          { key: '价格', val: h.price_min != null ? `¥${h.price_min}~${h.price_max || '—'}/晚` : '—' },
          { key: '距离', val: h.distance_km != null ? `${h.distance_km.toFixed(1)}km` : '—' },
        ],
      },
    }))
  })

  // ── 人流 ──
  getEnrichmentArray(enrichment, 'crowd').slice(0, maxPerType).forEach(c => {
    markers.push(mk(c.lat, c.lng, T.CROWD, {
      title: c.location_name,
      subtitle: `${c.crowd_level || '—'} · ${c.estimated_count || 0}人`,
      detail: {
        label: '人流',
        fields: [
          { key: '地点', val: c.location_name },
          { key: '拥挤度', val: c.crowd_level || '—' },
          { key: '预估人数', val: c.estimated_count ? `${c.estimated_count}人` : '—' },
          { key: '距离', val: c.distance_km != null ? `${c.distance_km.toFixed(1)}km` : '—' },
        ],
      },
    }))
  })

  return markers.filter(Boolean)
}

export function crowdToHeatmap(crowdItems) {
  return crowdItems
    .filter(c => c.estimated_count > 0 && c.lat != null && c.lng != null)
    .map(c => ({ lng: c.lng, lat: c.lat, count: c.estimated_count }))
}

// ─────────────────────────────────────────────
//  路线途经点提取（Phase 7 — 地图路线可视化）
// ─────────────────────────────────────────────

/**
 * 从 plan 中提取 AMap.Driving 所需的途经点坐标。
 * 顺序：从 plan.days[].activities[] 按时间排列提取所有有坐标的 activity，
 *       优先使用 route_geo.waypoints，fallback 到 days 中的 activities。
 *
 * @param {Object} plan — enriched trip plan
 * @returns {Array<{lng: number, lat: number, name: string}>}
 */
export function extractPlanWaypoints(plan) {
  // 优先：route_geo.waypoints（后端已整理好顺序和坐标）
  const geoWaypoints = plan?.route_geo?.waypoints
  if (geoWaypoints && geoWaypoints.length >= 2) {
    return geoWaypoints.map(wp => ({
      lng: wp.lng,
      lat: wp.lat,
      name: wp.name || '',
    }))
  }

  // Fallback：从 days[].activities[] 中按时间提取
  const days = plan?.days || []
  const waypoints = []
  for (const day of days) {
    const activities = day.activities || []
    for (const act of activities) {
      if (act.lat != null && act.lng != null) {
        waypoints.push({
          lng: act.lng,
          lat: act.lat,
          name: act.name || '',
        })
      }
    }
  }
  return waypoints
}

// ─────────────────────────────────────────────
//  平台数据 → Markers 转换器（新增 Phase 3.5）
// ─────────────────────────────────────────────

/** 美食列表 → food markers */
export function foodsToMarkers(foods, maxCount = 30) {
  return foods.slice(0, maxCount).map(f => {
    const lat = f.latitude != null ? Number(f.latitude) : null
    const lng = f.longitude != null ? Number(f.longitude) : null
    return mk(lat, lng, T.FOOD, {
      title: f.name,
      subtitle: [f.category_name, f.price_range].filter(Boolean).join(' · '),
      detail: {
        label: '美食',
        fields: [
          { key: '名称', val: f.name },
          { key: '分类', val: f.category_name || '—' },
          { key: '价格', val: f.price_range || '—' },
          { key: '区域', val: f.region || '—' },
          { key: '热度', val: f.view_count != null ? `${f.view_count}次浏览` : '—' },
        ],
      },
    })
  })
}

/** 非遗项目列表 → heritage markers */
export function heritagesToMarkers(heritages, maxCount = 30) {
  return heritages.slice(0, maxCount).map(h => {
    const lat = h.latitude != null ? Number(h.latitude) : null
    const lng = h.longitude != null ? Number(h.longitude) : null
    return mk(lat, lng, T.HERITAGE, {
      title: h.name,
      subtitle: [h.category, h.type].filter(Boolean).join(' · '),
      detail: {
        label: '非遗',
        fields: [
          { key: '名称', val: h.name },
          { key: '级别', val: h.category || '—' },
          { key: '类型', val: h.type || '—' },
          { key: '传承人', val: h.inheritor || '—' },
          { key: '区域', val: h.region || '—' },
        ],
      },
    })
  })
}

/** 民俗活动列表 → heritage markers（用 🎭 标识区分） */
export function eventsToMarkers(events, maxCount = 30) {
  return events.slice(0, maxCount).map(e => {
    const lat = e.latitude != null ? Number(e.latitude) : null
    const lng = e.longitude != null ? Number(e.longitude) : null
    const dateStr = e.event_date || ''
    return mk(lat, lng, T.HERITAGE, {
      title: e.name,
      subtitle: [e.region, dateStr].filter(Boolean).join(' · '),
      icon: '🎭',
      detail: {
        label: '民俗',
        fields: [
          { key: '名称', val: e.name },
          { key: '类型', val: e.event_type || '—' },
          { key: '区域', val: e.region || '—' },
          { key: '日期', val: dateStr || '—' },
          { key: '地址', val: e.address || '—' },
        ],
      },
    })
  })
}

/** 酒店列表 → hotel markers */
export function hotelsToMarkers(hotels, maxCount = 30) {
  return hotels.slice(0, maxCount).map(h => {
    const lat = h.latitude != null ? Number(h.latitude) : null
    const lng = h.longitude != null ? Number(h.longitude) : null
    const priceStr = h.price_min != null
      ? `¥${h.price_min}~${h.price_max || '—'}/晚`
      : ''
    return mk(lat, lng, T.HOTEL, {
      title: h.name,
      subtitle: [`${'⭐'.repeat(h.stars || 0)}`, priceStr].filter(Boolean).join(' '),
      detail: {
        label: '酒店',
        fields: [
          { key: '名称', val: h.name },
          { key: '星级', val: '⭐'.repeat(h.stars || 0) || '—' },
          { key: '价格', val: priceStr || '—' },
          { key: '区域', val: h.region || '—' },
          { key: '地址', val: h.address || '—' },
        ],
      },
    })
  })
}

/** 人流监测点列表 → interest markers */
export function crowdLocationsToMarkers(crowdItems, maxCount = 30) {
  const levelLabels = { 1: '低', 2: '较低', 3: '中', 4: '较高', 5: '高' }
  return crowdItems.slice(0, maxCount).map(c => {
    const lat = c.latitude != null ? Number(c.latitude) : null
    const lng = c.longitude != null ? Number(c.longitude) : null
    const levelLabel = levelLabels[c.crowd_level] || '—'
    return mk(lat, lng, T.CROWD, {
      title: c.location_name,
      subtitle: `人流${levelLabel} · ${c.estimated_count || 0}人`,
      detail: {
        label: '人流',
        fields: [
          { key: '地点', val: c.location_name },
          { key: '拥挤度', val: levelLabel },
          { key: '预估人数', val: c.estimated_count ? `${c.estimated_count}人` : '—' },
          { key: '承载量', val: c.base_capacity ? `${c.base_capacity}人` : '—' },
          { key: '区域', val: c.region || '—' },
        ],
      },
    })
  })
}

/** 天气数据列表 → weather markers */
export function weatherToMarkers(weatherItems, maxCount = 10) {
  return weatherItems.slice(0, maxCount).map(w => {
    const lat = w.lat != null ? Number(w.lat) : null
    const lng = w.lng != null ? Number(w.lng) : null
    return mk(lat, lng, T.WEATHER, {
      title: `${w.city || w.region || ''} ${w.temperature ?? ''}℃`,
      subtitle: w.weather_desc || '',
      temp: w.temperature != null ? `${w.temperature}℃` : '',
      detail: {
        label: '天气',
        fields: [
          { key: '城市', val: w.city || w.region || '—' },
          { key: '温度', val: w.temperature != null ? `${w.temperature}℃` : '—' },
          { key: '天气', val: w.weather_desc || '—' },
          { key: '湿度', val: w.humidity != null ? `${w.humidity}%` : '—' },
          { key: '风力', val: w.wind_level != null ? `${w.wind_level}级` : '—' },
        ].filter(f => f.val && f.val !== '—'),
      },
    })
  })
}

/**
 * 编排器：将全部平台数据转换为 MapContainer props。
 * @param {Object}  data - { foods, heritages, events, hotels, crowd, weather }
 * @returns {{ center: [lng, lat], markers: Array, heatmapData: Array }}
 */
export function platformDataToMapData({ foods = [], heritages = [], events = [], hotels = [], crowd = [], weather = [] } = {}) {
  const markers = [
    ...foodsToMarkers(foods),
    ...heritagesToMarkers(heritages),
    ...eventsToMarkers(events),
    ...hotelsToMarkers(hotels),
    ...crowdLocationsToMarkers(crowd),
    ...weatherToMarkers(weather),
  ].filter(Boolean)

  // 计算所有 marker 的几何中心，fallback 到汕头
  const valid = markers.filter(m => m.lat != null && m.lng != null)
  const center = valid.length > 0
    ? [
        valid.reduce((s, m) => s + m.lng, 0) / valid.length,
        valid.reduce((s, m) => s + m.lat, 0) / valid.length,
      ]
    : [116.68, 23.35]

  // 热力图数据来自人流点中 estimated_count > 0 的条目
  const heatmapData = crowd
    .filter(c => (c.estimated_count > 0 || c.crowd_level > 0))
    .map(c => ({
      lng: Number(c.longitude),
      lat: Number(c.latitude),
      count: c.estimated_count || (c.crowd_level || 1) * 20,
    }))
    .filter(d => !isNaN(d.lng) && !isNaN(d.lat))

  return { center, markers, heatmapData }
}
