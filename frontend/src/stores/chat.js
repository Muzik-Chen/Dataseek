import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 意图 → 路由映射配置
export const INTENT_CONFIG = {
  food:       { path: '/foods',        label: '美食一览 >>>',   secondaryLabel: '美食',     guideText: '点击下方按钮了解更多潮汕美食~~' },
  heritage:   { path: '/heritages',    label: '非遗文化 >>>',   secondaryLabel: '非遗文化', guideText: '点击下方按钮探索潮汕非遗文化~~' },
  festival:   { path: '/festival',     label: '民俗活动 >>>',   secondaryLabel: '民俗活动', guideText: '点击下方按钮了解潮汕民俗活动~~' },
  trip:       { path: '/trip/create',  label: '行程规划 >>>',   secondaryLabel: '行程规划', guideText: '点击下方按钮定制你的潮汕之旅~~' },
  community:  { path: '/community',    label: '社区交流 >>>',   secondaryLabel: '社区交流', guideText: '点击下方按钮加入潮汕文化社区~~' },
  dashboard:  { path: '/dashboard',    label: '数据大屏 >>>',   secondaryLabel: '数据大屏', guideText: '点击下方按钮查看潮汕文旅数据~~' },
  home:       { path: '/',             label: '回到首页 >>>',   secondaryLabel: '回到首页', guideText: '点击下方按钮回到首页探索更多~~' },
}

export const useChatStore = defineStore('chat', () => {
  // ===== State =====
  const messages = ref([])
  const sessionId = ref(localStorage.getItem('chat_session_id') || '')
  const isOpen = ref(false)
  const thinkingLabel = ref('')
  const currentIntent = ref(null)

  // ===== Getters =====
  const lastMessage = computed(() => messages.value[messages.value.length - 1])
  const hasMessages = computed(() => messages.value.length > 0)

  // ===== Helpers =====
  function makeMsg(role, type, content, cardData, extra = {}) {
    // 标准化 intents：兼容旧的单个 intent 和新的数组格式
    let intents = extra.intents || []
    if (!intents.length && extra.intent) {
      intents = [{ intent: extra.intent, confidence: 1.0, primary: true }]
    }
    return {
      id: Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      role,
      type: type || 'text',
      content: content || null,
      cardData: cardData || null,
      time: new Date().toISOString(),
      sources: extra.sources || [],
      tripPlans: extra.tripPlans || [],
      foodItems: extra.foodItems || [],
      foodSummary: extra.foodSummary || '',
      isStreaming: extra.isStreaming || false,
      intent: intents.length > 0 ? (intents.find(i => i.primary) || intents[0]).intent : null,
      intents,
    }
  }

  // ===== Actions =====
  function addMessage(role, content, type) {
    messages.value.push(makeMsg(role, type || 'text', content))
  }

  function addCardMessage(type, cardData) {
    messages.value.push(makeMsg('assistant', type, null, cardData))
  }

  function appendToken(token) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant' && last.type === 'text') {
      last.content += token
    } else {
      addMessage('assistant', token)
    }
  }

  function setSessionId(id) {
    sessionId.value = id
    localStorage.setItem('chat_session_id', id)
  }

  function setThinking(label) {
    thinkingLabel.value = label
  }

  function clearThinking() {
    thinkingLabel.value = ''
  }

  function updateMessage(msgId, updates) {
    const idx = messages.value.findIndex(m => m.id === msgId)
    if (idx >= 0) {
      messages.value[idx] = { ...messages.value[idx], ...updates }
    }
  }

  function setIntent(intent) {
    currentIntent.value = intent
  }

  /**
   * 设置消息的多意图列表（新方法）。
   * @param {string} msgId - 消息 ID
   * @param {Array} intents - [{intent, confidence, primary}, ...]
   */
  function setMessageIntents(msgId, intents) {
    if (!intents || !intents.length) return
    const idx = messages.value.findIndex(m => m.id === msgId)
    if (idx < 0) return

    const msg = messages.value[idx]
    const primary = intents.find(i => i.primary) || intents[0]
    const config = INTENT_CONFIG[primary.intent]

    // 附加 primary 引导文字（幂等）
    let content = msg.content || ''
    if (config && !content.includes(config.guideText)) {
      content = content + '\n\n' + config.guideText
    }

    messages.value[idx] = {
      ...msg,
      intent: primary.intent,
      intents,
      content,
    }
    currentIntent.value = primary.intent
  }

  /**
   * 设置消息意图（兼容旧接口，内部转为 intents 数组）。
   */
  function setMessageIntent(msgId, intent) {
    if (!intent || !INTENT_CONFIG[intent]) return
    setMessageIntents(msgId, [{ intent, confidence: 1.0, primary: true }])
  }

  /**
   * 为最后一条 assistant 消息设置多意图（新方法）。
   */
  function setLastAssistantIntents(intents) {
    if (!intents || !intents.length) return
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i].role === 'assistant') {
        setMessageIntents(messages.value[i].id, intents)
        return
      }
    }
  }

  /**
   * 为最后一条 assistant 消息设置意图（兼容旧接口）。
   */
  function setLastAssistantIntent(intent) {
    if (!INTENT_CONFIG[intent]) return
    setLastAssistantIntents([{ intent, confidence: 1.0, primary: true }])
  }

  function startNewSession() {
    messages.value = []
    sessionId.value = ''
    thinkingLabel.value = ''
    currentIntent.value = null
    localStorage.removeItem('chat_session_id')
  }

  function toggle() {
    isOpen.value = !isOpen.value
  }

  function open() {
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
  }

  return {
    messages,
    sessionId,
    isOpen,
    thinkingLabel,
    currentIntent,
    lastMessage,
    hasMessages,
    makeMsg,
    addMessage,
    addCardMessage,
    appendToken,
    setSessionId,
    setThinking,
    clearThinking,
    updateMessage,
    setIntent,
    setMessageIntent,
    setMessageIntents,
    setLastAssistantIntent,
    setLastAssistantIntents,
    startNewSession,
    toggle,
    open,
    close,
  }
})
