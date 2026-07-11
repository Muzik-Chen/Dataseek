<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <router-link to="/" class="auth-logo">
          <span class="logo-icon">潮</span>
          <span class="logo-text">潮汕文化宣传平台</span>
        </router-link>
        <h1>欢迎回来</h1>
        <p>登录您的账号，探索潮汕文化</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        class="auth-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="请输入邮箱"
            :prefix-icon="Message"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="submit-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        <span>还没有账号？</span>
        <router-link to="/register" class="link">立即注册</router-link>
      </div>
      <div class="auth-footer" style="margin-top: 8px">
        <router-link to="/forgot-password" class="link">忘记密码？</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Message, Lock } from '@element-plus/icons-vue'
import { login } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  email: '',
  password: '',
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const data = await login(form.email, form.password)
    userStore.setAuth(data.token, data.user)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    ElMessage.error(e.message || '登录失败，请重试')
  } finally {
    loading.value = false
  }
}
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
  box-shadow: var(--shadow-md);
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
  background: var(--brand-red);
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
