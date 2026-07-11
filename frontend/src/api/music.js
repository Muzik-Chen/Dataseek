import api from './request'

export const musicApi = {
  /** 获取首页背景音乐信息，返回 { url, title, ... } */
  getBGM() { return api.get('/music/bgm') },
}

export default musicApi
