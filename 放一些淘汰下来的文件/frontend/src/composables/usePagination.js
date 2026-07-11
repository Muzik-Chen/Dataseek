import { ref } from 'vue'

export function usePagination(fetchFn, pageSize = 20) {
  const page = ref(1)
  const total = ref(0)
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function loadPage(p = page.value, size = pageSize) {
    loading.value = true
    error.value = null
    try {
      const result = await fetchFn({ page: p, page_size: size })
      items.value = result.items || []
      total.value = result.total || 0
      page.value = p
    } catch (e) {
      error.value = e.message || '加载失败'
    } finally {
      loading.value = false
    }
  }

  function goTo(p) {
    return loadPage(p)
  }

  function refresh() {
    return loadPage(page.value)
  }

  return { page, total, items, loading, error, loadPage, goTo, refresh }
}
