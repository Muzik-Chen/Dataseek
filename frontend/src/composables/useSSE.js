import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'

/**
 * 通用 SSE fetch 封装 — 读取流式响应并按事件类型分派回调。
 *
 * @param {string} url   请求 URL
 * @param {object} body  请求体（JSON）
 * @param {object} callbacks  事件回调映射 { onToken, onDone, onTripCard, ... }
 * @param {object} opts  可选配置 { signal, retry }
 * @returns {Promise<void>}
 */
export async function streamFetch(url, body, callbacks = {}, opts = {}) {
  const {
    onToken = () => {},
    onDone = () => {},
    onError = () => {},
    onTripCard = () => {},
    onFoodCard = () => {},
    onHeritageCard = () => {},
    onAsk = () => {},
    onThinking = () => {},
    onSources = () => {},
    onRouteWeather = () => {},
    onRouteFoods = () => {},
    onRouteHeritages = () => {},
    onRouteHotels = () => {},
    onRouteCrowd = () => {},
    onPlanFailed = () => {},
  } = callbacks

  const userStore = useUserStore()
  const { signal } = opts

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(userStore.token ? { Authorization: `Bearer ${userStore.token}` } : {}),
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        switch (data.type) {
          case 'token':
            onToken(data.content)
            break
          case 'thinking':
            onThinking(data.label)
            break
          case 'ask':
            onAsk(data.question, data.options, data.intent, data.intents)
            break
          case 'trip_card':
            onTripCard(data.plan)
            break
          case 'food_card':
            onFoodCard(data.items, data.summary)
            break
          case 'heritage_card':
            onHeritageCard(data.item)
            break
          case 'done':
            onDone(data.session_id || data)
            break
          case 'error':
            onError(data.message || '未知错误')
            break
          case 'sources':
            onSources(data.sources || [])
            break
          case 'plan_failed':
            onPlanFailed(data)
            break
          // ── Phase 2: Route Enrichment Events ──
          case 'route_weather':
            onRouteWeather(data)
            break
          case 'route_foods':
            onRouteFoods(data)
            break
          case 'route_heritages':
            onRouteHeritages(data)
            break
          case 'route_hotels':
            onRouteHotels(data)
            break
          case 'route_crowd':
            onRouteCrowd(data)
            break
        }
      } catch {
        // 忽略 JSON 解析错误
      }
    }
  }
}

export function useSSE() {
  const isStreaming = ref(false)
  const error = ref(null)
  let abortController = null

  async function streamChat(sessionId, message, callbacks = {}) {
    const {
      onToken = () => {},
      onDone = () => {},
      onError = () => {},
      onTripCard = () => {},
      onFoodCard = () => {},
      onHeritageCard = () => {},
      onAsk = () => {},
      onThinking = () => {},
      onSources = () => {},
    } = callbacks

    const userStore = useUserStore()
    const chatStore = useChatStore()
    abortController = new AbortController()
    isStreaming.value = true
    error.value = null

    const base = import.meta.env.VITE_API_BASE || '/api/v1'

    try {
      await streamFetch(`${base}/ai/chat`, { session_id: sessionId || null, message }, {
        ...callbacks,
        onDone(data) {
          chatStore.clearThinking()
          if (data?.intents?.length) {
            chatStore.setLastAssistantIntents(data.intents)
          } else if (data?.intent) {
            chatStore.setIntent(data.intent)
          }
          callbacks.onDone?.(data)
        },
      }, { signal: abortController.signal })
    } catch (e) {
      if (e.name !== 'AbortError') {
        error.value = e.message || '连接失败'
        callbacks.onError?.(error.value)
      }
    } finally {
      isStreaming.value = false
    }
  }

  /**
   * SSE 流式行程规划 — 用于 TripCreate 页面。
   *
   * @param {object}   params    { origin, days, crowd_type, interests, budget }
   * @param {object}   callbacks SSE 事件回调
   * @returns {Promise<void>}
   */
  async function streamTripPlan(params, callbacks = {}) {
    abortController = new AbortController()
    isStreaming.value = true
    error.value = null

    const base = import.meta.env.VITE_API_BASE || '/api/v1'
    const maxRetries = 2
    const backoffs = [1000, 3000]

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        await streamFetch(`${base}/trip/plan/stream`, params, callbacks, {
          signal: abortController.signal,
        })
        break // 成功则退出循环
      } catch (e) {
        if (e.name === 'AbortError') break
        if (attempt < maxRetries) {
          console.warn(`[useSSE] SSE retry ${attempt + 1}/${maxRetries} after ${backoffs[attempt]}ms`)
          // 通知回调重连中
          callbacks.onThinking?.(`连接中断，正在重连... (${attempt + 1}/${maxRetries})`)
          await new Promise(r => setTimeout(r, backoffs[attempt]))
          // 重置 abortController 以便重试
          abortController = new AbortController()
        } else {
          error.value = e.message || '连接失败'
          callbacks.onError?.(error.value)
        }
      }
    }
    isStreaming.value = false
  }

  function abort() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isStreaming.value = false
  }

  return { isStreaming, error, streamChat, streamTripPlan, streamFetch, abort }
}
