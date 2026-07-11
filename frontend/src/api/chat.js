import api from './request'
import { useUserStore } from '@/stores/user'

export const chatApi = {
  // SSE 流式对话 — 不走 Axios，用原生 fetch
  async sendMessage(sessionId, message, { onToken, onDone, onSources, onError }) {
    const userStore = useUserStore()
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE || '/api/v1'}/chat/send`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(userStore.token ? { Authorization: `Bearer ${userStore.token}` } : {}),
          },
          body: JSON.stringify({ session_id: sessionId, message }),
        }
      )
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'token') onToken?.(data.content)
            else if (data.type === 'done') onDone?.(data.session_id)
            else if (data.type === 'sources') onSources?.(data.sources)
          } catch { /* 解析失败跳过 */ }
        }
      }
    } catch (err) {
      onError?.(err)
    }
  },

  history() { return api.get('/chat/history') },
  session(sessionId) { return api.get(`/chat/history/${sessionId}`) },
}

export default chatApi
