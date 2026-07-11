import api from './request'

export const adminApi = {
  // 仪表盘
  stats() { return api.get('/admin/stats') },
  recentActivity() { return api.get('/admin/recent-activity') },
  // 用户
  users(params) { return api.get('/admin/users', { params }) },
  userDetail(id) { return api.get(`/admin/users/${id}`) },
  updateUser(id, data) { return api.put(`/admin/users/${id}`, data) },
  // 美食
  createFood(formData) { return api.post('/admin/foods', formData) },
  updateFood(id, formData) { return api.put(`/admin/foods/${id}`, formData) },
  deleteFood(id) { return api.delete(`/admin/foods/${id}`) },
  // 非遗
  createHeritage(formData) { return api.post('/admin/heritages', formData) },
  updateHeritage(id, formData) { return api.put(`/admin/heritages/${id}`, formData) },
  deleteHeritage(id) { return api.delete(`/admin/heritages/${id}`) },
  // 节日
  createEvent(data) { return api.post('/admin/events', data) },
  updateEvent(id, data) { return api.put(`/admin/events/${id}`, data) },
  deleteEvent(id) { return api.delete(`/admin/events/${id}`) },
  // 社区
  getPosts(params) { return api.get('/admin/posts', { params }) },
  getPostDetail(id) { return api.get(`/admin/posts/${id}`) },
  deletePost(id) { return api.delete(`/admin/posts/${id}`) },
  deleteComment(id) { return api.delete(`/admin/comments/${id}`) },
  // 数据
  weatherLogs(params) { return api.get('/admin/weather-logs', { params }) },
  crowdLogs(params) { return api.get('/admin/crowd-logs', { params }) },
  refreshWeather() { return api.post('/admin/refresh-weather') },
  generateCrowd() { return api.post('/admin/generate-crowd') },
  // 设置
  getSettings() { return api.get('/admin/settings') },
  updateSettings(data) { return api.put('/admin/settings', data) },
}

export default adminApi
