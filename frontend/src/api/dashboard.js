import api from './request'

export const dashboardApi = {
  weather(params) { return api.get('/dashboard/weather', { params }) },
  crowd(params) { return api.get('/dashboard/crowd', { params }) },
<<<<<<< HEAD
=======
  crowdHistory(params) { return api.get('/dashboard/crowd/history', { params }) },
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
  crowdGeo(params) { return api.get('/dashboard/crowd/geo', { params }) },
  weatherGeo(params) { return api.get('/dashboard/weather/geo', { params }) },
}

export default dashboardApi
