<template>
  <div class="trip-create-page">
    <BackButton />
    <!-- 页面标题 · 不对称左对齐 -->
    <div class="page-header">
      <h1 class="display-text--section">🧭 创建行程</h1>
      <p>告诉AI您的偏好，智能生成专属潮汕旅行计划</p>
      <div class="section-divider section-divider--left"></div>
    </div>

    <!-- ===== 步骤指示器 ===== -->
    <div class="steps-bar">
      <div class="steps-wrapper">
        <div
          v-for="(step, idx) in steps"
          :key="idx"
          :class="['step-item', { active: currentStep === idx, done: currentStep > idx }]"
          @click="currentStep > idx && (currentStep = idx)"
        >
          <div class="step-circle">
            <el-icon v-if="currentStep > idx" :size="16"><Check /></el-icon>
            <span v-else>{{ idx + 1 }}</span>
          </div>
          <div class="step-label">
            <span class="step-num">步骤 {{ idx + 1 }}</span>
            <span class="step-title">{{ step.title }}</span>
          </div>
        </div>
      </div>
      <div class="steps-connector">
        <div class="connector-fill" :style="{ width: progressPercent + '%' }" />
      </div>
    </div>

    <!-- ===== 表单区域 ===== -->
    <div class="form-card">
      <!-- Step 1: 行程参数 -->
      <div v-show="currentStep === 0" class="step-content">
        <h3 class="step-heading">📅 行程基本参数</h3>

        <div class="step-field">
          <label class="field-label">旅行天数</label>
          <div class="days-picker">
            <el-input-number
              v-model="form.days"
              :min="1"
              :max="14"
              size="large"
              controls-position="right"
            />
            <span class="field-hint">建议 3-5 天可覆盖核心景点</span>
          </div>
        </div>

        <div class="step-field">
          <label class="field-label">预算档位</label>
          <el-radio-group v-model="form.budget" size="large">
            <el-radio-button value="low">💰 经济型</el-radio-button>
            <el-radio-button value="mid">💰💰 舒适型</el-radio-button>
            <el-radio-button value="high">💰💰💰 豪华型</el-radio-button>
          </el-radio-group>
        </div>

        <div class="step-field">
          <label class="field-label">出发城市</label>
          <el-input
            v-model="form.origin"
            placeholder="如：深圳、广州"
            maxlength="20"
            style="max-width: 280px"
            size="large"
          />
          <span class="field-hint">用于规划往返交通方案</span>
        </div>
      </div>

      <!-- Step 2: 出行人群 -->
      <div v-show="currentStep === 1" class="step-content">
        <h3 class="step-heading">👥 选择出行人群</h3>
        <p class="step-desc">AI 会根据同行人群调整行程风格和节奏</p>

        <div class="crowd-cards">
          <div
            v-for="c in crowdOptions"
            :key="c.value"
            :class="['crowd-card', { selected: form.crowd_type === c.value }]"
            @click="form.crowd_type = c.value"
          >
            <span class="crowd-icon">{{ c.icon }}</span>
            <strong>{{ c.label }}</strong>
            <p>{{ c.desc }}</p>
          </div>
        </div>
      </div>

      <!-- Step 3: 偏好选择 -->
      <div v-show="currentStep === 2" class="step-content">
        <h3 class="step-heading">🎯 选择您的兴趣偏好</h3>
        <p class="step-desc">AI 将根据您的偏好调整行程中各类活动的比重</p>

        <div class="pref-grid">
          <div
            v-for="p in prefOptions"
            :key="p.value"
            :class="['pref-card', { on: form.preferences.includes(p.value) }]"
            @click="togglePref(p.value)"
          >
            <span class="pref-icon">{{ p.icon }}</span>
            <span class="pref-label">{{ p.label }}</span>
          </div>
        </div>

        <div v-if="form.preferences.length === 0" class="pref-warning">
          ⚠️ 请至少选择一项偏好
        </div>
      </div>

      <!-- Step 4: 确认生成 -->
      <div v-show="currentStep === 3" class="step-content">
        <h3 class="step-heading">✅ 确认并生成</h3>

        <div class="summary-card">
          <div class="summary-row">
            <span class="summary-label">行程标题</span>
            <el-input
              v-model="form.title"
              placeholder="如：潮汕3天美食之旅"
              maxlength="100"
              size="large"
            />
          </div>
          <div class="summary-row">
            <span class="summary-label">天数</span>
            <span class="summary-value">{{ form.days }} 天</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">预算</span>
            <span class="summary-value">{{ budgetLabel(form.budget) }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">出发地</span>
            <span class="summary-value">{{ form.origin || '未指定' }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">出行人群</span>
            <span class="summary-value">{{ crowdLabel(form.crowd_type) }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">偏好</span>
            <div class="summary-tags">
              <el-tag v-for="p in form.preferences" :key="p" size="small" round>{{ p }}</el-tag>
            </div>
          </div>
        </div>

        <div class="generate-area">
          <el-button
            type="primary"
            size="large"
            :loading="generating"
            :disabled="!form.title || !form.preferences.length"
            @click="generatePlan"
          >
            {{ generating ? generatingText : '🤖 AI 智能规划' }}
          </el-button>
        </div>
      </div>

      <!-- 步骤导航按钮 -->
      <div class="step-nav">
        <el-button
          v-if="currentStep > 0"
          size="large"
          @click="currentStep--"
        >上一步</el-button>
        <div class="step-nav-spacer" />
        <el-button
          v-if="currentStep < 3"
          type="primary"
          size="large"
          :disabled="!canProceed"
          @click="currentStep++"
        >下一步</el-button>
      </div>
    </div>

    <!-- ===== AI 生成的行程预览 ===== -->
    <div v-if="planResult" class="plan-result">
      <h2>📋 您的行程计划</h2>

      <!-- AI 3方案格式 -->
      <template v-if="planResult.plans?.length">
        <TripCard
          :plans="planResult.plans"
          @save="savePlan"
          @refresh="regeneratePlan"
        />
      </template>

      <!-- 新格式但是 plans 为空 -->
      <div v-else-if="planResult.plans !== undefined && planResult.plans.length === 0" class="plan-empty">
        <p>😕 AI 未能成功生成方案，请检查后端日志或稍后重试</p>
        <el-button type="primary" @click="regeneratePlan">重新生成</el-button>
      </div>

      <!-- 旧格式（mock 降级） -->
      <template v-else>
        <div class="plan-days">
          <div v-for="day in planResult.days" :key="day.day" class="plan-day">
            <div class="day-header">
              <span class="day-num">Day {{ day.day }}</span>
              <h3>{{ day.title }}</h3>
            </div>
            <div class="day-spots">
              <div v-for="spot in day.spots" :key="spot.name" class="spot-item">
                <span class="spot-time">{{ spot.duration }}</span>
                <div class="spot-info">
                  <strong>{{ spot.name }}</strong>
                  <el-tag size="small">{{ spot.type }}</el-tag>
                  <p>{{ spot.tip }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="planResult.tips" class="plan-tips">
          <h3>💡 出行小贴士</h3>
          <ul>
            <li v-for="tip in planResult.tips" :key="tip">{{ tip }}</li>
          </ul>
        </div>

        <div class="plan-actions">
          <el-button type="primary" size="large" @click="savePlan">保存行程</el-button>
          <el-button size="large" @click="regeneratePlan">重新生成</el-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import { createTripPlan } from '@/api'
import BackButton from '@/components/common/BackButton.vue'
import TripCard from '@/components/business/TripCard.vue'

const router = useRouter()

// === 步骤状态 ===
const steps = [
  { title: '行程参数' },
  { title: '出行人群' },
  { title: '偏好选择' },
  { title: '确认生成' },
]
const currentStep = ref(0)
const progressPercent = computed(() => (currentStep.value / (steps.length - 1)) * 100)

// === 表单 ===
const generating = ref(false)
const planResult = ref(null)
const generatingText = ref('AI 正在规划中...')

const form = reactive({
  title: '',
  origin: '广州',
  days: 3,
  budget: 'mid',
  crowd_type: 'solo',
  preferences: ['美食', '非遗'],
})

// === 选项数据 ===
const crowdOptions = [
  { value: 'solo', icon: '🧑', label: '独自旅行', desc: '自由探索，节奏随性' },
  { value: 'couple', icon: '💑', label: '情侣出游', desc: '浪漫景点、美食打卡' },
  { value: 'family', icon: '👨‍👩‍👧', label: '家庭出游', desc: '老少皆宜、轻松舒适' },
  { value: 'friends', icon: '👫', label: '朋友结伴', desc: '热闹体验、深度探索' },
]

const prefOptions = [
  { value: '美食', icon: '🍲', label: '美食探索' },
  { value: '非遗', icon: '🎭', label: '非遗文化' },
  { value: '自然', icon: '🏞️', label: '自然风光' },
  { value: '历史', icon: '🏛️', label: '历史古迹' },
  { value: '民俗', icon: '🎊', label: '民俗体验' },
  { value: '购物', icon: '🛍️', label: '特产购物' },
]

// === 每步校验 ===
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0: return form.days >= 1 && form.days <= 14
    case 1: return !!form.crowd_type
    case 2: return form.preferences.length > 0
    default: return true
  }
})

// === 标签函数 ===
function budgetLabel(v) {
  return { low: '💰 经济型', mid: '💰💰 舒适型', high: '💰💰💰 豪华型' }[v] || v
}
function crowdLabel(v) {
  return crowdOptions.find(c => c.value === v)?.label || v
}
function togglePref(val) {
  const idx = form.preferences.indexOf(val)
  if (idx > -1) form.preferences.splice(idx, 1)
  else form.preferences.push(val)
}

// === 生成逻辑 ===
const thinkingLabels = [
  '正在了解潮汕美食…',
  '正在安排每日路线…',
  '正在优化行程方案…',
  '即将完成…',
]
let thinkingTimer = null

async function generatePlan() {
  if (!form.title) {
    ElMessage.warning('请输入行程标题')
    return
  }
  if (!form.preferences.length) {
    ElMessage.warning('请至少选一项偏好')
    return
  }

  generating.value = true
  planResult.value = null

  // 循环切换加载文案
  let ti = 0
  generatingText.value = thinkingLabels[0]
  thinkingTimer = setInterval(() => {
    ti = (ti + 1) % thinkingLabels.length
    generatingText.value = thinkingLabels[ti]
  }, 2500)

  try {
    const data = await createTripPlan({
      title: form.title,
      origin: form.origin,
      days: form.days,
      budget: form.budget,
      crowd_type: form.crowd_type,
      preferences: form.preferences,
    })
    planResult.value = data.plan_content || data

    const hasPlans = planResult.value?.plans?.length > 0
    const hasOldFormat = planResult.value?.days?.length > 0

    if (hasPlans) {
      const errorCount = planResult.value.plans.filter(p => p.error).length
      if (errorCount === planResult.value.plans.length) {
        ElMessage.warning(`行程生成遇到问题（${errorCount}/3 失败），可尝试重新生成`)
      } else {
        ElMessage.success(`行程规划完成！共生成 ${planResult.value.plans.length} 套方案`)
      }
    } else if (hasOldFormat) {
      ElMessage.success('行程规划完成！')
    } else {
      ElMessage.warning('行程内容为空，请检查后端日志或稍后重试')
    }
  } catch {
    planResult.value = mockPlan()
    ElMessage.info('已生成演示行程（离线模式）')
  } finally {
    generating.value = false
    if (thinkingTimer) {
      clearInterval(thinkingTimer)
      thinkingTimer = null
    }
    generatingText.value = 'AI 正在规划中...'
  }
}

function regeneratePlan() {
  planResult.value = null
  generatePlan()
}

function savePlan(selectedPlan) {
  if (selectedPlan) {
    console.log('[TripCreate] Saving plan:', selectedPlan.title)
  }
  ElMessage.success('行程已保存，可在个人中心查看')
  setTimeout(() => router.push('/profile'), 800)
}

function mockPlan() {
  return {
    days: [
      {
        day: 1, title: '汕头老城 · 美食初探',
        spots: [
          { name: '小公园骑楼群', type: '景点', duration: '1.5小时', tip: '拍摄骑楼最佳时间在上午' },
          { name: '八合里海记牛肉火锅', type: '美食', duration: '1小时', tip: '吊龙和匙柄是必点' },
          { name: '西堤公园', type: '景点', duration: '1小时', tip: '傍晚看日落位置绝佳' },
        ],
      },
      {
        day: 2, title: '潮州古城 · 非遗之旅',
        spots: [
          { name: '广济桥', type: '景点', duration: '1.5小时', tip: '中国四大古桥之一' },
          { name: '工夫茶体验馆', type: '体验', duration: '1.5小时', tip: '学习二十一式冲泡法' },
          { name: '牌坊街', type: '街区', duration: '2小时', tip: '品尝地道小吃' },
        ],
      },
      {
        day: 3, title: '南澳岛 · 海岛风光',
        spots: [
          { name: '青澳湾', type: '景点', duration: '2小时', tip: '广东最美的海湾之一' },
          { name: '南澳总兵府', type: '历史', duration: '1小时', tip: '明清海防重地' },
          { name: '海鲜大排档', type: '美食', duration: '1.5小时', tip: '现捞现做' },
        ],
      },
    ],
    tips: [
      '潮汕秋冬季节（10月-次年4月）是最佳旅游时间',
      '牛肉火锅建议午餐去，牛肉最新鲜',
      '部分非遗体验项目需提前预约',
    ],
    crowd_label: crowdLabel(form.crowd_type),
    preferences: form.preferences,
  }
}
</script>

<style scoped>
.trip-create-page {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-md);
}

.page-header {
  text-align: left;
  margin-bottom: var(--space-2xl);
}

.page-header h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-xs); }
.page-header p { color: var(--muted); margin: 0 0 var(--space-md); }

/* ===== 步骤条 ===== */
.steps-bar {
  position: relative;
  margin-bottom: var(--space-2xl);
  padding: 0 var(--space-lg);
}

.steps-wrapper {
  display: flex;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  cursor: default;
}

.step-item.done {
  cursor: pointer;
}

.step-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: oklch(0 0 0 / 0.06);
  color: var(--muted);
  font-weight: 600;
  font-size: var(--fs-base);
  transition: all 0.3s;
}

.step-item.active .step-circle {
  background: var(--brand-red);
  color: #fff;
  box-shadow: 0 4px 12px oklch(0.53 0.22 25 / 0.35);
}

.step-item.done .step-circle {
  background: var(--brand-red);
  color: #fff;
}

.step-label {
  text-align: center;
}

.step-num {
  display: block;
  font-size: var(--fs-xs);
  color: var(--muted);
}

.step-title {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--muted);
}

.step-item.active .step-title,
.step-item.done .step-title {
  color: var(--ink);
}

.steps-connector {
  position: absolute;
  top: 20px;
  left: calc(12.5% + 20px);
  right: calc(12.5% + 20px);
  height: 2px;
  background: oklch(0 0 0 / 0.08);
  z-index: 0;
}

.connector-fill {
  height: 100%;
  background: var(--brand-red);
  transition: width 0.3s;
}

/* ===== 表单卡片 ===== */
.form-card {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-2xl);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-2xl);
}

.step-heading {
  font-size: var(--fs-xl);
  color: var(--ink);
  margin: 0 0 var(--space-xs);
}

.step-desc {
  color: var(--muted);
  font-size: var(--fs-sm);
  margin: 0 0 var(--space-xl);
}

.step-field {
  margin-bottom: var(--space-xl);
}

.field-label {
  display: block;
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--ink);
  margin-bottom: var(--space-sm);
}

.field-hint {
  color: var(--muted);
  font-size: var(--fs-sm);
  margin-left: var(--space-md);
}

.days-picker {
  display: flex;
  align-items: center;
}

/* ===== Step 2: 人群选择卡片 ===== */
.crowd-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
}

.crowd-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xl) var(--space-md);
  border: 2px solid oklch(0 0 0 / 0.08);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.crowd-card:hover {
  border-color: oklch(0.55 0.18 28 / 0.3);
  background: oklch(0.55 0.18 28 / 0.03);
}

.crowd-card.selected {
  border-color: var(--primary);
  background: oklch(0.55 0.18 28 / 0.06);
  box-shadow: 0 0 0 4px oklch(0.55 0.18 28 / 0.08);
}

.crowd-icon { font-size: 36px; }
.crowd-card strong { font-size: var(--fs-base); color: var(--ink); }
.crowd-card p { font-size: var(--fs-sm); color: var(--muted); margin: 0; }

/* ===== Step 3: 偏好卡片 ===== */
.pref-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.pref-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-lg);
  border: 2px solid oklch(0 0 0 / 0.08);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.pref-card:hover {
  border-color: oklch(0.55 0.18 28 / 0.25);
}

.pref-card.on {
  border-color: var(--primary);
  background: oklch(0.55 0.18 28 / 0.06);
}

.pref-icon { font-size: 28px; }
.pref-label { font-size: var(--fs-sm); font-weight: 600; color: var(--ink); }

.pref-warning {
  margin-top: var(--space-md);
  color: var(--accent);
  font-size: var(--fs-sm);
  text-align: center;
}

/* ===== Step 4: 确认 ===== */
.summary-card {
  background: oklch(0 0 0 / 0.02);
  border-radius: 12px;
  padding: var(--space-xl);
  margin-bottom: var(--space-xl);
}

.summary-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid oklch(0 0 0 / 0.04);
}

.summary-row:last-child { border-bottom: none; }

.summary-label {
  min-width: 80px;
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--muted);
}

.summary-value {
  font-size: var(--fs-base);
  color: var(--ink);
}

.summary-tags {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.generate-area {
  text-align: center;
  padding-top: var(--space-md);
}

/* ===== 步骤导航 ===== */
.step-nav {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-xl);
  padding-top: var(--space-xl);
  border-top: 1px solid oklch(0 0 0 / 0.06);
}

.step-nav-spacer { flex: 1; }

/* ===== 结果展示区 ===== */
.plan-result {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-2xl);
  box-shadow: var(--shadow-sm);
}

.plan-result h2 { font-size: var(--fs-xl); color: var(--ink); margin: 0 0 var(--space-xl); }

.plan-days { display: flex; flex-direction: column; gap: var(--space-xl); }

.plan-day {
  border: 1px solid oklch(0 0 0 / 0.08);
  border-radius: 12px;
  padding: var(--space-lg);
}

.day-header { display: flex; align-items: center; gap: var(--space-md); margin-bottom: var(--space-md); }
.day-num { background: var(--brand-red); color: #fff; padding: 4px 14px; border-radius: 12px; font-weight: 600; font-size: var(--fs-sm); }
.day-header h3 { font-size: var(--fs-lg); color: var(--ink); margin: 0; }

.day-spots { display: flex; flex-direction: column; gap: var(--space-sm); }

.spot-item { display: flex; gap: var(--space-md); padding: var(--space-sm) 0; }
.spot-time { color: var(--muted); font-size: var(--fs-sm); min-width: 72px; }
.spot-info strong { color: var(--ink); display: block; }
.spot-info p { color: var(--muted); font-size: var(--fs-sm); margin: 4px 0 0; }

.plan-tips {
  margin-top: var(--space-xl);
  padding: var(--space-lg);
  background: oklch(0.55 0.18 28 / 0.06);
  border-radius: 10px;
}

.plan-tips h3 { font-size: var(--fs-base); color: var(--ink); margin: 0 0 var(--space-sm); }
.plan-tips ul { margin: 0; padding-left: var(--space-lg); }
.plan-tips li { color: var(--muted); font-size: var(--fs-sm); margin-bottom: 4px; }

.plan-empty {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--muted);
}

.plan-empty p { margin: 0 0 var(--space-lg); font-size: var(--fs-base); }

.plan-actions { display: flex; gap: var(--space-md); margin-top: var(--space-xl); padding-top: var(--space-xl); border-top: 1px solid oklch(0 0 0 / 0.06); }

@media (max-width: 640px) {
  .crowd-cards { grid-template-columns: 1fr; }
  .pref-grid { grid-template-columns: repeat(2, 1fr); }
  .days-picker { flex-direction: column; align-items: flex-start; gap: var(--space-sm); }
  .step-label { display: none; }
  .steps-connector { left: 24px; right: 24px; }
}
</style>
