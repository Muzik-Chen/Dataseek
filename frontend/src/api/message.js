import api from './request'

export const messageApi = {
  conversations(params) { return api.get('/messages/conversations', { params }) },
  withUser(userId, params) { return api.get(`/messages/${userId}`, { params }) },
  send(data) { return api.post('/messages', data) },
  markRead(id) { return api.put(`/messages/${id}/read`) },
}

export default messageApi
