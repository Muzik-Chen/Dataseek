<template>
  <!-- 空杯待茶 — 工夫茶杯隐喻空状态 -->
  <div class="empty-state">
    <div class="empty-state__cup" aria-hidden="true">
      <!-- CSS-drawn 工夫茶杯 -->
      <div class="tea-cup">
        <div class="tea-cup__bowl"></div>
        <div class="tea-cup__handle"></div>
        <!-- 蒸汽 -->
        <div class="tea-cup__steam">
          <span class="tea-cup__steam-line"></span>
          <span class="tea-cup__steam-line"></span>
        </div>
      </div>
    </div>

    <p class="empty-state__desc">{{ description }}</p>

    <p v-if="!$slots.default && !$slots.action" class="empty-state__hint">
      空杯待茶，精彩即将登场
    </p>

    <div v-if="$slots.action || $slots.default" class="empty-state__action">
      <slot name="action" />
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  description: { type: String, default: '暂无内容' },
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl) var(--space-md);
  text-align: center;
}

/* ── 工夫茶杯 (CSS drawn) ── */
.empty-state__cup {
  margin-bottom: var(--space-xl);
}

.tea-cup {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
}

/* 杯身 */
.tea-cup__bowl {
  width: 44px;
  height: 36px;
  border: 2.5px solid var(--brand-amber);
  border-radius: 4px 4px 14px 14px;
  background: oklch(0.97 0.02 80);
  position: relative;
  z-index: 1;
}

/* 杯内茶汤 — 浅浅的琥珀色 */
.tea-cup__bowl::after {
  content: '';
  position: absolute;
  bottom: 4px;
  left: 6px;
  right: 6px;
  height: 8px;
  background: oklch(0.82 0.08 80 / 0.4);
  border-radius: 50%;
}

/* 杯柄 */
.tea-cup__handle {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 22px;
  border: 2.5px solid var(--brand-amber);
  border-left: none;
  border-radius: 0 10px 10px 0;
  z-index: 0;
}

/* 蒸汽动画 */
.tea-cup__steam {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 6px;
}

.tea-cup__steam-line {
  display: block;
  width: 2px;
  height: 14px;
  background: var(--brand-amber);
  border-radius: var(--radius-full);
  opacity: 0;
  animation: steam-rise 2s ease-in-out infinite;
}

.tea-cup__steam-line:nth-child(2) {
  animation-delay: 0.7s;
}

@keyframes steam-rise {
  0% {
    opacity: 0;
    transform: translateY(6px) scaleY(0.6);
  }
  30% {
    opacity: 0.35;
  }
  70% {
    opacity: 0.15;
  }
  100% {
    opacity: 0;
    transform: translateY(-6px) scaleY(1.2);
  }
}

/* ── Text ── */
.empty-state__desc {
  font-size: var(--fs-base);
  color: var(--text-secondary);
  margin: 0 0 var(--space-sm);
}

.empty-state__hint {
  font-size: var(--fs-sm);
  color: var(--text-tertiary);
  margin: 0 0 var(--space-lg);
  font-style: italic;
}

/* ── Action ── */
.empty-state__action {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

/* ── Reduced motion ── */
@media (prefers-reduced-motion: reduce) {
  .tea-cup__steam-line {
    animation: none;
    opacity: 0.2;
  }
}
</style>
