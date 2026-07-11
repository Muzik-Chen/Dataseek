export const rules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],

  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],

  smsCode: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码为 6 位数字', trigger: 'blur' },
  ],

  nickname: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { min: 2, max: 20, message: '昵称 2-20 个字符', trigger: 'blur' },
  ],

  postTitle: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 2, max: 50, message: '标题 2-50 个字符', trigger: 'blur' },
  ],

  postContent: [
    { required: true, message: '请输入正文', trigger: 'blur' },
    { min: 10, message: '正文至少 10 个字符', trigger: 'blur' },
  ],

  confirmPassword(passwordRef) {
    return [
      { required: true, message: '请再次输入密码', trigger: 'blur' },
      {
        validator: (rule, value, callback) => {
          if (value !== passwordRef?.value) {
            callback(new Error('两次输入的密码不一致'))
          } else {
            callback()
          }
        },
        trigger: 'blur',
      },
    ]
  },
}

export function validateFileSize(file, maxMB = 5) {
  const maxBytes = maxMB * 1024 * 1024
  return file.size <= maxBytes
}

export function validateImageType(file) {
  const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  return allowed.includes(file.type)
}
