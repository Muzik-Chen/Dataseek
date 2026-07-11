import api from './request'

export const tripApi = {
  create(data) { return api.post('/trip/plan', data, { timeout: 180000 }) },
  list(params) { return api.get('/trip/plans', { params }) },
  detail(id) { return api.get(`/trip/plans/${id}`) },
  delete(id) { return api.delete(`/trip/plans/${id}`) },
}

export default tripApi
