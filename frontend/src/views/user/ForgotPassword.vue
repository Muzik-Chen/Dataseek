<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <router-link to="/" class="auth-logo">
          <span class="logo-icon">潮</span>
          <span class="logo-text">潮汕文化宣传平台</span>
        </router-link>
        <h1>找回密码</h1>
        <p>验证邮箱，设置新密码</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="auth-form"
        @submit.prevent="handleReset"
      >
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="请输入已注册的邮箱"
            :prefix-icon="Message"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="code">
          <div class="code-row">
            <el-input
              v-model="form.code"
              placeholder="验证码"
              :prefix-icon="Key"
              maxlength="6"
              size="large"
            />
            <el-button
              :disabled="countdown > 0"
              :loading="sending"
              size="large"
              class="code-btn"
              @click="sendCode"
            >
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item prop="newPassword">
          <el-input
            v-model="form.newPassword"
            type="password"
            placeholder="请设置新密码（至少6位）"
            :prefix-icon="Lock"
            show-password
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="submit-btn"
            @click="handleReset"
          >
            {{ loading ? '重置中...' : '重置密码' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        <span>想起密码了？</span>
        <router-link to="/login" class="link">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Message, Key, Lock } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'

const router = useRouter()

const formRef = ref(null)
const loading = ref(false)
const sending = ref(false)
const countdown = ref(0)
let timer = null

const form = reactive({
  email: '',
  code: '',
  newPassword: '',
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
<<<<<<< HEAD
    { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '邮箱格式不正确', trigger: 'blur' },
=======
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' },
  ],
  newPassword: [
    { required: true, message: '请设置新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

async function sendCode() {
  const emailValid = await formRef.value?.validateField('email').catch(() => false)
  if (!emailValid) return

  sending.value = true
  try {
    await authApi.sendCode(form.email, 'reset_password')
    ElMessage.success('验证码已发送，请查收邮件')
    countdown.value = 60
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (e) {
    ElMessage.error(e.message || '发送失败，请重试')
  } finally {
    sending.value = false
  }
}

async function handleReset() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authApi.resetPassword(form.email, form.code, form.newPassword)
    ElMessage.success('密码重置成功，请重新登录')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message || '重置失败，请重试')
  } finally {
    loading.value = false
  }
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  padding: var(--space-lg);
}

.auth-card {
  width: 100%;
  max-width: 420px;
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-3xl) var(--space-2xl);
  box-shadow: 0 4px 24px oklch(0 0 0 / 0.06);
}

.auth-header {
  text-align: center;
  margin-bottom: var(--space-2xl);
}

.auth-logo {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  text-decoration: none;
  margin-bottom: var(--space-xl);
}

.logo-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary);
  color: #fff;
  font-size: var(--fs-xl);
  font-weight: 700;
  border-radius: 12px;
}

.logo-text {
  font-size: var(--fs-lg);
  font-weight: 600;
  color: var(--ink);
}

.auth-header h1 {
  font-size: var(--fs-2xl);
  color: var(--ink);
  margin: 0 0 var(--space-xs);
}

.auth-header p {
  color: var(--muted);
  margin: 0;
  font-size: var(--fs-sm);
}

.auth-form {
  margin-bottom: var(--space-lg);
}

.code-row {
  display: flex;
  gap: var(--space-sm);
}

.code-row .el-input {
  flex: 1;
}

.code-btn {
  min-width: 120px;
  flex-shrink: 0;
}

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: var(--fs-base);
  font-weight: 600;
}

.auth-footer {
  text-align: center;
  color: var(--muted);
  font-size: var(--fs-sm);
}

.auth-footer .link {
  color: var(--primary);
  font-weight: 600;
  text-decoration: none;
  margin-left: var(--space-xs);
}

.auth-footer .link:hover {
  text-decoration: underline;
}
</style>
