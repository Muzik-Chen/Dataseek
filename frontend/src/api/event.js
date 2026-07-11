import api from './request'

export const eventApi = {
  list(params) { return api.get('/events', { params }) },
  detail(id) { return api.get(`/events/${id}`) },
}

export default eventApi
