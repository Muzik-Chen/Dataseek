import api from './request'

export const heritageApi = {
  list(params) { return api.get('/heritages', { params }) },
  detail(id) { return api.get(`/heritages/${id}`) },
  images(id) { return api.get(`/heritages/${id}/images`) },
}

export default heritageApi
