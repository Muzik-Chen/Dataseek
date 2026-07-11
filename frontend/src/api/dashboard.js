import api from './request'

export const dashboardApi = {
  weather(params) { return api.get('/dashboard/weather', { params }) },
  crowd(params) { return api.get('/dashboard/crowd', { params }) },
  crowdHistory(params) { return api.get('/dashboard/crowd/history', { params }) },
  crowdGeo(params) { return api.get('/dashboard/crowd/geo', { params }) },
  weatherGeo(params) { return api.get('/dashboard/weather/geo', { params }) },
}

export default dashboardApi
