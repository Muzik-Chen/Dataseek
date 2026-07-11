<template>
  <!-- 印章善本卡片 -->
  <article v-if="item" class="heritage-card" @click="goDetail">
    <!-- 印章角标 -->
    <div class="heritage-card__seal" aria-hidden="true">
      <span class="heritage-card__seal-text">非遗</span>
    </div>

    <!-- 琥珀善本边框 -->
    <div class="heritage-card__inner">
      <div class="heritage-card__media">
        <img
          v-if="item.image_url"
          :src="item.image_url"
          :alt="item.name"
          class="heritage-card__img"
          loading="lazy"
          @error="(e) => { e.target.style.display = 'none' }"
        />
        <span v-else class="heritage-card__placeholder">🎭</span>
      </div>

      <div class="heritage-card__content">
        <h3 class="heritage-card__name">{{ item.name }}</h3>

        <div class="heritage-card__tags">
          <span class="heritage-card__level" :class="'heritage-card__level--' + levelClass(item.category)">
            {{ item.category || '非遗' }}
          </span>
          <span v-if="item.type" class="heritage-card__type">{{ item.type }}</span>
          <span v-if="item.region" class="heritage-card__region">📍 {{ item.region }}</span>
        </div>

        <p class="heritage-card__desc">{{ item.description?.slice(0, 150) || '暂无描述' }}</p>

        <div v-if="item.inheritor" class="heritage-card__inheritor">
          <span class="heritage-card__inheritor-icon">👤</span>
          <span>传承人：{{ item.inheritor }}</span>
        </div>
      </div>
    </div>

    <div class="heritage-card__actions">
      <button class="heritage-card__btn heritage-card__btn--primary" @click.stop="goDetail">
        查看详情
      </button>
      <button class="heritage-card__btn heritage-card__btn--ghost" @click.stop="$emit('favorite', item)">
        ♥ 收藏
      </button>
    </div>
  </article>
</template>

<script setup>
import { useRouter } from 'vue-router'

defineProps({
  item: { type: Object, default: null },
})

defineEmits(['favorite'])

const router = useRouter()

function goDetail() {
  if (item?.id) {
    router.push(`/heritages/${item.id}`)
  }
}

function levelClass(category) {
  if (!category) return 'default'
  if (category.includes('国家')) return 'national'
  if (category.includes('省级')) return 'province'
  if (category.includes('市级')) return 'city'
  return 'default'
}
</script>

<style scoped>
.heritage-card {
  position: relative;
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-accent);
  padding: var(--space-md);
  cursor: pointer;
  transition: transform var(--duration-base) var(--ease-out),
              box-shadow var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-sm);
}

.heritage-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--brand-amber);
}

/* ── 印章角标 — 右上角红色篆刻印章 ── */
.heritage-card__seal {
  position: absolute;
  top: -6px;
  right: var(--space-md);
  width: 40px;
  height: 40px;
  border: 2px solid var(--brand-red);
  border-radius: 4px;
  background: oklch(0.53 0.22 25 / 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  transform: rotate(8deg);
  z-index: 1;
  box-shadow: 0 1px 4px oklch(0.53 0.22 25 / 0.15);
}

.heritage-card__seal-text {
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: var(--fw-black);
  color: var(--brand-red);
  letter-spacing: 0.15em;
  writing-mode: vertical-rl;
  line-height: 1;
  transform: rotate(0deg);
}

/* ── Inner content area ── */
.heritage-card__inner {
  display: flex;
  gap: var(--space-md);
}

.heritage-card__media {
  flex-shrink: 0;
  width: 120px;
  height: 160px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--bg-surface-alt);
  display: flex;
  align-items: center;
  justify-content: center;
}

.heritage-card__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.heritage-card__placeholder {
  font-size: 40px;
  opacity: 0.5;
}

.heritage-card__content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.heritage-card__name {
  font-size: var(--fs-lg);
  font-weight: var(--fw-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-sm);
  line-height: var(--lh-tight);
}

/* ── Tags ── */
.heritage-card__tags {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  flex-wrap: wrap;
  margin-bottom: var(--space-sm);
}

.heritage-card__level {
  font-size: var(--fs-xs);
  font-weight: var(--fw-semibold);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.heritage-card__level--national {
  background: var(--status-error-bg);
  color: var(--status-error);
}

.heritage-card__level--province {
  background: var(--status-warning-bg);
  color: oklch(0.50 0.12 80);
}

.heritage-card__level--city {
  background: var(--status-success-bg);
  color: var(--status-success);
}

.heritage-card__level--default {
  background: var(--status-info-bg);
  color: var(--status-info);
}

.heritage-card__type {
  font-size: var(--fs-xs);
  color: var(--text-secondary);
}

.heritage-card__region {
  font-size: var(--fs-xs);
  color: var(--text-secondary);
}

/* ── Description ── */
.heritage-card__desc {
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  line-height: var(--lh-base);
  margin: 0 0 var(--space-sm);
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Inheritor ── */
.heritage-card__inheritor {
  font-size: var(--fs-xs);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 4px;
  padding-top: var(--space-xs);
  border-top: 1px dashed var(--border-light);
}

.heritage-card__inheritor-icon {
  font-size: var(--fs-sm);
}

/* ── Actions ── */
.heritage-card__actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-light);
}

.heritage-card__btn {
  padding: var(--space-xs) var(--space-lg);
  border-radius: var(--radius-sm);
  font-size: var(--fs-sm);
  font-family: var(--font-body);
  font-weight: var(--fw-medium);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  border: 1px solid transparent;
}

.heritage-card__btn--primary {
  background: var(--brand-red);
  color: var(--text-inverse);
  border-color: var(--brand-red);
}

.heritage-card__btn--primary:hover {
  background: var(--brand-red-hover);
  border-color: var(--brand-red-hover);
}

.heritage-card__btn--ghost {
  background: transparent;
  color: var(--text-secondary);
  border-color: var(--border-default);
}

.heritage-card__btn--ghost:hover {
  color: var(--brand-red);
  border-color: var(--brand-red);
  background: var(--brand-red-light);
}

/* ── Responsive ── */
@media (max-width: 480px) {
  .heritage-card__inner {
    flex-direction: column;
  }

  .heritage-card__media {
    width: 100%;
    height: 160px;
  }
}

/* ── Reduced motion ── */
@media (prefers-reduced-motion: reduce) {
  .heritage-card:hover {
    transform: none;
  }
}
</style>
