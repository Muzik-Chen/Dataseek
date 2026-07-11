/**
 * 高德地图 JSAPI 2.0 异步加载器
 *
 * 使用方式：
 *   import { loadAMap } from '@/utils/loadAmap'
 *   const AMap = await loadAMap()
 *
 * 安全密钥（2.0 必填）通过 _AMapSecurityConfig 注入。
 */
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || ''
const AMAP_VERSION = import.meta.env.VITE_AMAP_VERSION || '2.0'

let loadingPromise = null
let AMapInstance = null

export function loadAMap() {
  // 已加载完成
  if (AMapInstance) return Promise.resolve(AMapInstance)

  // 正在加载中，复用同一个 Promise
  if (loadingPromise) return loadingPromise

  loadingPromise = new Promise((resolve, reject) => {
    // 安全密钥（必须在 JSAPI 加载前设置）
    if (AMAP_KEY && AMAP_KEY !== 'your_amap_jsapi_key_here') {
      ;window._AMapSecurityConfig = {
        securityJsCode: '', // 如有安全密钥可填入
      }
    }

    // 如果已有 CDN 脚本且已加载
    if (window.AMap) {
      AMapInstance = window.AMap
      resolve(AMapInstance)
      return
    }

    // 动态注入 script
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=${AMAP_VERSION}&key=${AMAP_KEY}`
    script.async = true

    script.onload = () => {
      const AMap = window.AMap
      if (AMap) {
        AMapInstance = AMap
        resolve(AMap)
      } else {
        loadingPromise = null
        reject(new Error('AMap script loaded but window.AMap not found'))
      }
    }

    script.onerror = () => {
      loadingPromise = null
      reject(new Error('AMap JSAPI 加载失败，请检查网络或 Key 有效性'))
    }

    document.head.appendChild(script)
  })

  return loadingPromise
}

/**
 * 判断当前 Key 是否已配置（非占位符值）。
 */
export function isAMapConfigured() {
  return AMAP_KEY !== '' && AMAP_KEY !== 'your_amap_jsapi_key_here'
}
