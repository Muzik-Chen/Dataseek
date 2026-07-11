import api from './request'

export const foodApi = {
  list(params) { return api.get('/foods', { params }) },
  detail(id) { return api.get(`/foods/${id}`) },
  categories() { return api.get('/foods/categories') },
  recommend(preference) { return api.post('/foods/recommend', { preference }) },
}

export default foodApi
