import api from './request'

export const authApi = {
  sendCode(email, purpose = 'register') {
    return api.post('/auth/send-code', { email, purpose })
  },
  register(email, code, password, confirmPassword, nickname) {
    return api.post('/auth/register', {
      email, code, password, confirm_password: confirmPassword, nickname,
    })
  },
  login(email, password) {
    return api.post('/auth/login', { email, password })
  },
  resetPassword(email, code, newPassword) {
    return api.post('/auth/reset-password', { email, code, new_password: newPassword })
  },
}

export default authApi
