<template>
  <div class="admin-page">
    <h1>系统设置</h1>
    <el-card style="max-width: 640px;">
      <el-form :model="form" label-width="140px" v-loading="loading">

        <!-- LLM -->
        <el-divider content-position="left">LLM 配置</el-divider>
        <el-form-item label="LLM 提供商">
          <el-radio-group v-model="form.llm_provider">
            <el-radio value="qwen">阿里云通义千问</el-radio>
            <el-radio value="deepseek">DeepSeek</el-radio>
            <el-radio value="zhipu">智谱 AI</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="form.llm_model" style="width: 100%;">
            <template v-if="form.llm_provider === 'qwen'">
              <el-option label="Qwen-Turbo (快速)" value="qwen-turbo" />
              <el-option label="Qwen-Plus (均衡)" value="qwen-plus" />
              <el-option label="Qwen-Max (强大)" value="qwen-max" />
            </template>
            <template v-else-if="form.llm_provider === 'deepseek'">
              <el-option label="DeepSeek-Chat" value="deepseek-chat" />
            </template>
            <template v-else>
              <el-option label="GLM-4-Flash" value="glm-4-flash" />
            </template>
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            :placeholder="form.api_key ? '已配置（输入新值覆盖）' : 'sk-...'"
          />
        </el-form-item>

        <!-- SMTP -->
        <el-divider content-position="left">邮件配置 (SMTP)</el-divider>
        <el-form-item label="服务器地址">
          <el-input v-model="form.smtp_server" placeholder="smtp.163.com" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="form.smtp_username" placeholder="your-email@163.com" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.smtp_password"
            type="password"
            show-password
            :placeholder="form.smtp_password ? '已配置（输入新值覆盖）' : ''"
          />
        </el-form-item>
        <el-form-item label="发件人地址">
          <el-input v-model="form.smtp_from" placeholder="your-email@163.com" />
        </el-form-item>

        <!-- SMS -->
        <el-divider content-position="left">短信配置 (阿里云 SMS)</el-divider>
        <el-form-item label="Access Key">
          <el-input v-model="form.sms_access_key" placeholder="LTAI..." />
        </el-form-item>
        <el-form-item label="Access Secret">
          <el-input
            v-model="form.sms_access_secret"
            type="password"
            show-password
            :placeholder="form.sms_access_secret ? '已配置（输入新值覆盖）' : ''"
          />
        </el-form-item>
        <el-form-item label="签名名称">
          <el-input v-model="form.sms_sign_name" placeholder="潮汕文化平台" />
        </el-form-item>

        <!-- 天气 -->
        <el-divider content-position="left">天气 API</el-divider>
        <el-form-item label="和风天气 API Key">
          <el-input
            v-model="form.weather_api_key"
            type="password"
            show-password
            :placeholder="form.weather_api_key ? '已配置（输入新值覆盖）' : ''"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="handleSave">保存设置</el-button>
          <el-button @click="loadSettings">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import adminApi from '@/api/admin'
import { toast } from '@/utils/toast'

const loading = ref(false)
const saving = ref(false)

const form = reactive({
  llm_provider: 'qwen',
  llm_model: 'qwen-turbo',
  api_key: '',
  smtp_server: 'smtp.163.com',
  smtp_username: '',
  smtp_password: '',
  smtp_from: '',
  sms_access_key: '',
  sms_access_secret: '',
  sms_sign_name: '潮汕文化平台',
  weather_api_key: '',
})

async function loadSettings() {
  loading.value = true
  try {
    const data = await adminApi.getSettings()
    if (data) Object.assign(form, data)
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}

async function handleSave() {
  saving.value = true
  try {
    await adminApi.updateSettings(form)
    toast.success('设置已保存')
  } catch (e) {
    toast.error(e?.message || '保存失败')
  }
  finally { saving.value = false }
}

onMounted(() => loadSettings())
</script>

<style scoped>
.admin-page h1 { font-size: 1.5rem; margin-bottom: 24px; }
</style>
