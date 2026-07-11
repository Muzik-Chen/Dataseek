import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'

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

    try {
      const base = import.meta.env.VITE_API_BASE || '/api/v1'
      const response = await fetch(`${base}/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(userStore.token ? { Authorization: `Bearer ${userStore.token}` } : {}),
        },
        body: JSON.stringify({ session_id: sessionId || null, message }),
        signal: abortController.signal,
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
                chatStore.clearThinking()
                if (data.intents?.length) {
                  chatStore.setLastAssistantIntents(data.intents)
                } else if (data.intent) {
                  chatStore.setIntent(data.intent)
                }
                onDone(data.session_id)
                break
              case 'error':
                onError(data.message || '未知错误')
                break
              case 'sources':
                onSources(data.sources || [])
                break
            }
          } catch {
            // 忽略 JSON 解析错误
          }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        error.value = e.message || '连接失败'
        onError(error.value)
      }
    } finally {
      isStreaming.value = false
    }
  }

  function abort() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isStreaming.value = false
  }

  return { isStreaming, error, streamChat, abort }
}
