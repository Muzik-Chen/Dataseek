import api from './request'

export const userApi = {
  getProfile() { return api.get('/user/profile') },
  updateProfile(data) { return api.put('/user/profile', data) },
  getFavorites(params) { return api.get('/user/favorites', { params }) },
  addFavorite(data) { return api.post('/user/favorites', data) },
  removeFavorite(id) { return api.delete(`/user/favorites/${id}`) },
}

export default userApi
