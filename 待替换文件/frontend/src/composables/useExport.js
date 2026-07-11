/**
 * useExport.js — 行程导出为图片。
 *
 * 策略：AMap WebGL Canvas 无法被 html2canvas 捕获（黑屏），
 * 采用 MapContainer.getCanvas() + html2canvas(TripCard DOM) 手动拼接。
 */

/**
 * 导出行程方案为 PNG 图片。
 *
 * @param {object}   mapContainerRef  MapContainer 组件的 ref（需 expose getMapCanvas）
 * @param {object}   tripCardEl       TripCard 的 DOM 根元素
 * @param {string}   filename         下载文件名
 * @returns {Promise<void>}
 */
export async function exportTripWithMap(mapContainerRef, tripCardEl, filename = '潮汕行程方案.png') {
  try {
    const mapCanvas = mapContainerRef?.getMapCanvas?.()
    const cardEl = tripCardEl?.$el || tripCardEl

    if (!cardEl) {
      console.warn('[useExport] TripCard element not found')
      return
    }

    // 动态加载 html2canvas（仅 TripCard DOM 部分）
    const html2canvas = (await import('html2canvas')).default

    const cardCanvas = await html2canvas(cardEl, {
      scale: 2,
      backgroundColor: '#ffffff',
      useCORS: true,
    })

    // 创建合并 canvas
    const mapHeight = mapCanvas ? mapCanvas.height : 0
    const mapWidth = mapCanvas ? mapCanvas.width : cardCanvas.width

    const canvas = document.createElement('canvas')
    canvas.width = Math.max(mapWidth, cardCanvas.width)
    canvas.height = mapHeight + cardCanvas.height

    const ctx = canvas.getContext('2d')

    // 绘制地图
    if (mapCanvas) {
      ctx.fillStyle = '#f5f5f5'
      ctx.fillRect(0, 0, canvas.width, mapHeight)
      ctx.drawImage(mapCanvas, 0, 0)
    }

    // 绘制 TripCard
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, mapHeight, canvas.width, cardCanvas.height)
    ctx.drawImage(cardCanvas, 0, mapHeight)

    // 下载
    const link = document.createElement('a')
    link.download = filename
    link.href = canvas.toDataURL('image/png')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (e) {
    console.error('[useExport] Export failed:', e)
    throw e
  }
}

/**
 * 导出行程为纯文本格式。
 *
 * @param {object} plan  行程方案对象
 * @returns {string}
 */
export function planToText(plan) {
  const lines = []
  lines.push(`【${plan.title || plan.theme || '行程方案'}】`)
  if (plan.summary) lines.push(plan.summary)

  // 交通
  if (plan.transport) {
    const t = plan.transport
    lines.push('\n🚗 交通方案：')
    if (t.to) lines.push(`  去程：${t.to.route} · ${t.to.duration} · ¥${t.to.cost}/人`)
    if (t.return) lines.push(`  返程：${t.return.route} · ${t.return.duration} · ¥${t.return.cost}/人`)
  }

  // 每日行程
  if (plan.days?.length) {
    for (const day of plan.days) {
      lines.push(`\n📅 Day ${day.day} · ${day.title}`)
      for (const act of (day.activities || [])) {
        lines.push(`  ${act.time} ${act.name} [${act.type}] ${act.cost || ''}`)
        if (act.description) lines.push(`    ${act.description}`)
      }
    }
  }

  // 费用
  if (plan.estimated_cost) {
    const c = plan.estimated_cost
    lines.push('\n💰 预估费用（每人）：')
    if (c.transport) lines.push(`  交通：¥${c.transport}`)
    if (c.hotel) lines.push(`  住宿：¥${c.hotel}`)
    if (c.food) lines.push(`  餐饮：¥${c.food}`)
    if (c.tickets) lines.push(`  门票：¥${c.tickets}`)
    lines.push(`  合计：¥${c.total}`)
  }

  // 贴士
  if (plan.tips?.length) {
    lines.push('\n📝 出行贴士：')
    plan.tips.forEach(t => lines.push(`  • ${t}`))
  }

  return lines.join('\n')
}
