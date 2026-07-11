/**
 * useMusic.js — 首页背景音乐控制器（模块级单例）
 *
 * 使用方式：
 *   const { isPlaying, hasMusic, toggle, play, pause } = useMusic()
 *   onMounted(() => init())  // 在 Home.vue 中初始化并尝试自动播放
 *
 * - 后端不可达或网络故障 → hasMusic = false，toggle() 无操作
 * - 浏览器自动播放限制 → play() 失败时静默忽略，用户可手动点击按钮触发播放
 */
import { ref } from 'vue'
import { musicApi } from '@/api/music'

// ── 模块级单例状态 ──
let audio = null
const isPlaying = ref(false)
const hasMusic = ref(false)
let initAttempted = false

export function useMusic() {
  /**
   * 初始化：从后端获取 BGM URL 并创建 Audio 实例。
   * 仅首次调用生效，重复调用直接返回。
   */
  async function init() {
    if (initAttempted) return
    initAttempted = true

    try {
      const res = await musicApi.getBGM()
      const url = res?.url || res?.data?.url || res?.data?.music_url
      if (url) {
        audio = new Audio(url)
        audio.loop = true
        audio.volume = 0.4
        hasMusic.value = true

        // 尝试自动播放（浏览器策略可能阻止，静默失败）
        audio.play().then(() => {
          isPlaying.value = true
        }).catch(() => {
          // 自动播放被浏览器阻止，用户需手动点击按钮
          isPlaying.value = false
        })
      }
    } catch {
      // 后端不可达 / 网络故障 → 静默，按钮无反应
      hasMusic.value = false
    }
  }

  function play() {
    if (!audio || !hasMusic.value) return
    audio.play().then(() => {
      isPlaying.value = true
    }).catch(() => {})
  }

  function pause() {
    if (!audio) return
    audio.pause()
    isPlaying.value = false
  }

  function toggle() {
    if (!hasMusic.value) return // 后端不可达 → 无反应
    if (isPlaying.value) {
      pause()
    } else {
      play()
    }
  }

  return { isPlaying, hasMusic, init, play, pause, toggle }
}
