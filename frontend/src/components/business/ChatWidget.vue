<template>
  <div class="chat-widget" :class="{ 'is-open': isOpen }">
    <!-- 悬浮按钮 -->
    <button v-if="!isOpen" class="chat-fab" @click="openChat" aria-label="打开AI助手">
      <el-icon :size="28"><ChatDotRound /></el-icon>
    </button>

    <!-- 聊天弹窗 -->
    <div v-else ref="panelRef" class="chat-panel" :class="{ 'is-dragging': isDragging }" :style="panelStyle">
      <div class="chat-panel__header">
        <!-- 拖拽手柄 — 顶部居中黑色圆角横杠 -->
        <div
          class="drag-handle"
          @mousedown="startDrag"
          @touchstart.prevent="startDrag"
        >
          <div class="drag-handle__bar"></div>
        </div>
        <div class="chat-panel__header-row">
          <div class="chat-panel__title">
            <span class="chat-panel__avatar">🍵</span>
            <span>潮小文 · AI茶伴</span>
          </div>
          <div class="chat-panel__actions">
          <el-button text circle size="small" @click="goFullscreen" title="全屏">
            <el-icon><FullScreen /></el-icon>
          </el-button>
          <el-button text circle size="small" @click="startNewChat" title="新对话">
            <el-icon><Plus /></el-icon>
          </el-button>
          <el-button text circle size="small" @click="closeChat" title="关闭">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        </div>
      </div>

      <div class="chat-panel__body" ref="msgContainer">
        <!-- 欢迎语 — 茶叙语境 -->
        <div v-if="!hasMessages" class="chat-welcome">
          <div class="chat-welcome__icon">🍵</div>
          <div class="chat-welcome__text">
            <p class="chat-welcome__greeting">来食茶。</p>
            <p>我是<strong>潮小文</strong>，你的潮汕文化AI茶伴。</p>
            <p class="chat-welcome__services">
              可以帮你 —<br />
              🍲 觅食寻味 &nbsp; 🎭 探访非遗<br />
              🗺️ 定做行程 &nbsp; 💬 闲聊文化
            </p>
          </div>
          <div class="chat-welcome__suggestions">
            <button
              v-for="q in suggestedQuestions"
              :key="q"
              class="tea-pill"
              @click="sendMessage(q)"
            >
              {{ q }}
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="msg in messages" :key="msg.id" class="chat-message" :class="`is-${msg.role}`">
          <!-- 文本消息 -->
          <div v-if="msg.type === 'text'" class="chat-message__bubble">
            <div class="chat-message__text">{{ msg.content }}</div>
            <span v-if="isStreaming && msg.id === lastMessageId && msg.role === 'assistant'" class="chat-cursor">|</span>
          </div>

          <!-- 行程方案（纯文字排版） -->
          <div v-else-if="msg.type === 'trip_text'" class="chat-message__bubble chat-trip-text">
            <div class="trip-text__content" v-html="msg.content"></div>
            <div class="trip-text__actions">
              <el-button size="small" text @click="handleSaveTripText(msg)">
                💾 保存到我的行程
              </el-button>
              <el-button size="small" text @click="handleCopyTripText(msg)">
                📋 复制
              </el-button>
              <el-button size="small" text @click="handleRefreshTrip">
                🔄 换一换
              </el-button>
            </div>
          </div>

          <!-- 美食卡片 -->
          <FoodCard
            v-else-if="msg.type === 'food_card'"
            :items="msg.cardData?.items || []"
            :summary="msg.cardData?.summary || ''"
            @favorite="handleFavorite"
          />

          <!-- 非遗卡片 -->
          <HeritageCard
            v-else-if="msg.type === 'heritage_card'"
            :item="msg.cardData"
            @favorite="handleFavorite"
          />

          <!-- 意图导航按钮（多意图，主次分明） -->
          <div
            v-if="msg.intents?.length && msg.role === 'assistant'"
            class="intent-nav"
          >
            <el-button
              v-for="(item, idx) in msg.intents.filter(i => INTENT_CONFIG[i.intent]).slice(0, 3)"
              :key="item.intent"
              :type="item.primary ? 'primary' : 'default'"
              :class="{ 'is-primary-intent': item.primary, 'is-secondary-intent': !item.primary }"
              round
              size="small"
              @click="router.push(INTENT_CONFIG[item.intent].path)"
            >
              {{ item.primary ? INTENT_CONFIG[item.intent].label : (INTENT_CONFIG[item.intent].secondaryLabel || INTENT_CONFIG[item.intent].label) }}
            </el-button>
          </div>
        </div>

        <!-- 冲泡中 — 茶叙 thinking 状态 -->
        <div v-if="chatStore.thinkingLabel" class="chat-thinking">
          <span class="chat-thinking__steam">
            <span class="steam-dot"></span>
            <span class="steam-dot"></span>
            <span class="steam-dot"></span>
          </span>
          <span class="chat-thinking__label">冲泡中...</span>
        </div>

        <!-- 快捷选项 -->
        <div v-if="quickOptions.length" class="chat-quick-options">
          <el-button
            v-for="opt in quickOptions"
            :key="opt"
            size="small"
            round
            :disabled="isStreaming"
            @click="sendMessage(opt)"
          >
            {{ opt }}
          </el-button>
        </div>

        <!-- 错误提示 -->
        <div v-if="streamError" class="chat-error">
          <el-alert :title="streamError" type="error" :closable="true" @close="streamError = null" show-icon />
        </div>
      </div>

      <div class="chat-panel__footer">
        <el-input
          v-model="inputText"
          placeholder="输入问题..."
          :disabled="isStreaming"
          :maxlength="2000"
          @keyup.enter="sendCurrentMessage"
          class="chat-input"
        >
          <template #append>
            <el-button
              :disabled="!inputText.trim() || isStreaming"
              :loading="isStreaming"
              @click="sendCurrentMessage"
              :icon="Promotion"
            />
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Plus, Close, FullScreen, Promotion, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useChatStore, INTENT_CONFIG } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { useSSE } from '@/composables/useSSE'
import { tripApi } from '@/api/trip'
import { userApi } from '@/api/user'
import FoodCard from './FoodCard.vue'
import HeritageCard from './HeritageCard.vue'

const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()
const { isStreaming, streamChat } = useSSE()

const inputText = ref('')
const streamError = ref(null)
const msgContainer = ref(null)
const quickOptions = ref([])
const lastTripParams = ref(null)
const tripPlans = ref([])
const savedTripPlans = ref([])       // persisted across onDone for save button
const enrichmentByPlanId = ref({})  // Phase 2: enrichment data keyed by plan_id

// ── 拖拽状态（仅作用于 panel，FAB 按钮固定不动）──
const panelRef = ref(null)
const isDragging = ref(false)
const panelPos = ref(null) // null = 使用 CSS 默认定位；{ left, top } = 自定义位置
let dragStartMouse = { x: 0, y: 0 }
let dragStartPos = { left: 0, top: 0 }

const panelStyle = computed(() => {
  if (!panelPos.value) return {}
  return {
    position: 'fixed',
    left: panelPos.value.left + 'px',
    top: panelPos.value.top + 'px',
    right: 'auto',
    bottom: 'auto',
  }
})

function startDrag(e) {
  if (!panelRef.value) return
  const rect = panelRef.value.getBoundingClientRect()

  isDragging.value = true
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY
  dragStartMouse = { x: clientX, y: clientY }

  panelPos.value = { left: rect.left, top: rect.top }
  dragStartPos = { ...panelPos.value }

  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', stopDrag)
}

function onDrag(e) {
  if (!isDragging.value) return
  e.preventDefault()
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const clientY = e.touches ? e.touches[0].clientY : e.clientY

  const dx = clientX - dragStartMouse.x
  const dy = clientY - dragStartMouse.y

  let newLeft = dragStartPos.left + dx
  let newTop = dragStartPos.top + dy

  // 只约束拖拽横杠不超出屏幕（横杠在 panel 顶部居中，40px 宽）
  // 面板本身可以部分溢出屏幕
  if (panelRef.value) {
    const panelW = panelRef.value.offsetWidth
    // 横杠左右各 20px 必须在视口内
    const barHalf = 20
    newLeft = Math.max(barHalf - panelW / 2, Math.min(newLeft, window.innerWidth - barHalf - panelW / 2))
    // 横杠垂直方向：top 不低于 0，横杠区域不超出窗口底部
    newTop = Math.max(0, Math.min(newTop, window.innerHeight - 60))
  }

  panelPos.value = { left: newLeft, top: newTop }
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
}

const isOpen = ref(false)
const messages = computed(() => chatStore.messages)
const hasMessages = computed(() => chatStore.hasMessages)
const lastMessageId = computed(() => {
  const msgs = chatStore.messages
  return msgs.length ? msgs[msgs.length - 1].id : null
})

// 同步 store 的 isOpen 状态
watch(() => chatStore.isOpen, v => { isOpen.value = v })
watch(isOpen, v => { v ? chatStore.open() : chatStore.close() })

const suggestedQuestions = [
  '帮我规划3天潮汕美食之旅',
  '潮汕有什么必吃的美食？',
  '英歌舞是什么？',
  '从深圳出发去潮汕玩4天',
]

function openChat() { isOpen.value = true }
function closeChat() { isOpen.value = false }

function goFullscreen() {
  router.push('/chat')
}

function startNewChat() {
  chatStore.startNewSession()
  streamError.value = null
  quickOptions.value = []
  lastTripParams.value = null
  tripPlans.value = []
  savedTripPlans.value = []
  enrichmentByPlanId.value = {}
}

function sendCurrentMessage() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return
  sendMessage(text)
  inputText.value = ''
}

async function sendMessage(text) {
  if (isStreaming.value) return
  streamError.value = null
  quickOptions.value = []
  tripPlans.value = []
  chatStore.addMessage('user', text)

  await streamChat(chatStore.sessionId, text, {
    onToken(token) {
      chatStore.appendToken(token)
      scrollToBottom()
    },
    onDone(sessionId) {
      if (sessionId) chatStore.setSessionId(sessionId)
      // Phase 2: merge enrichment into trip plans before formatting
      if (tripPlans.value.length > 0) {
        for (const plan of tripPlans.value) {
          if (enrichmentByPlanId.value[plan.plan_id]) {
            plan.enrichment = enrichmentByPlanId.value[plan.plan_id]
          }
        }
        // Persist plans for save button (tripPlans is cleared below)
        savedTripPlans.value = tripPlans.value.map(p => ({ ...p }))
        const formattedText = formatTripPlansAsText(tripPlans.value)
        const msgId = chatStore.addMessage('assistant', formattedText, 'trip_text')
        // Attach trip plans to the message so handleSaveTripText can access them
        chatStore.updateMessage(msgId, { tripPlans: tripPlans.value.map(p => ({ ...p })) })
        tripPlans.value = []
        enrichmentByPlanId.value = {}
      }
      // 意图导航 — useSSE 的 done 事件已通过 setLastAssistantIntents 处理
      // 此处保留兜底：如果 currentIntent 有值但 intents 未设置
      if (chatStore.currentIntent && !chatStore.messages[chatStore.messages.length - 1]?.intents?.length) {
        chatStore.setLastAssistantIntent(chatStore.currentIntent)
      }
      scrollToBottom()
    },
    onThinking(label) {
      chatStore.setThinking(label)
    },
    onAsk(question, options, intent, intents) {
      chatStore.clearThinking()
      if (intents?.length) {
        chatStore.setIntent(intents.find(i => i.primary)?.intent || intents[0].intent)
      } else if (intent) {
        chatStore.setIntent(intent)
      }
      if (options?.length) {
        quickOptions.value = options
      }
      if (question) {
        chatStore.addMessage('assistant', question)
      }
      if (intent === 'trip') {
        lastTripParams.value = { question: text, options }
      }
      scrollToBottom()
    },
    onTripCard(plan) {
      chatStore.clearThinking()
      if (plan) {
        tripPlans.value.push(plan)
      }
      scrollToBottom()
    },
    onFoodCard(items, summary) {
      chatStore.clearThinking()
      chatStore.addCardMessage('food_card', { items, summary })
      scrollToBottom()
    },
    onHeritageCard(item) {
      chatStore.clearThinking()
      chatStore.addCardMessage('heritage_card', item)
      scrollToBottom()
    },
    onError(msg) {
      chatStore.clearThinking()
      streamError.value = msg
    },
    // ── Phase 2: Route Enrichment Callbacks ──
    onRouteWeather(data) {
      if (data.plan_id) {
        if (!enrichmentByPlanId.value[data.plan_id]) enrichmentByPlanId.value[data.plan_id] = {}
        enrichmentByPlanId.value[data.plan_id].weather = data.weather || data
      }
    },
    onRouteFoods(data) {
      if (data.plan_id) {
        if (!enrichmentByPlanId.value[data.plan_id]) enrichmentByPlanId.value[data.plan_id] = {}
        enrichmentByPlanId.value[data.plan_id].foods = data.foods || data
      }
    },
    onRouteHeritages(data) {
      if (data.plan_id) {
        if (!enrichmentByPlanId.value[data.plan_id]) enrichmentByPlanId.value[data.plan_id] = {}
        enrichmentByPlanId.value[data.plan_id].heritages = data.heritages || data
      }
    },
    onRouteHotels(data) {
      if (data.plan_id) {
        if (!enrichmentByPlanId.value[data.plan_id]) enrichmentByPlanId.value[data.plan_id] = {}
        enrichmentByPlanId.value[data.plan_id].hotels = data.hotels || data
      }
    },
    onRouteCrowd(data) {
      if (data.plan_id) {
        if (!enrichmentByPlanId.value[data.plan_id]) enrichmentByPlanId.value[data.plan_id] = {}
        enrichmentByPlanId.value[data.plan_id].crowd = data.crowd || data
      }
    },
  })
}

function formatTripPlansAsText(plans) {
  if (!plans || !plans.length) return ''

  let html = ''
  plans.forEach((plan, idx) => {
    if (idx > 0) html += '<hr class="trip-divider">'

    // 标题
    html += `<h3 class="trip-h3">🗺️ 方案${plan.plan_id || idx + 1}：${plan.theme || plan.title || '旅行方案'}</h3>`

    // 概要
    if (plan.summary) {
      html += `<p class="trip-summary">${escapeHtml(plan.summary)}</p>`
    }

    // 交通方案
    if (plan.transport) {
      html += '<h4 class="trip-h4">🚗 交通方案</h4><ul class="trip-ul">'
      if (plan.transport.to) {
        html += `<li><strong>去程：</strong>${escapeHtml(plan.transport.to.route)} · ${escapeHtml(plan.transport.to.duration)} · ¥${plan.transport.to.cost}/人</li>`
      }
      if (plan.transport.return) {
        html += `<li><strong>返程：</strong>${escapeHtml(plan.transport.return.route)} · ${escapeHtml(plan.transport.return.duration)} · ¥${plan.transport.return.cost}/人</li>`
      }
      html += '</ul>'
    }

    // 酒店推荐
    if (plan.hotels?.length) {
      html += '<h4 class="trip-h4">🏨 推荐住宿</h4><ul class="trip-ul">'
      plan.hotels.forEach(h => {
        const stars = '⭐'.repeat(h.stars || 0)
        html += `<li><strong>${escapeHtml(h.name)}</strong> ${stars} · ¥${h.price}/晚 — ${escapeHtml(h.reason || '')}</li>`
      })
      html += '</ul>'
    }

    // 每日行程
    if (plan.days?.length) {
      html += '<h4 class="trip-h4">📅 每日行程</h4>'
      plan.days.forEach(day => {
        html += `<p class="trip-day-title"><strong>Day ${day.day} · ${escapeHtml(day.title || '')}</strong></p>`
        if (day.activities?.length) {
          html += '<ul class="trip-ul">'
          day.activities.forEach(act => {
            html += `<li><span class="trip-time">${escapeHtml(act.time || '')}</span> <strong>${escapeHtml(act.name || '')}</strong>`
            if (act.cost) html += ` · ${escapeHtml(act.cost)}`
            html += `<br><span class="trip-desc">${escapeHtml(act.description || '')}</span></li>`
          })
          html += '</ul>'
        }
      })
    }

    // 预估费用
    if (plan.estimated_cost) {
      const c = plan.estimated_cost
      html += '<h4 class="trip-h4">💰 预估费用（每人）</h4>'
      html += '<div class="trip-cost-table">'
      if (c.transport) html += `<div class="trip-cost-row"><span>交通</span><span>¥${c.transport}</span></div>`
      if (c.hotel) html += `<div class="trip-cost-row"><span>住宿</span><span>¥${c.hotel}</span></div>`
      if (c.food) html += `<div class="trip-cost-row"><span>餐饮</span><span>¥${c.food}</span></div>`
      if (c.tickets) html += `<div class="trip-cost-row"><span>门票</span><span>¥${c.tickets}</span></div>`
      if (c.total) html += `<div class="trip-cost-row trip-cost-total"><span>合计</span><span>¥${c.total}</span></div>`
      html += '</div>'
    }

    // 出行贴士
    if (plan.tips?.length) {
      html += '<h4 class="trip-h4">📝 出行贴士</h4><ul class="trip-ul">'
      plan.tips.forEach(tip => {
        html += `<li>${escapeHtml(tip)}</li>`
      })
      html += '</ul>'
    }

    // ── Phase 2: Enrichment 富化数据 ──
    const enrich = plan.enrichment
    if (enrich) {
      // 天气
      if (enrich.weather?.length) {
        html += '<h4 class="trip-h4">🌤️ 沿途天气</h4><div class="trip-enrich-weather">'
        enrich.weather.forEach(w => {
          html += `<span class="enrich-weather-chip">${escapeHtml(w.city || '')} ${w.temperature || '—'}℃ ${escapeHtml(w.weather_desc || '')}</span>`
        })
        html += '</div>'
      }
      // 周边美食
      if (enrich.foods?.length) {
        html += '<h4 class="trip-h4">🍲 周边美食</h4><div class="trip-enrich-grid">'
        enrich.foods.slice(0, 6).forEach(f => {
          html += `<span class="enrich-chip food">🍲 ${escapeHtml(f.name)}<small>${f.distance_km != null ? f.distance_km.toFixed(1) + 'km' : ''}</small></span>`
        })
        html += '</div>'
      }
      // 周边非遗
      if (enrich.heritages?.length) {
        html += '<h4 class="trip-h4">🏛️ 周边非遗</h4><div class="trip-enrich-grid">'
        enrich.heritages.slice(0, 6).forEach(h => {
          html += `<span class="enrich-chip heritage">🏛️ ${escapeHtml(h.name)}<small>${h.distance_km != null ? h.distance_km.toFixed(1) + 'km' : ''}</small></span>`
        })
        html += '</div>'
      }
      // 周边酒店
      if (enrich.hotels?.length) {
        html += '<h4 class="trip-h4">🏨 附近酒店</h4><div class="trip-enrich-grid">'
        enrich.hotels.slice(0, 4).forEach(h => {
          const stars = '⭐'.repeat(h.stars || 0)
          html += `<span class="enrich-chip hotel">🏨 ${escapeHtml(h.name)} ${stars}<small>¥${h.price_min || '—'}/晚 · ${h.distance_km != null ? h.distance_km.toFixed(1) + 'km' : ''}</small></span>`
        })
        html += '</div>'
      }
      // 人流
      if (enrich.crowd?.length) {
        html += '<h4 class="trip-h4">👥 实时人流</h4><div class="trip-enrich-grid">'
        const levelEmoji = { '低': '🟢', '中': '🟡', '高': '🔴' }
        enrich.crowd.forEach(c => {
          html += `<span class="enrich-chip crowd">${levelEmoji[c.crowd_level] || '🔵'} ${escapeHtml(c.location_name || '')}<small>${c.crowd_level || '—'} · ${c.estimated_count || '—'}人</small></span>`
        })
        html += '</div>'
      }
    }
  })

  return html
}

function escapeHtml(str) {
  if (!str) return ''
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

async function handleSaveTrip(plan) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await tripApi.importPlan({
      title: plan.title || plan.theme || 'AI 行程方案',
      days: plan.days?.length || 3,
      crowd_type: plan._crowd_type || lastTripParams.value?.crowd_type || 'solo',
      preferences: plan._preferences || lastTripParams.value?.preferences || [],
      plan_content: {
        plans: [plan],
      },
    })
    ElMessage.success('行程已保存！可在个人中心查看')
  } catch {
    ElMessage.error('保存失败，请重试')
  }
}

async function handleSaveTripText(msg) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  // Try msg.tripPlans first (persisted in onDone), fall back to savedTripPlans
  const plans = msg.tripPlans?.length ? msg.tripPlans : savedTripPlans.value
  if (!plans || !plans.length) {
    ElMessage.info('没有可保存的行程数据，请重新规划')
    return
  }
  try {
    for (const plan of plans) {
      await tripApi.importPlan({
        title: plan.title || plan.theme || 'AI 行程方案',
        days: plan.days?.length || 3,
        crowd_type: plan._crowd_type || 'solo',
        preferences: plan._preferences || [],
        plan_content: { plans: [plan] },
      })
    }
    ElMessage.success(`${plans.length} 套方案已保存！可在个人中心查看`)
  } catch {
    ElMessage.error('保存失败，请重试')
  }
}

function handleCopyTripText(msg) {
  const tempDiv = document.createElement('div')
  tempDiv.innerHTML = msg.content || ''
  const plainText = tempDiv.textContent || tempDiv.innerText || ''
  navigator.clipboard.writeText(plainText).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.info('复制失败，请手动选择')
  })
}

async function handleRefreshTrip() {
  if (!lastTripParams.value) return
  chatStore.addMessage('user', '🔄 换一换')
  await sendMessage(lastTripParams.value.question || '重新规划行程')
}

async function handleFavorite(item) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await userApi.addFavorite({
      item_type: 'food',
      item_id: item.id || item.food_id,
    })
    ElMessage.success('已收藏')
  } catch {
    ElMessage.info('已收藏或收藏失败')
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-widget {
  position: fixed;
  right: 24px;
  bottom: 50px;
  z-index: var(--z-sticky, 200);
}

.chat-fab {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--brand-red);
  color: var(--text-inverse);
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-lg);
  transition: transform var(--duration-fast) var(--ease-spring),
              box-shadow var(--duration-fast);
}

.chat-fab:hover {
  transform: scale(1.08);
  box-shadow: var(--shadow-xl);
  background: var(--brand-red-hover);
}

.chat-panel {
  width: 420px;
  height: 600px;
  background: var(--bg-page);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── 拖拽手柄（位于红色 header 顶部居中）── */
.drag-handle {
  display: flex;
  justify-content: center;
  padding-bottom: 6px;
  cursor: grab;
  user-select: none;
  -webkit-user-select: none;
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-handle__bar {
  width: 40px;
  height: 4px;
  background: rgba(255, 255, 255, 0.55);
  border-radius: 999px;
  transition: background 0.2s;
}

.drag-handle:hover .drag-handle__bar {
  background: rgba(255, 255, 255, 0.85);
}

/* 拖拽时禁止选中 */
.chat-panel.is-dragging {
  user-select: none;
  -webkit-user-select: none;
}

.chat-panel__header {
  padding: 6px 16px 8px;
  background: linear-gradient(135deg, var(--brand-red) 0%, oklch(0.42 0.20 25) 100%);
  color: var(--text-inverse);
  display: flex;
  flex-direction: column;
}

.chat-panel__header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-panel__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.chat-panel__avatar {
  font-size: 20px;
}

.chat-panel__actions .el-button {
  color: var(--text-inverse);
}

.chat-panel__body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-welcome {
  text-align: center;
  padding: 8px 0 20px;
}

.chat-welcome__icon {
  font-size: 48px;
  margin-bottom: var(--space-md);
}

.chat-welcome__text {
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  line-height: 1.8;
  margin-bottom: var(--space-lg);
}

.chat-welcome__text p {
  margin: 0 0 var(--space-xs);
}

.chat-welcome__greeting {
  font-family: var(--font-display);
  font-size: var(--fs-xl);
  font-weight: var(--fw-bold);
  color: var(--brand-red);
  margin-bottom: var(--space-sm) !important;
}

.chat-welcome__services {
  font-size: var(--fs-sm);
  color: var(--text-tertiary);
  margin-top: var(--space-sm);
}

.chat-welcome__suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  justify-content: center;
}

.chat-message {
  display: flex;
}

.chat-message.is-user {
  justify-content: flex-end;
}

.chat-message__bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: var(--fs-sm);
  line-height: 1.6;
  word-break: break-word;
}

.chat-message.is-user .chat-message__bubble {
  background: var(--brand-red);
  color: var(--text-inverse);
  border-bottom-right-radius: 4px;
}

.chat-message.is-assistant .chat-message__bubble {
  background: var(--brand-amber-wash);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
  border: 1px solid oklch(0.58 0.18 80 / 0.12);
}

.chat-cursor {
  animation: blink 0.8s infinite;
  font-weight: bold;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ── 冲泡中 thinking — 三颗蒸汽圆点 ── */
.chat-thinking {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  color: var(--text-secondary);
  font-size: var(--fs-sm);
}

.chat-thinking__steam {
  display: flex;
  gap: 4px;
  align-items: flex-end;
}

.steam-dot {
  width: 5px;
  height: 5px;
  border-radius: var(--radius-full);
  background: var(--brand-amber);
  animation: steam-bubble 1.2s ease-in-out infinite;
}

.steam-dot:nth-child(2) { animation-delay: 0.2s; }
.steam-dot:nth-child(3) { animation-delay: 0.4s; }

.steam-dot:nth-child(1) { width: 4px; height: 4px; }
.steam-dot:nth-child(3) { width: 6px; height: 6px; }

@keyframes steam-bubble {
  0%, 100% { opacity: 0.3; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-4px); }
}

.chat-thinking__label {
  font-size: var(--fs-xs);
  color: var(--text-tertiary);
}

.chat-quick-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  padding: 0 4px;
}

.chat-error {
  padding: 0 4px;
}

/* 意图导航按钮 — 多意图，主次分明 */
.intent-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}
/* 主要意图按钮 — 红色渐变实心 */
.intent-nav .is-primary-intent {
  background: linear-gradient(135deg, var(--brand-red) 0%, oklch(0.50 0.22 25) 100%);
  border: none;
  color: #fff;
  font-weight: 600;
  font-size: var(--fs-xs);
  transition: transform 0.2s, box-shadow 0.2s;
}
.intent-nav .is-primary-intent:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px oklch(0.42 0.20 25 / 0.3);
}
/* 次要意图按钮 — 红色边框描边 */
.intent-nav .is-secondary-intent {
  background: transparent;
  border: 1.5px solid var(--brand-red);
  color: var(--brand-red);
  font-weight: 500;
  font-size: var(--fs-xs);
  transition: background 0.2s, transform 0.2s;
}
.intent-nav .is-secondary-intent:hover {
  background: oklch(0.42 0.20 25 / 0.06);
  transform: translateY(-1px);
}

.chat-panel__footer {
  padding: 12px 16px;
  border-top: 1px solid var(--border-light);
}

/* ── 行程文字排版样式 ── */
.chat-trip-text {
  max-width: 92% !important;
  padding: 14px 18px !important;
  line-height: 1.7;
}

.trip-text__content :deep(.trip-h3) {
  font-size: 15px;
  font-weight: 700;
  color: var(--brand-red);
  margin: 0 0 8px 0;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--brand-red);
}

.trip-text__content :deep(.trip-h4) {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  margin: 14px 0 6px 0;
}

.trip-text__content :deep(.trip-summary) {
  font-size: 13px;
  color: var(--muted);
  margin: 0 0 10px 0;
  line-height: 1.6;
}

.trip-text__content :deep(.trip-ul) {
  margin: 0 0 8px 0;
  padding-left: 18px;
  font-size: 12px;
  color: var(--ink);
  line-height: 1.8;
}

.trip-text__content :deep(.trip-ul li) {
  margin-bottom: 4px;
}

.trip-text__content :deep(.trip-day-title) {
  margin: 8px 0 4px 0;
  font-size: 13px;
  color: var(--ink);
}

.trip-text__content :deep(.trip-time) {
  display: inline-block;
  min-width: 40px;
  color: var(--muted);
  font-size: 11px;
}

.trip-text__content :deep(.trip-desc) {
  color: var(--muted);
  font-size: 11px;
}

.trip-text__content :deep(.trip-cost-table) {
  font-size: 12px;
  margin: 0 0 8px 0;
}

.trip-text__content :deep(.trip-cost-row) {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px dotted var(--border-light);
}

.trip-text__content :deep(.trip-cost-total) {
  font-weight: 700;
  color: var(--brand-red);
  border-bottom: none;
}

.trip-text__content :deep(.trip-divider) {
  border: none;
  border-top: 1px dashed var(--border-default);
  margin: 16px 0;
}

/* ── Phase 2: Enrichment 富化数据样式 ── */
.trip-text__content :deep(.trip-enrich-weather) {
  display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 8px;
}
.trip-text__content :deep(.enrich-weather-chip) {
  background: oklch(0.55 0.14 160 / 0.1);
  color: var(--brand-jade);
  padding: 2px 8px; border-radius: 10px; font-size: 11px;
}
.trip-text__content :deep(.trip-enrich-grid) {
  display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 8px;
}
.trip-text__content :deep(.enrich-chip) {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 10px; font-size: 11px;
}
.trip-text__content :deep(.enrich-chip small) {
  opacity: 0.7; font-size: 10px;
}
.trip-text__content :deep(.enrich-chip.food) {
  background: #FFF3E0; color: #E65100;
}
.trip-text__content :deep(.enrich-chip.heritage) {
  background: #FFEBEE; color: #C62828;
}
.trip-text__content :deep(.enrich-chip.hotel) {
  background: #E3F2FD; color: #1565C0;
}
.trip-text__content :deep(.enrich-chip.crowd) {
  background: #F3E5F5; color: #6A1B9A;
}

.trip-text__actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border-light);
}

@media (max-width: 767px) {
  .chat-panel {
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .drag-handle {
    display: none;
  }

  .chat-widget {
    right: 16px;
    bottom: 80px;
  }
}
</style>
