<template>
  <div class="admin-page">
    <h1>系统设置</h1>
    <el-card style="max-width: 600px;">
      <el-form :model="form" label-width="140px" v-loading="loading">
        <el-divider content-position="left">LLM 配置</el-divider>
        <el-form-item label="LLM 提供商">
          <el-radio-group v-model="form.llm_provider">
            <el-radio value="qwen">阿里云通义千问</el-radio>
            <el-radio value="deepseek">DeepSeek</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="form.llm_model">
            <el-option v-if="form.llm_provider === 'qwen'" label="Qwen-Turbo (快速)" value="qwen-turbo" />
            <el-option v-if="form.llm_provider === 'qwen'" label="Qwen-Plus (均衡)" value="qwen-plus" />
            <el-option v-if="form.llm_provider === 'qwen'" label="Qwen-Max (强大)" value="qwen-max" />
            <el-option v-if="form.llm_provider === 'deepseek'" label="DeepSeek-Chat" value="deepseek-chat" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>

        <el-divider content-position="left">短信配置</el-divider>
        <el-form-item label="Access Key"><el-input v-model="form.sms_access_key" /></el-form-item>
        <el-form-item label="Access Secret"><el-input v-model="form.sms_access_secret" type="password" show-password /></el-form-item>
        <el-form-item label="签名名称"><el-input v-model="form.sms_sign_name" placeholder="潮汕文化平台" /></el-form-item>

        <el-divider content-position="left">天气 API</el-divider>
        <el-form-item label="和风天气 API Key"><el-input v-model="form.weather_api_key" type="password" show-password /></el-form-item>

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
import api from '@/api/request'
import { toast } from '@/utils/toast'

const loading = ref(false); const saving = ref(false)
const form = reactive({ llm_provider: 'qwen', llm_model: 'qwen-turbo', api_key: '', sms_access_key: '', sms_access_secret: '', sms_sign_name: '潮汕文化平台', weather_api_key: '' })

async function loadSettings() {
  loading.value = true
  try { const data = await api.get('/admin/settings'); if (data) Object.assign(form, data) } catch { /* */ } finally { loading.value = false }
}

async function handleSave() {
  saving.value = true
  try { await api.put('/admin/settings', form); toast.success('设置已保存') } catch { toast.error('保存失败') } finally { saving.value = false }
}

onMounted(() => loadSettings())
</script>
<style scoped>
.admin-page h1 { font-size: 1.5rem; margin-bottom: 24px; }
</style>
