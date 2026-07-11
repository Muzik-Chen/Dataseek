<template>
  <div class="messages-page">
    <div class="messages-container">
      <!-- 会话列表 -->
      <aside class="conv-sidebar">
        <div class="sidebar-header">
          <h2>💬 私信</h2>
        </div>
        <div class="conv-list">
          <div
            v-for="conv in conversations"
            :key="conv.user_id"
            :class="['conv-item', { active: activeConv === conv.user_id }]"
            @click="openConversation(conv)"
          >
            <el-badge :value="conv.unread_count" :hidden="!conv.unread_count">
              <el-avatar :size="44" :src="conv.user_avatar">
                {{ conv.user_nickname?.[0] || 'U' }}
              </el-avatar>
            </el-badge>
            <div class="conv-info">
              <strong>{{ conv.user_nickname || '用户' }}</strong>
              <p>{{ conv.last_message?.slice(0, 30) || '暂无消息' }}</p>
            </div>
          </div>
          <div v-if="!conversations.length" class="no-conv">
            <p>暂无私信</p>
          </div>
        </div>
      </aside>

      <!-- 聊天区 -->
      <main class="chat-area">
        <template v-if="activeConv">
          <div class="chat-header">
            <strong>{{ activeConvUser?.user_nickname || '用户' }}</strong>
          </div>
          <div class="message-list" ref="msgListRef">
            <div
              v-for="msg in currentMessages"
              :key="msg.id"
              :class="['msg', msg.sender_id === userId ? 'sent' : 'received']"
            >
              <div class="msg-bubble">
                {{ msg.content }}
              </div>
              <span class="msg-time">{{ msg.created_at?.slice(11, 16) }}</span>
            </div>
            <div v-if="!currentMessages.length" class="no-msg">
              <p>暂无消息，发送第一条吧</p>
            </div>
          </div>
          <div class="chat-input">
            <el-input
              v-model="inputText"
              placeholder="输入消息..."
              maxlength="5000"
              @keyup.enter="sendMsg"
            >
              <template #append>
                <el-button :disabled="!inputText.trim()" @click="sendMsg">发送</el-button>
              </template>
            </el-input>
          </div>
        </template>
        <div v-else class="no-chat">
          <el-icon :size="48" color="var(--muted)"><ChatDotSquare /></el-icon>
          <p>选择一个会话开始聊天</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { ChatDotSquare } from '@element-plus/icons-vue'
import { getConversations, getMessages, sendMessage } from '@/api'

import { useUserStore } from '@/stores/user'
const userStore = useUserStore()
const userId = computed(() => userStore.user?.id)
const conversations = ref([])
const activeConv = ref(null)
const activeConvUser = ref(null)
const currentMessages = ref([])
const inputText = ref('')
const msgListRef = ref(null)

async function fetchConversations() {
  try {
    const data = await getConversations({ page_size: 50 })
    conversations.value = data.items || []
  } catch { /* 静默失败 */ }
}

async function openConversation(conv) {
  activeConv.value = conv.user_id
  activeConvUser.value = conv
  try {
    const data = await getMessages(conv.user_id, { page_size: 100 })
    currentMessages.value = (data.items || []).reverse()
  } catch {
    currentMessages.value = []
  }
  await scrollToBottom()
}

async function sendMsg() {
  const text = inputText.value.trim()
  if (!text || !activeConv.value) return

  currentMessages.value.push({
    id: Date.now(),
    sender_id: userId,
    content: text,
    created_at: new Date().toISOString(),
  })
  inputText.value = ''

  try {
    await sendMessage({ receiver_id: activeConv.value, content: text })
  } catch { /* 静默失败 */ }

  await scrollToBottom()
}

async function scrollToBottom() {
  await nextTick()
  const el = msgListRef.value
  if (el) el.scrollTop = el.scrollHeight
}

onMounted(() => fetchConversations())
</script>

<style scoped>
.messages-page { height: calc(100vh - 64px - 80px); padding: 0; }

.messages-container {
  display: flex;
  height: 100%;
  max-width: 1000px;
  margin: 0 auto;
  border-left: 1px solid oklch(0 0 0 / 0.06);
  border-right: 1px solid oklch(0 0 0 / 0.06);
}

/* Sidebar */
.conv-sidebar {
  width: 300px;
  background: var(--surface);
  border-right: 1px solid oklch(0 0 0 / 0.06);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header { padding: var(--space-lg); border-bottom: 1px solid oklch(0 0 0 / 0.06); }
.sidebar-header h2 { font-size: var(--fs-base); color: var(--ink); margin: 0; }

.conv-list { flex: 1; overflow-y: auto; }

.conv-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  cursor: pointer;
  transition: background 0.2s;
}

.conv-item:hover, .conv-item.active { background: oklch(0.52 0.16 248 / 0.04); }

.conv-info { flex: 1; min-width: 0; }
.conv-info strong { display: block; font-size: var(--fs-sm); color: var(--ink); }
.conv-info p { color: var(--muted); font-size: var(--fs-xs); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin: 2px 0 0; }

.no-conv { text-align: center; padding: var(--space-2xl); color: var(--muted); font-size: var(--fs-sm); }

/* Chat */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg);
}

.chat-header {
  padding: var(--space-md) var(--space-xl);
  background: var(--surface);
  border-bottom: 1px solid oklch(0 0 0 / 0.06);
}

.chat-header strong { color: var(--ink); font-size: var(--fs-base); }

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.msg { display: flex; align-items: flex-end; gap: var(--space-xs); max-width: 75%; }
.msg.sent { align-self: flex-end; flex-direction: row-reverse; }
.msg.received { align-self: flex-start; }

.msg-bubble {
  padding: var(--space-sm) var(--space-md);
  border-radius: 14px;
  font-size: var(--fs-sm);
  line-height: 1.5;
  word-break: break-word;
}

.msg.sent .msg-bubble { background: var(--primary); color: #fff; border-bottom-right-radius: 4px; }
.msg.received .msg-bubble { background: var(--surface); color: var(--ink); border-bottom-left-radius: 4px; }

.msg-time { font-size: var(--fs-xs); color: var(--muted); }

.no-msg { text-align: center; color: var(--muted); padding: var(--space-3xl); }

.chat-input { padding: var(--space-md); background: var(--surface); border-top: 1px solid oklch(0 0 0 / 0.06); }

.no-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  gap: var(--space-md);
}

@media (max-width: 768px) {
  .conv-sidebar { width: 100%; }
  .chat-area { display: none; }
  .chat-area:has(.no-chat) { display: flex; }
}
</style>
