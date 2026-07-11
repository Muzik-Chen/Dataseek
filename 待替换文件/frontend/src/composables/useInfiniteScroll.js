import { ref } from 'vue'

export function useInfiniteScroll(loadMoreFn, threshold = 200) {
  const loading = ref(false)
  const finished = ref(false)
  const error = ref(null)

  async function onLoad() {
    if (loading.value || finished.value) return
    loading.value = true
    error.value = null
    try {
      await loadMoreFn()
    } catch (e) {
      error.value = e.message || '加载失败'
    } finally {
      loading.value = false
    }
  }

  function reset() {
    finished.value = false
    error.value = null
  }

  function markFinished() {
    finished.value = true
  }

  return { loading, finished, error, onLoad, reset, markFinished }
}
