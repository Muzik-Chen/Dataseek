/**
 * 纯函数防抖 — 延迟执行给定函数。
 * 用于非响应式场景（如搜索输入处理）。
 *
 * @param {Function} fn - 要防抖的函数
 * @param {number} delay - 延迟毫秒数，默认 300
 * @returns {Function} 防抖后的函数
 */
export function debounce(fn, delay = 300) {
  let timeout = null
  return function (...args) {
    clearTimeout(timeout)
    timeout = setTimeout(() => fn.apply(this, args), delay)
  }
}
