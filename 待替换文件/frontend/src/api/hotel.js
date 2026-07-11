import api from './request'

export const hotelApi = {
  list(params) { return api.get('/hotels', { params }) },
  detail(id) { return api.get(`/hotels/${id}`) },
}

export default hotelApi
