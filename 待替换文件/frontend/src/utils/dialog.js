import { ElMessageBox } from 'element-plus'

export function confirmDelete(title = '确认删除？', message = '') {
  return ElMessageBox.confirm(message || '此操作不可恢复', title, {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
}

export function confirmLeave(message = '内容尚未保存，确定离开？') {
  return ElMessageBox.confirm(message, '提示', {
    confirmButtonText: '确定离开',
    cancelButtonText: '继续编辑',
    type: 'warning',
  })
}

export function confirmAction(message, title = '提示', options = {}) {
  return ElMessageBox.confirm(message, title, {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    ...options,
  })
}
