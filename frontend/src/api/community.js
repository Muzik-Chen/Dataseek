import api from './request'

export const communityApi = {
  posts(params) { return api.get('/community/posts', { params }) },
  postDetail(id) { return api.get(`/community/posts/${id}`) },
  create(formData) { return api.post('/community/posts', formData) },
  update(id, formData) { return api.put(`/community/posts/${id}`, formData) },
  delete(id) { return api.delete(`/community/posts/${id}`) },
  getComments(postId, params) { return api.get(`/community/posts/${postId}/comments`, { params }) },
  addComment(postId, data) { return api.post(`/community/posts/${postId}/comments`, data) },
  deleteComment(id) { return api.delete(`/community/comments/${id}`) },
  like(postId) { return api.post(`/community/posts/${postId}/like`) },
  unlike(postId) { return api.delete(`/community/posts/${postId}/like`) },
}

export default communityApi
