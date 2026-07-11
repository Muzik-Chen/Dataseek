import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')

  // 从 localStorage 恢复用户信息，避免刷新后丢失
  let savedUser = null
  try {
    const raw = localStorage.getItem('user')
    if (raw) savedUser = JSON.parse(raw)
  } catch { /* ignore parse error */ }
  const user = ref(savedUser)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setAuth(newToken, newUser) {
    token.value = newToken
    user.value = newUser
    localStorage.setItem('token', newToken)
    if (newUser) {
      localStorage.setItem('user', JSON.stringify(newUser))
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, isAdmin, setAuth, logout }
})
