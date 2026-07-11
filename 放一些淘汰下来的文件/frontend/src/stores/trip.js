import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'trip_plan_state'

function _readStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function _writeStorage(state) {
  try {
    const toSave = {
      form: { ...state.form },
      streamPlans: state.streamPlans,
      streamNarration: state.streamNarration,
      activeResultPlanId: state.activeResultPlanId,
      draftId: state.draftId,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
  } catch {
    // 静默失败（存储满等情况）
  }
}

export const useTripStore = defineStore('trip', () => {
  // ── 从 localStorage 恢复 ──
  const saved = _readStorage()

  // 表单（带默认值）
  const form = ref({
    origin: saved?.form?.origin || '',
    days: saved?.form?.days || 3,
    budget: saved?.form?.budget || 'mid',
    crowd_type: saved?.form?.crowd_type || 'solo',
    preferences: saved?.form?.preferences || [],
    title: saved?.form?.title || '',
  })

  // 生成结果
  const streamPlans = ref(saved?.streamPlans || [])
  const streamNarration = ref(saved?.streamNarration || '')
  const activeResultPlanId = ref(saved?.activeResultPlanId || null)
  const draftId = ref(saved?.draftId || null)

  // 是否有已保存的方案（用于自动恢复）
  const hasSavedPlans = ref(saved?.streamPlans?.length > 0)

  // ── 自动保存 ──
  const saveToStorage = () => {
    _writeStorage({
      form: form.value,
      streamPlans: streamPlans.value,
      streamNarration: streamNarration.value,
      activeResultPlanId: activeResultPlanId.value,
      draftId: draftId.value,
    })
  }

  // 防抖 watch — 方案数组变更时批量保存
  let saveTimer = null
  watch(
    [form, streamPlans, streamNarration, activeResultPlanId, draftId],
    () => {
      if (saveTimer) clearTimeout(saveTimer)
      saveTimer = setTimeout(saveToStorage, 300)
    },
    { deep: true }
  )

  // ── 清除 ──
  function clearAll() {
    form.value = { origin: '', days: 3, budget: 'mid', crowd_type: 'solo', preferences: [], title: '' }
    streamPlans.value = []
    streamNarration.value = ''
    activeResultPlanId.value = null
    draftId.value = null
    hasSavedPlans.value = false
    try { localStorage.removeItem(STORAGE_KEY) } catch { /* ignore */ }
  }

  return {
    form,
    streamPlans,
    streamNarration,
    activeResultPlanId,
    draftId,
    hasSavedPlans,
    clearAll,
  }
})
