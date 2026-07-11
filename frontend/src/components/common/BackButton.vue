<template>
  <button class="back-btn" @click="goBack" aria-label="返回上一页">
    <el-icon :size="18"><ArrowLeft /></el-icon>
    <span>返回</span>
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()

function goBack() {
  router.go(-1)
}
</script>

<style scoped>
.back-btn {
  display: none;
  align-items: center;
  gap: 4px;
  padding: 6px 14px 6px 10px;
  margin-bottom: var(--space-md);
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.back-btn:hover {
  color: var(--primary);
  background: var(--brand-red-muted);
  border-color: var(--primary);
}

.back-btn:active {
  transform: scale(0.96);
}

@media (max-width: 767px) {
  .back-btn {
    display: inline-flex;
  }
}
</style>
