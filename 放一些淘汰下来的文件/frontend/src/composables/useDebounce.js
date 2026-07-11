import { ref, watch } from 'vue'

/**
 * 响应式防抖 composable。
 * 对 ref 值做防抖处理，返回一个新的防抖 ref。
 */
export function useDebounce(value, delay = 300) {
  const debouncedValue = ref(value.value)

  let timeout = null
  watch(value, (newVal) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => {
      debouncedValue.value = newVal
    }, delay)
  })

  return debouncedValue
}
