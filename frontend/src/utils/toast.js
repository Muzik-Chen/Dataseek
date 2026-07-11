import { ElMessage } from 'element-plus'

const DURATION = { fast: 1500, normal: 2000, slow: 3000 }

export const toast = {
  success(msg) {
    ElMessage({ type: 'success', message: msg, duration: DURATION.normal })
  },
  error(msg) {
    ElMessage({ type: 'error', message: msg, duration: DURATION.slow })
  },
  warning(msg) {
    ElMessage({ type: 'warning', message: msg, duration: DURATION.normal })
  },
  info(msg) {
    ElMessage({ type: 'info', message: msg, duration: DURATION.fast })
  },
}
