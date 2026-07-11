import api from './request'

export const tripApi = {
  create(data) { return api.post('/trip/plan', data, { timeout: 180000 }) },
<<<<<<< HEAD
  importPlan(data) { return api.post('/trip/plan/import', data) },
  saveDraft(data) { return api.post('/trip/plan/draft', data) },
  updatePlan(id, data) { return api.put(`/trip/plans/${id}`, data) },
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
  list(params) { return api.get('/trip/plans', { params }) },
  detail(id) { return api.get(`/trip/plans/${id}`) },
  delete(id) { return api.delete(`/trip/plans/${id}`) },
}

export default tripApi
