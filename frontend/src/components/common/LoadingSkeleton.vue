<template>
  <!-- 关公巡城 — 三杯循环递进加载 -->
  <div class="skeleton-wrapper" role="status" aria-label="加载中">
    <template v-if="type === 'card'">
      <div
        v-for="i in count"
        :key="i"
        class="skeleton-card"
        :style="{ '--stagger': staggerIndex(i) }"
      >
        <div class="skeleton-rect shimmer"></div>
        <div class="skeleton-line shimmer" style="width: 70%"></div>
        <div class="skeleton-line shimmer" style="width: 50%"></div>
      </div>
    </template>

    <template v-else-if="type === 'list'">
      <div
        v-for="i in count"
        :key="i"
        class="skeleton-list-item"
        :style="{ '--stagger': staggerIndex(i) }"
      >
        <div class="skeleton-circle shimmer"></div>
        <div class="skeleton-list-text">
          <div class="skeleton-line shimmer" style="width: 60%"></div>
          <div class="skeleton-line shimmer" style="width: 40%"></div>
        </div>
      </div>
    </template>

    <template v-else-if="type === 'banner'">
      <div class="skeleton-banner shimmer"></div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'card',
    validator: (v) => ['card', 'list', 'banner'].includes(v),
  },
  count: { type: Number, default: 6 },
})

/**
 * 关公巡城节奏 — 3杯循环, 每杯间隔 200ms
 * 1,4,7... → 0ms | 2,5,8... → 200ms | 3,6,9... → 400ms
 */
function staggerIndex(i) {
  const cup = ((i - 1) % 3)
  return `${cup * 200}ms`
}
</script>

<style scoped>
.skeleton-wrapper {
  display: contents;
}

.skeleton-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton-rect {
  aspect-ratio: 16 / 10;
  border-radius: var(--radius-md);
}

.skeleton-circle {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.skeleton-line {
  height: 14px;
  border-radius: 4px;
}

.skeleton-list-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) 0;
}

.skeleton-list-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.skeleton-banner {
  width: 100%;
  aspect-ratio: 21 / 9;
  border-radius: var(--radius-lg);
}

/* ── 关公巡城 Shimmer — 茶汤般暖调 ── */
.shimmer {
  background: linear-gradient(
    90deg,
    oklch(0.94 0.01 60) 25%,
    oklch(0.89 0.015 70) 50%,
    oklch(0.94 0.01 60) 75%
  );
  background-size: 200% 100%;
  animation: tea-pour 1.5s infinite;
  /* 三杯 staggered delay via inline --stagger */
  animation-delay: var(--stagger, 0ms);
}

@keyframes tea-pour {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Reduced motion ── */
@media (prefers-reduced-motion: reduce) {
  .shimmer {
    animation: none;
    background: oklch(0.94 0.01 60);
  }
}
</style>
