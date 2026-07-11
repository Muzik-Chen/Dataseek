import api from './request'

export const userApi = {
  getProfile() { return api.get('/user/profile') },
  updateProfile(data) { return api.put('/user/profile', data) },
  getFavorites(params) { return api.get('/user/favorites', { params }) },
  addFavorite(data) { return api.post('/user/favorites', data) },
  removeFavorite(id) { return api.delete(`/user/favorites/${id}`) },
<<<<<<< HEAD
  checkFavorite(params) { return api.get('/user/favorites/check', { params }) },
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
}

export default userApi
