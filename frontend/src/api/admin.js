import api from './request'

/**
 * Admin API — 按 resource 命名空间组织。
 *
 * AdminCrud 通过 adminApi[config.resource].list/create/update/delete/detail 调用。
 * 命名空间方法签名统一：
 *   list(params)   → GET  /admin/{resource}
 *   detail(id)     → GET  /admin/{resource}/{id}
 *   create(data)   → POST /admin/{resource}
 *   update(id,data)→ PUT  /admin/{resource}/{id}
 *   delete(id)     → DELETE /admin/{resource}/{id}
 */
const adminApi = {

  // ── 仪表盘 ──────────────────────────────────────────
  stats() { return api.get('/admin/stats') },
  recentActivity() { return api.get('/admin/recent-activity') },

  // ── 设置 ────────────────────────────────────────────
  getSettings() { return api.get('/admin/settings') },
  updateSettings(data) { return api.put('/admin/settings', data) },

  // ── 美食 ────────────────────────────────────────────
  foods: {
    list(params) { return api.get('/admin/foods', { params }) },
    detail(id) { return api.get(`/admin/foods/${id}`) },
    create(data) { return api.post('/admin/foods', data) },
    update(id, data) { return api.put(`/admin/foods/${id}`, data) },
    delete(id) { return api.delete(`/admin/foods/${id}`) },
  },

  // ── 非遗 ────────────────────────────────────────────
  heritages: {
    list(params) { return api.get('/admin/heritages', { params }) },
    detail(id) { return api.get(`/admin/heritages/${id}`) },
    create(data) { return api.post('/admin/heritages', data) },
    update(id, data) { return api.put(`/admin/heritages/${id}`, data) },
    delete(id) { return api.delete(`/admin/heritages/${id}`) },
  },

  // ── 节日/民俗活动 ────────────────────────────────────
  events: {
    list(params) { return api.get('/admin/events', { params }) },
    detail(id) { return api.get(`/admin/events/${id}`) },
    create(data) { return api.post('/admin/events', data) },
    update(id, data) { return api.put(`/admin/events/${id}`, data) },
    delete(id) { return api.delete(`/admin/events/${id}`) },
  },

  // ── 用户（无 create，用户通过 /auth/register 注册）────
  users: {
    list(params) { return api.get('/admin/users', { params }) },
    detail(id) { return api.get(`/admin/users/${id}`) },
    update(id, data) { return api.put(`/admin/users/${id}`, data) },
    delete(id) { return api.delete(`/admin/users/${id}`) },
  },

  // ── 社区帖子（仅审核查看+删除，无 create/update）─────
  posts: {
    list(params) { return api.get('/admin/posts', { params }) },
    detail(id) { return api.get(`/admin/posts/${id}`) },
    delete(id) { return api.delete(`/admin/posts/${id}`) },
    deleteComment(id) { return api.delete(`/admin/comments/${id}`) },
  },

  // ── 数据管理 ─────────────────────────────────────────
  weatherLogs(params) { return api.get('/admin/weather-logs', { params }) },
  crowdLogs(params) { return api.get('/admin/crowd-logs', { params }) },
  refreshWeather() { return api.post('/admin/refresh-weather') },
  generateCrowd() { return api.post('/admin/generate-crowd') },
}

export { adminApi }
export default adminApi
