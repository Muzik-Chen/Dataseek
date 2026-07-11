<template>
  <div class="trip-card">
    <div class="trip-card__header">
      <span class="trip-card__icon">🗺️</span>
      <span class="trip-card__title">旅行方案</span>
    </div>

    <!-- 方案 Tab 切换 -->
    <el-tabs v-model="activePlan" class="trip-tabs">
      <el-tab-pane
        v-for="plan in plans"
        :key="plan.plan_id"
        :label="`方案${plan.plan_id}: ${plan.theme || plan.title?.slice(0, 8)}`"
        :name="plan.plan_id"
      />
    </el-tabs>

    <template v-if="currentPlan">
      <!-- 概览 -->
      <div class="trip-plan__summary">{{ currentPlan.summary }}</div>

      <!-- 交通 -->
      <div class="trip-plan__section" v-if="currentPlan.transport">
        <h4>🚗 交通方案</h4>
        <div class="trip-transport">
          <div class="transport-item" v-if="currentPlan.transport.to">
            <span class="transport-label">去程</span>
            <span>{{ currentPlan.transport.to.route }} · {{ currentPlan.transport.to.duration }} · ¥{{ currentPlan.transport.to.cost }}/人</span>
          </div>
          <div class="transport-item" v-if="currentPlan.transport.return">
            <span class="transport-label">返程</span>
            <span>{{ currentPlan.transport.return.route }} · {{ currentPlan.transport.return.duration }} · ¥{{ currentPlan.transport.return.cost }}/人</span>
          </div>
        </div>
      </div>

      <!-- 酒店 -->
      <div class="trip-plan__section" v-if="currentPlan.hotels?.length">
        <h4>🏨 推荐住宿</h4>
        <div class="trip-hotels">
          <div
            v-for="hotel in currentPlan.hotels"
            :key="hotel.name"
            class="hotel-item"
            :class="`hotel-${hotel.level}`"
          >
            <div class="hotel-info">
              <span class="hotel-name">{{ hotel.name }}</span>
              <span class="hotel-stars">{{ '⭐'.repeat(hotel.stars || 0) }}</span>
              <span class="hotel-price">¥{{ hotel.price }}/晚</span>
            </div>
            <div class="hotel-reason">{{ hotel.reason }}</div>
          </div>
        </div>
      </div>

      <!-- 每日行程 -->
      <div class="trip-plan__section" v-if="currentPlan.days?.length">
        <h4>📅 每日行程</h4>
        <el-collapse v-model="activeDays" accordion>
          <el-collapse-item
            v-for="day in currentPlan.days"
            :key="day.day"
            :title="`Day ${day.day} · ${day.title}`"
            :name="day.day"
          >
            <div
              v-for="act in day.activities"
              :key="act.time + act.name"
              class="activity-item"
            >
              <span class="activity-time">{{ act.time }}</span>
              <span class="activity-icon">{{ typeIcon(act.type) }}</span>
              <div class="activity-detail">
                <strong>{{ act.name }}</strong>
                <span v-if="act.cost" class="activity-cost">{{ act.cost }}</span>
                <p class="activity-desc">{{ act.description }}</p>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 费用 -->
      <div class="trip-plan__section" v-if="currentPlan.estimated_cost">
        <h4>💰 预估费用（每人）</h4>
        <div class="trip-cost">
          <div class="cost-row" v-if="currentPlan.estimated_cost.transport">
            <span>交通</span><span>¥{{ currentPlan.estimated_cost.transport }}</span>
          </div>
          <div class="cost-row" v-if="currentPlan.estimated_cost.hotel">
            <span>住宿</span><span>¥{{ currentPlan.estimated_cost.hotel }}</span>
          </div>
          <div class="cost-row" v-if="currentPlan.estimated_cost.food">
            <span>餐饮</span><span>¥{{ currentPlan.estimated_cost.food }}</span>
          </div>
          <div class="cost-row" v-if="currentPlan.estimated_cost.tickets">
            <span>门票</span><span>¥{{ currentPlan.estimated_cost.tickets }}</span>
          </div>
          <div class="cost-row cost-total">
            <span>合计</span><span>¥{{ currentPlan.estimated_cost.total }}</span>
          </div>
        </div>
      </div>

      <!-- 贴士 -->
      <div class="trip-plan__section" v-if="currentPlan.tips?.length">
        <h4>📝 出行贴士</h4>
        <ul class="trip-tips">
          <li v-for="tip in currentPlan.tips" :key="tip">{{ tip }}</li>
        </ul>
      </div>
    </template>

    <!-- 操作栏 -->
    <div class="trip-card__actions">
      <el-button type="primary" size="small" @click="$emit('save', currentPlan)" :disabled="!currentPlan">
        💾 保存到我的行程
      </el-button>
      <el-button size="small" @click="copyPlan">
        📋 复制
      </el-button>
      <el-button size="small" @click="$emit('refresh')">
        🔄 换一换
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  plans: { type: Array, default: () => [] },
})

defineEmits(['save', 'refresh'])

const activePlan = ref(props.plans[0]?.plan_id || 'A')
const activeDays = ref(1)

const currentPlan = computed(() =>
  props.plans.find(p => p.plan_id === activePlan.value)
)

function typeIcon(type) {
  const map = {
    food: '🍲', scenery: '📸', culture: '🏛️',
    shopping: '🛍️', transport: '🚗', rest: '😴',
  }
  return map[type] || '📍'
}

function copyPlan() {
  if (!currentPlan.value) return
  const text = JSON.stringify(currentPlan.value, null, 2)
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.info('复制失败，请手动选择')
  })
}
</script>

<style scoped>
.trip-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  max-width: 100%;
  font-size: var(--fs-sm);
}

.trip-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-weight: 600;
  margin-bottom: var(--space-sm);
  color: var(--ink);
}

.trip-card__icon { font-size: 18px; }

.trip-tabs { margin-bottom: var(--space-sm); }

.trip-plan__summary {
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--bg);
  border-radius: var(--radius-sm);
}

.trip-plan__section {
  margin-bottom: var(--space-md);
}

.trip-plan__section h4 {
  font-size: var(--fs-sm);
  color: var(--ink);
  margin: 0 0 var(--space-sm) 0;
}

.trip-transport {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.transport-item {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg);
  border-radius: var(--radius-sm);
  font-size: var(--fs-xs);
}

.transport-label {
  color: var(--primary);
  font-weight: 600;
  white-space: nowrap;
}

.trip-hotels { display: flex; flex-direction: column; gap: var(--space-xs); }

.hotel-item {
  padding: var(--space-sm);
  background: var(--bg);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}

.hotel-info {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  margin-bottom: 2px;
}

.hotel-name { font-weight: 600; }
.hotel-price { color: var(--primary); font-weight: 600; margin-left: auto; }
.hotel-reason { font-size: var(--fs-xs); color: var(--muted); }

.activity-item {
  display: flex;
  gap: var(--space-sm);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid oklch(0 0 0 / 0.05);
}

.activity-item:last-child { border-bottom: none; }

.activity-time {
  font-size: var(--fs-xs);
  color: var(--muted);
  white-space: nowrap;
  min-width: 44px;
}

.activity-icon { font-size: 16px; }

.activity-detail { flex: 1; min-width: 0; }
.activity-detail strong { display: block; font-size: var(--fs-sm); }
.activity-cost { font-size: var(--fs-xs); color: var(--primary); }
.activity-desc { margin: 2px 0 0; font-size: var(--fs-xs); color: var(--muted); }

.trip-cost { display: flex; flex-direction: column; gap: var(--space-xs); }

.cost-row {
  display: flex;
  justify-content: space-between;
  padding: var(--space-xs) var(--space-sm);
  background: var(--bg);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
}

.cost-total { font-weight: 700; color: var(--primary); }

.trip-tips {
  margin: 0;
  padding-left: var(--space-lg);
  font-size: var(--fs-xs);
  color: var(--muted);
}

.trip-tips li { margin-bottom: var(--space-xs); }

.trip-card__actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px solid oklch(0 0 0 / 0.06);
  flex-wrap: wrap;
}
</style>
