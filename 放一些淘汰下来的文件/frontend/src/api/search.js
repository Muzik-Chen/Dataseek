import api from './request'

export const searchApi = {
  // 前端并行搜索三个模块
  async search(keyword) {
    const [foods, heritages, events] = await Promise.all([
      api.get('/foods', { params: { keyword, page_size: 5 } }),
      api.get('/heritages', { params: { keyword, page_size: 3 } }),
      api.get('/events', { params: { keyword, page_size: 3 } }),
    ])
    return { foods, heritages, events }
  },
}

export default searchApi
