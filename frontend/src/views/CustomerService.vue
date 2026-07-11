<template>
  <div class="chat-page">
    <BackButton />
    <div class="chat-container">
      <!-- 侧边栏：会话列表 -->
      <aside class="chat-sidebar">
        <div class="sidebar-header">
          <h2>💬 智能客服</h2>
          <el-button :icon="Plus" circle size="small" @click="newChat" />
        </div>

        <div class="session-list">
          <div
            v-for="s in sessions"
            :key="s.session_id"
            :class="['session-item', { active: s.session_id === activeSession }]"
            @click="switchSession(s.session_id)"
          >
            <div class="session-info">
              <span class="session-title">{{ s.title }}</span>
              <span class="session-time">{{ s.updated_at?.slice(0, 10) }}</span>
            </div>
            <span class="session-count">{{ s.message_count }}</span>
          </div>
          <div v-if="!sessions.length" class="no-sessions">
            <p>暂无对话记录</p>
          </div>
        </div>
      </aside>

      <!-- 聊天主区域 -->
      <main class="chat-main">
        <!-- 欢迎状态 -->
        <div v-if="!activeSession && messages.length === 0" class="chat-welcome">
          <div class="welcome-icon">🍵</div>
          <h1>潮小文 · AI茶伴</h1>
          <p class="welcome-text">{{ welcomeText }}</p>
          <div class="suggestions">
            <button
              v-for="q in suggestions"
              :key="q"
              class="suggest-btn"
              @click="sendMessage(q)"
            >{{ q }}</button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="message-list" ref="msgListRef">
          <div
            v-for="(msg, i) in messages"
            :key="msg.id || i"
            :class="['message', msg.role]"
          >
            <div class="msg-avatar">
              {{ msg.role === 'user' ? '👤' : '🍵' }}
            </div>
            <div class="msg-body">
              <!-- 文本消息 -->
              <div class="msg-bubble" v-if="msg.type === 'text' || (!msg.type && msg.content)">
                <div class="msg-content">{{ msg.content }}</div>
                <span v-if="msg.isStreaming" class="typing-cursor">|</span>
              </div>

              <!-- 参考来源 -->
              <div v-if="msg.sources?.length" class="msg-sources">
                <span class="source-label">📚 参考：</span>
                <el-tag
                  v-for="(s, si) in msg.sources"
                  :key="si"
                  size="small"
                  round
                >{{ s.title || s.name }}</el-tag>
              </div>

              <!-- 行程方案卡片（结构化数据） -->
              <div v-if="msg.tripPlans?.length" class="trip-cards">
                <div
                  v-for="(plan, pi) in msg.tripPlans"
                  :key="pi"
                  :class="['trip-card', { 'trip-card-error': plan.error }]"
                >
                  <div class="trip-card-header">
                    <span :class="['plan-badge', 'plan-' + (plan.plan_id || 'A')]">
                      {{ plan.plan_id === 'A' ? '🍲' : plan.plan_id === 'B' ? '🏛️' : '🗺️' }}
                      方案{{ plan.plan_id }}
                    </span>
                    <strong>{{ plan.title || plan.theme }}</strong>
                  </div>
                  <div class="trip-card-summary">
                    {{ plan.error ? '⚠️ ' + plan.summary : plan.summary }}
                  </div>
                  <div v-if="!plan.error && plan.days" class="trip-card-days">
                    <div class="trip-day-chip" v-for="d in plan.days.slice(0, 3)" :key="d.day">
                      Day{{ d.day }} {{ d.title }}
                    </div>
                  </div>
                  <div v-if="!plan.error && plan.estimated_cost" class="trip-card-cost">
                    💰 预估人均：¥{{ plan.estimated_cost.total || '—' }}
                  </div>
                  <!-- Phase 2: Enrichment 摘要 -->
                  <div v-if="plan.enrichment" class="trip-card-enrich">
                    <span v-if="plan.enrichment.weather?.length" class="enrich-badge weather">🌤️ {{ plan.enrichment.weather.length }}处天气</span>
                    <span v-if="plan.enrichment.foods?.length" class="enrich-badge food">🍲 {{ plan.enrichment.foods.length }}家美食</span>
                    <span v-if="plan.enrichment.heritages?.length" class="enrich-badge heritage">🏛️ {{ plan.enrichment.heritages.length }}项非遗</span>
                    <span v-if="plan.enrichment.hotels?.length" class="enrich-badge hotel">🏨 {{ plan.enrichment.hotels.length }}家酒店</span>
                    <span v-if="plan.enrichment.crowd?.length" class="enrich-badge crowd">👥 {{ plan.enrichment.crowd.length }}处人流</span>
                  </div>
                </div>
              </div>

              <!-- 行程文字（来自 ChatWidget 的 trip_text 格式） -->
              <div v-if="msg.type === 'trip_text'" class="trip-text-content" v-html="msg.content"></div>

              <!-- 美食推荐卡片 -->
              <div v-if="msg.foodItems?.length" class="food-cards">
                <div v-if="msg.foodSummary" class="food-summary">{{ msg.foodSummary }}</div>
                <div class="food-card" v-for="(item, fi) in msg.foodItems" :key="fi">
                  <img
                    v-if="item.image_url"
                    :src="item.image_url"
                    :alt="item.name"
                    class="food-card-img"
                    @error="e => e.target.style.display = 'none'"
                  />
                  <div class="food-card-info">
                    <div class="food-card-name">
                      {{ item.name }}
                      <el-tag size="small" round v-if="item.score">{{ (item.score * 10).toFixed(0) }}分</el-tag>
                    </div>
                    <div class="food-card-reason">{{ item.reason }}</div>
                  </div>
                </div>
              </div>

              <!-- cardData 格式的美食卡片（来自 ChatWidget） -->
              <div v-if="msg.type === 'food_card' && msg.cardData?.items" class="food-cards">
                <div v-if="msg.cardData.summary" class="food-summary">{{ msg.cardData.summary }}</div>
                <div class="food-card" v-for="(item, fi) in msg.cardData.items" :key="fi">
                  <img
                    v-if="item.image_url"
                    :src="item.image_url"
                    :alt="item.name"
                    class="food-card-img"
                    @error="e => e.target.style.display = 'none'"
                  />
                  <div class="food-card-info">
                    <div class="food-card-name">
                      {{ item.name }}
                      <el-tag size="small" round v-if="item.score">{{ (item.score * 10).toFixed(0) }}分</el-tag>
                    </div>
                    <div class="food-card-reason">{{ item.reason }}</div>
                  </div>
                </div>
              </div>

              <!-- 快捷选项（追问） -->
              <div v-if="msg._quickOptions?.length && !msg.isStreaming" class="quick-options">
                <el-button
                  v-for="opt in msg._quickOptions"
                  :key="opt"
                  size="small"
                  round
                  @click="sendMessage(opt)"
                >{{ opt }}</el-button>
              </div>

              <!-- 意图导航按钮（多意图，主次分明） -->
              <div
                v-if="msg.intents?.length && !msg.isStreaming"
                class="intent-nav"
              >
                <el-button
                  v-for="(item, idx) in msg.intents.filter(i => INTENT_CONFIG[i.intent]).slice(0, 3)"
                  :key="item.intent"
                  :type="item.primary ? 'primary' : 'default'"
                  :class="{ 'is-primary-intent': item.primary, 'is-secondary-intent': !item.primary }"
                  round
                  @click="router.push(INTENT_CONFIG[item.intent].path)"
                >
                  {{ item.primary ? INTENT_CONFIG[item.intent].label : (INTENT_CONFIG[item.intent].secondaryLabel || INTENT_CONFIG[item.intent].label) }}
                </el-button>
              </div>
            </div>
          </div>

          <!-- 思考中 -->
          <div v-if="isThinking && !streamingMessageId" class="message assistant">
            <div class="msg-avatar">🍵</div>
            <div class="msg-body">
              <div class="msg-bubble thinking">
                <span>{{ thinkingLabel }}</span>
                <span class="dot" />
                <span class="dot" />
                <span class="dot" />
              </div>
            </div>
          </div>
        </div>

        <!-- 输入框 -->
        <div class="chat-input-bar">
          <el-input
            v-model="inputText"
            placeholder="输入您的问题..."
            :disabled="isThinking"
            maxlength="2000"
            show-word-limit
            @keyup.enter="sendMessage()"
          >
            <template #append>
              <el-button
                :icon="Promotion"
                :disabled="!inputText.trim() || isThinking"
                @click="sendMessage()"
              >发送</el-button>
            </template>
          </el-input>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Promotion } from '@element-plus/icons-vue'
import { useChatStore, INTENT_CONFIG } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { getChatSession, getChatHistory } from '@/api'
import BackButton from '@/components/common/BackButton.vue'

const chatStore = useChatStore()
const userStore = useUserStore()
const router = useRouter()

const activeSession = ref('')
const sessions = ref([])
const inputText = ref('')
const isThinking = ref(false)
const thinkingLabel = ref('思考中...')
const streamingMessageId = ref(null)
const msgListRef = ref(null)

const messages = computed(() => chatStore.messages)

const welcomeText = '您好！我是潮小文，你的潮汕文化AI茶伴 🍵 可以问我关于潮汕美食、非遗、旅游、民俗等任何问题～'
const suggestions = [
  '潮汕有什么必吃的美食？',
  '工夫茶有什么讲究？',
  '英歌舞是什么？',
  '推荐一条3天旅游路线',
  '潮汕有哪些非遗项目？',
]

// 同步 chatStore 的 sessionId 到本地 activeSession
watch(() => chatStore.sessionId, (sid) => {
  if (sid) activeSession.value = sid
})

// 页面加载时，如果 widget 已有聊天内容，自动同步
onMounted(async () => {
  try {
    const data = await getChatHistory({ page_size: 10 })
    sessions.value = data.items || []
  } catch { /* 静默 */ }

  // 如果从悬浮窗带来已有对话，同步 session
  if (chatStore.sessionId) {
    activeSession.value = chatStore.sessionId
  }
})

function newChat() {
  chatStore.startNewSession()
  activeSession.value = ''
  streamingMessageId.value = null
  isThinking.value = false
}

async function switchSession(sid) {
  activeSession.value = sid
  chatStore.setSessionId(sid)
  try {
    const data = await getChatSession(sid)
    // 将会话历史加载到 chatStore
    chatStore.messages = (data.items || []).map(item => ({
      id: item.id || Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      role: item.role || 'assistant',
      type: 'text',
      content: item.content || '',
      cardData: null,
      time: item.created_at || new Date().toISOString(),
      sources: item.sources || [],
      tripPlans: item.tripPlans || [],
      foodItems: [],
      foodSummary: '',
      isStreaming: false,
    }))
  } catch {
    chatStore.messages = []
  }
  streamingMessageId.value = null
  await scrollToBottom()
}

// ============ SSE AI 调用 ============
async function sendToAI(userContent) {
  const sessionId = activeSession.value || chatStore.sessionId || ''
  let abortController = null

  try {
    abortController = new AbortController()

    const base = import.meta.env.VITE_API_BASE || '/api/v1'
    const response = await fetch(`${base}/ai/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(userStore.token ? { Authorization: `Bearer ${userStore.token}` } : {}),
      },
      body: JSON.stringify({
        session_id: sessionId || null,
        message: userContent,
      }),
      signal: abortController.signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    // 创建占位 assistant 消息
    const msgId = Date.now() + '_' + Math.random().toString(36).slice(2, 8)
    const assistantMsg = {
      id: msgId,
      role: 'assistant',
      type: 'text',
      content: '',
      cardData: null,
      time: new Date().toISOString(),
      sources: [],
      tripPlans: [],
      foodItems: [],
      foodSummary: '',
      isStreaming: true,
      enrichment: null,  // Phase 2: enrichment data by plan_id
    }
    chatStore.messages.push(assistantMsg)
    streamingMessageId.value = msgId
    isThinking.value = true
    thinkingLabel.value = '思考中...'

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i]
        if (!line.startsWith('data: ')) continue

        try {
          const data = JSON.parse(line.slice(6))

          switch (data.type) {
            case 'thinking':
              thinkingLabel.value = data.label || '思考中...'
              break

            case 'token':
              chatStore.updateMessage(msgId, {
                content: (assistantMsg.content || '') + data.content,
              })
              assistantMsg.content += data.content
              await scrollToBottom()
              break

            case 'sources':
              chatStore.updateMessage(msgId, {
                sources: data.sources || [],
              })
              break

            case 'trip_card':
              if (data.plan) {
                assistantMsg.tripPlans.push(data.plan)
                chatStore.updateMessage(msgId, {
                  tripPlans: [...assistantMsg.tripPlans],
                })
                await scrollToBottom()
              }
              break

            case 'food_card':
              chatStore.updateMessage(msgId, {
                foodItems: data.items || [],
                foodSummary: data.summary || '',
              })
              await scrollToBottom()
              break

            case 'heritage_card':
              // 将 heritage 数据也放入消息中
              if (data.item) {
                const name = data.item.name || ''
                const desc = data.item.description || ''
                const extraContent = assistantMsg.content
                  ? assistantMsg.content + `\n\n🎭 **${name}**\n${desc}`
                  : `🎭 **${name}**\n${desc}`
                chatStore.updateMessage(msgId, { content: extraContent })
                assistantMsg.content = extraContent
              }
              break

            // ── Phase 2: Route Enrichment Events ──
            case 'route_weather':
            case 'route_foods':
            case 'route_heritages':
            case 'route_hotels':
            case 'route_crowd': {
              const planId = data.plan_id
              const enrichType = data.type  // e.g. 'route_weather'
              const enrichData = data  // full event payload
              // Inject into matching trip plan
              if (planId && assistantMsg.tripPlans.length) {
                const plan = assistantMsg.tripPlans.find(p => p.plan_id === planId)
                if (plan) {
                  if (!plan.enrichment) plan.enrichment = {}
                  // Extract the data key (weather / foods / heritages / hotels / crowd)
                  const dataKey = enrichType.replace('route_', '')
                  plan.enrichment[dataKey] = enrichData[dataKey] || enrichData[dataKey + 's'] || enrichData
                }
              }
              // Also store in the store
              chatStore.updateMessageEnrichment(msgId, planId, enrichType, enrichData)
              break
            }

            case 'ask':
              assistantMsg.content = data.question || assistantMsg.content
              assistantMsg._quickOptions = data.options || []
              if (data.intents?.length) {
                assistantMsg.intents = data.intents
                chatStore.setIntent(data.intent || (data.intents.find(i => i.primary) || data.intents[0]).intent)
              } else if (data.intent) {
                assistantMsg.intent = data.intent
                assistantMsg.intents = [{ intent: data.intent, confidence: 1.0, primary: true }]
                chatStore.setIntent(data.intent)
              }
              chatStore.updateMessage(msgId, {
                content: assistantMsg.content,
                _quickOptions: assistantMsg._quickOptions,
                intents: assistantMsg.intents || [],
                intent: assistantMsg.intent || null,
              })
              break

            case 'error':
              assistantMsg.content = (assistantMsg.content || '') + `\n\n❌ ${data.message || '服务异常，请稍后重试'}`
              chatStore.updateMessage(msgId, { content: assistantMsg.content })
              break

            case 'done':
              if (data.session_id) {
                activeSession.value = data.session_id
                chatStore.setSessionId(data.session_id)
              }
              if (data.intents?.length) {
                chatStore.setMessageIntents(msgId, data.intents)
              } else if (data.intent) {
                chatStore.setMessageIntent(msgId, data.intent)
              }
              break
          }
        } catch {
          // JSON 解析失败
        }
      }
    }

    // 流结束
    assistantMsg.isStreaming = false
    chatStore.updateMessage(msgId, { isStreaming: false })
    streamingMessageId.value = null

    // 确保意图引导文字已附加（ask 事件可能已设置 intent 但 done 未触发）
    if (assistantMsg.intents?.length) {
      chatStore.setMessageIntents(msgId, assistantMsg.intents)
    } else if (assistantMsg.intent) {
      chatStore.setMessageIntent(msgId, assistantMsg.intent)
    }

    // 如果 AI 完全没回复，用本地知识库兜底
    if (!assistantMsg.content && !assistantMsg.tripPlans.length && !assistantMsg.foodItems.length) {
      const idx = chatStore.messages.findIndex(m => m.id === msgId)
      if (idx >= 0) chatStore.messages.splice(idx, 1)
      const local = localReply(userContent)
      chatStore.addMessage('assistant', local.answer)
    }

  } catch (err) {
    console.error('[AI Chat] SSE fetch failed:', err)
    if (streamingMessageId.value) {
      const idx = chatStore.messages.findIndex(m => m.id === streamingMessageId.value)
      if (idx >= 0) chatStore.messages.splice(idx, 1)
      streamingMessageId.value = null
    }
    const local = localReply(userContent)
    chatStore.addMessage('assistant', local.answer)
  } finally {
    isThinking.value = false
    thinkingLabel.value = '思考中...'
    await scrollToBottom()
  }
}

// ============ 发送消息入口 ============
async function sendMessage(text) {
  const content = (text || inputText.value).trim()
  if (!content || isThinking.value) return

  chatStore.addMessage('user', content)
  inputText.value = ''
  await scrollToBottom()

  await sendToAI(content)

  if (!activeSession.value && chatStore.sessionId) {
    activeSession.value = chatStore.sessionId
  }
}

// ============ 本地知识库（降级方案） ============
function localReply(query) {
  const kb = {
    '牛肉火锅': { answer: '潮汕牛肉火锅以新鲜为灵魂，牛肉从屠宰到上桌不超过4小时。必点部位：吊龙（嫩滑）、匙柄（弹牙）、胸口朥（爽脆）。蘸沙茶酱是灵魂。热门店铺：汕头八合里海记、福合埕。', sources: [{ title: '牛肉火锅' }] },
    '工夫茶': { answer: '潮汕工夫茶是中国茶道的活化石，讲究二十一式冲泡技法。核心要领：沸水热罐、高冲低斟、关公巡城（均匀分茶）、韩信点兵（点滴不漏）。常用茶叶：凤凰单丛。体验地点：潮州古城。', sources: [{ title: '工夫茶' }] },
    '英歌舞': { answer: '英歌舞是国家级非遗，融合武术、舞蹈、戏曲。表演者面绘梁山好汉脸谱，手持英歌槌，随锣鼓节奏变换阵型。最盛大的表演在春节至元宵期间，汕头潮阳区是主要传承地。', sources: [{ title: '英歌舞' }] },
    '肠粉': { answer: '潮汕肠粉皮薄滑嫩，馅料丰富（牛肉、猪肉、虾仁、鸡蛋等），淋秘制卤汁，撒菜脯粒。推荐：汕头小公园附近的老牌肠粉店。', sources: [{ title: '肠粉' }] },
    '广济桥': { answer: '广济桥（湘子桥）位于潮州古城，是中国四大古桥之一，集梁桥、浮桥、拱桥于一体，十八梭船廿四洲是其独特景观。门票20元。', sources: [{ title: '广济桥' }] },
    '南澳岛': { answer: '南澳岛是广东唯一的海岛县，拥有青澳湾（广东最美海湾）、总兵府、宋井等景点。推荐游玩1-3天，海鲜丰富新鲜。从汕头市区约1.5小时车程。', sources: [{ title: '南澳岛' }] },
    '旅游': { answer: '潮汕旅游核心：潮州古城（广济桥+牌坊街）+汕头南澳岛+小公园+揭阳学宫。建议3-5天，最佳季节10月-次年4月。美食是重头戏！', sources: [{ title: '潮汕旅游' }] },
    '美食': { answer: '潮汕必尝美食：牛肉火锅、肠粉、粿条汤、蚝烙、卤鹅、鱼饭、鸭母捻、甜汤。热门美食区：汕头小公园、潮州牌坊街。', sources: [{ title: '潮汕美食' }] },
    '非遗': { answer: '潮汕拥有丰富的非遗项目：英歌舞（国家级）、潮剧（国家级）、工夫茶（国家级）、嵌瓷（国家级）、潮绣（国家级）、木雕（国家级）等。', sources: [{ title: '非遗' }] },
    '节日': { answer: '潮汕重要民俗节日：春节营老爷（正月初一至十五）、元宵花灯、清明祭祖、端午赛龙舟、中秋拜月娘、冬至吃冬节丸。', sources: [{ title: '民俗节日' }] },
  }

  for (const [keyword, entry] of Object.entries(kb)) {
    if (query.includes(keyword)) return entry
  }

  return {
    answer: `关于「${query.slice(0, 30)}」，我还在学习中 📚\n\n您可以尝试问我：\n• 潮汕有什么好吃的？\n• 工夫茶怎么泡？\n• 推荐旅游路线\n• 英歌舞是什么？`,
    sources: [],
  }
}

async function scrollToBottom() {
  await nextTick()
  const el = msgListRef.value
  if (el) el.scrollTop = el.scrollHeight
}
</script>

<style scoped>
.chat-page { height: calc(100vh - 64px - 80px); padding: 0; }
.chat-container { display: flex; height: 100%; max-width: 1100px; margin: 0 auto; }

/* Sidebar */
.chat-sidebar {
  width: 260px;
  background: var(--surface);
  border-right: 1px solid oklch(0 0 0 / 0.06);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  border-bottom: 1px solid oklch(0 0 0 / 0.06);
}

.sidebar-header h2 { font-size: var(--fs-base); color: var(--ink); margin: 0; }

.session-list { flex: 1; overflow-y: auto; padding: var(--space-sm); }

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.session-item:hover, .session-item.active { background: oklch(0.52 0.16 248 / 0.06); }

.session-info { flex: 1; min-width: 0; }
.session-title { display: block; font-size: var(--fs-sm); color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-time { font-size: var(--fs-xs); color: var(--muted); }
.session-count { background: var(--brand-red); color: #fff; font-size: var(--fs-xs); padding: 2px 8px; border-radius: 10px; }

.no-sessions { text-align: center; color: var(--muted); padding: var(--space-2xl); font-size: var(--fs-sm); }

/* Main chat */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl);
  text-align: center;
}

.welcome-icon { font-size: 64px; margin-bottom: var(--space-md); }
.chat-welcome h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-sm); }
.welcome-text { color: var(--muted); max-width: 420px; line-height: 1.6; margin: 0 0 var(--space-xl); }

.suggestions { display: flex; flex-wrap: wrap; gap: var(--space-sm); justify-content: center; max-width: 480px; }
.suggest-btn {
  padding: var(--space-sm) var(--space-lg);
  border: 1px solid oklch(0 0 0 / 0.1);
  border-radius: 20px;
  background: var(--bg);
  color: var(--ink);
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: all 0.2s;
}
.suggest-btn:hover { border-color: var(--primary); color: var(--primary); }

/* Messages */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.message { display: flex; gap: var(--space-sm); max-width: 85%; }
.message.user { align-self: flex-end; flex-direction: row-reverse; }
.message.assistant { align-self: flex-start; }

.msg-avatar {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%; background: var(--surface);
  font-size: 18px; flex-shrink: 0;
}

.msg-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  min-width: 0;
}

.msg-bubble {
  padding: var(--space-md) var(--space-lg);
  border-radius: 16px;
  line-height: 1.7;
  font-size: var(--fs-sm);
}

.message.user .msg-bubble { background: var(--primary); color: #fff; border-bottom-right-radius: 4px; }
.message.assistant .msg-bubble { background: var(--surface); color: var(--ink); border-bottom-left-radius: 4px; box-shadow: 0 1px 4px oklch(0 0 0 / 0.04); }

.msg-content { white-space: pre-wrap; word-break: break-word; }

/* 打字机光标 */
.typing-cursor {
  display: inline-block;
  animation: blink 1s step-end infinite;
  color: var(--primary);
  font-weight: 700;
}
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.msg-sources { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.source-label { font-size: var(--fs-xs); color: var(--muted); }

/* 思考动画 */
.thinking { display: flex; align-items: center; gap: 6px; padding: var(--space-md) var(--space-xl); color: var(--muted); font-size: var(--fs-sm); }
.dot { width: 6px; height: 6px; background: var(--muted); border-radius: 50%; animation: bounce 1.4s infinite both; }
.dot:nth-child(2) { animation-delay: 0.16s; }
.dot:nth-child(3) { animation-delay: 0.32s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 快捷选项 */
.quick-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  padding-top: var(--space-xs);
}

/* Trip text (from ChatWidget) */
.trip-text-content {
  font-size: var(--fs-sm);
  line-height: 1.7;
  color: var(--ink);
}

/* ====== 行程卡片 ====== */
.trip-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-width: 520px;
}

.trip-card {
  background: var(--surface);
  border: 1px solid oklch(0 0 0 / 0.08);
  border-radius: 12px;
  padding: var(--space-md) var(--space-lg);
  box-shadow: 0 1px 6px oklch(0 0 0 / 0.03);
  transition: border-color 0.2s;
}

.trip-card:hover { border-color: var(--primary); }

.trip-card-error {
  border-color: oklch(0.55 0.18 28 / 0.3);
  background: oklch(0.55 0.18 28 / 0.04);
}

.trip-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.plan-badge {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: var(--fs-xs);
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
}

.plan-A { background: oklch(0.55 0.18 28 / 0.85); }
.plan-B { background: oklch(0.52 0.16 248 / 0.85); }
.plan-C { background: oklch(0.45 0.15 160 / 0.85); }

.trip-card-header strong { font-size: var(--fs-sm); color: var(--ink); }

.trip-card-summary {
  font-size: var(--fs-sm);
  color: var(--muted);
  margin-bottom: var(--space-sm);
  line-height: 1.5;
}

.trip-card-days {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: var(--space-sm);
}

.trip-day-chip {
  padding: 2px 8px;
  background: oklch(0 0 0 / 0.04);
  border-radius: 6px;
  font-size: var(--fs-xs);
  color: var(--muted);
}

.trip-card-cost {
  font-size: var(--fs-sm);
  color: var(--primary);
  font-weight: 600;
}

/* ── Phase 2: Enrichment Badges ── */
.trip-card-enrich {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.enrich-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}

.enrich-badge.weather { background: oklch(0.55 0.14 160 / 0.1); color: #276749; }
.enrich-badge.food { background: #FFF3E0; color: #E65100; }
.enrich-badge.heritage { background: #FFEBEE; color: #C62828; }
.enrich-badge.hotel { background: #E3F2FD; color: #1565C0; }
.enrich-badge.crowd { background: #F3E5F5; color: #6A1B9A; }

/* ====== 美食卡片 ====== */
.food-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-width: 480px;
}

.food-summary {
  font-size: var(--fs-sm);
  color: var(--muted);
  font-style: italic;
  padding: var(--space-xs) 0;
}

.food-card {
  display: flex;
  gap: var(--space-md);
  background: var(--surface);
  border: 1px solid oklch(0 0 0 / 0.08);
  border-radius: 12px;
  padding: var(--space-md);
  box-shadow: 0 1px 6px oklch(0 0 0 / 0.03);
}

.food-card-img {
  width: 72px;
  height: 72px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
}

.food-card-info { flex: 1; min-width: 0; }

.food-card-name {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 4px;
}

.food-card-reason {
  font-size: var(--fs-xs);
  color: var(--muted);
  line-height: 1.4;
}

/* Input */
.chat-input-bar { padding: var(--space-md) var(--space-lg); border-top: 1px solid oklch(0 0 0 / 0.06); background: var(--bg); }

/* 意图导航按钮 — 多意图，主次分明 */
.intent-nav {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  padding-top: var(--space-xs);
}
/* 主要意图按钮 — 红色渐变实心 */
.intent-nav .is-primary-intent {
  background: linear-gradient(135deg, var(--brand-red) 0%, oklch(0.50 0.22 25) 100%);
  border: none;
  color: #fff;
  font-weight: 600;
  font-size: var(--fs-sm);
  padding: 10px 24px;
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
  font-size: var(--fs-sm);
  padding: 9px 20px;
  transition: background 0.2s, transform 0.2s;
}
.intent-nav .is-secondary-intent:hover {
  background: oklch(0.42 0.20 25 / 0.06);
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .chat-sidebar { display: none; }
  .message { max-width: 92%; }
  .trip-cards, .food-cards { max-width: 100%; }
}
</style>
