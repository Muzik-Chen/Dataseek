<template>
  <!-- Single food card mode (listing pages) — 朱红匾额 -->
  <article
    v-if="food"
    class="food-card food-card--single"
    @click="goDetail(food)"
  >
    <!-- 门匾: 朱红条幅 -->
    <div class="food-card__plaque">
      <span class="food-card__plaque-label">{{ food.shop_name || food.category_name || '美食推荐' }}</span>
    </div>

    <div class="food-card__image">
      <img v-if="food.image_url" :src="food.image_url" :alt="food.name" loading="lazy" />
      <span v-else class="food-card__placeholder">🍲</span>
    </div>

    <div class="food-card__body">
      <h3 class="food-card__name">{{ food.name }}</h3>
      <div class="food-card__meta">
        <span class="food-card__score">⭐ {{ (food.score ?? food.rating ?? 4.5).toFixed(1) }}</span>
        <span v-if="food.price_range" class="food-card__price">{{ food.price_range }}</span>
      </div>
      <p v-if="food.reason || food.description" class="food-card__desc">
        {{ food.reason || (typeof food.description === 'string' ? food.description.slice(0, 80) : '') }}
      </p>
    </div>

    <button class="food-card__fav" @click.stop="$emit('favorite', food)" title="收藏">
      <span class="food-card__fav-icon">♥</span>
    </button>
  </article>

  <!-- Collection mode (ChatWidget horizontal scroll) — 朱红匾额包裹 -->
  <div v-else-if="items.length" class="food-card food-card--collection">
    <div class="food-card__plaque food-card__plaque--collection">
      <span>🍲 美食推荐</span>
    </div>
    <p v-if="summary" class="food-card__summary">{{ summary }}</p>
    <div class="food-card__scroll">
      <div
        v-for="item in items"
        :key="item.id || item.food_id"
        class="food-card__item"
        @click="goDetail(item)"
      >
        <div class="food-card__item-img">
          <img v-if="item.image_url" :src="item.image_url" :alt="item.name" loading="lazy" />
          <span v-else class="food-card__placeholder">🍲</span>
        </div>
        <div class="food-card__item-info">
          <strong>{{ item.name }}</strong>
          <div class="food-card__meta">
            <span class="food-card__score">⭐ {{ (item.score ?? item.rating ?? 4.5).toFixed(1) }}</span>
            <span v-if="item.price_range" class="food-card__price">{{ item.price_range }}</span>
          </div>
          <p class="food-card__desc">{{ item.reason || '' }}</p>
        </div>
        <button class="food-card__fav" @click.stop="$emit('favorite', item)" title="收藏">
          <span class="food-card__fav-icon">♥</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

defineProps({
  food: { type: Object, default: null },
  items: { type: Array, default: () => [] },
  summary: { type: String, default: '' },
})

defineEmits(['favorite'])

const router = useRouter()

function goDetail(item) {
  const id = item.id || item.food_id
  if (id) router.push(`/foods/${id}`)
}
</script>

<style scoped>
/* ── Base card ── */
.food-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: transform var(--duration-base) var(--ease-out),
              box-shadow var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-sm);
}

.food-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* ── 门匾: 朱红条幅 ── */
.food-card__plaque {
  background: var(--brand-red-muted);
  border-bottom: 2px solid var(--brand-red);
  padding: var(--space-sm) var(--space-md);
}

.food-card__plaque-label {
  font-family: var(--font-display);
  font-size: var(--fs-sm);
  font-weight: var(--fw-semibold);
  color: var(--brand-red);
  letter-spacing: 0.04em;
}

.food-card__plaque--collection {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-md);
  font-weight: var(--fw-semibold);
  color: var(--brand-red);
  font-family: var(--font-display);
  font-size: var(--fs-sm);
  letter-spacing: 0.04em;
}

/* ── Single card mode ── */
.food-card--single {
  cursor: pointer;
  position: relative;
}

.food-card--single .food-card__image {
  width: 100%;
  height: 180px;
  overflow: hidden;
  background: var(--bg-surface-alt);
  display: flex;
  align-items: center;
  justify-content: center;
}

.food-card--single .food-card__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.food-card__placeholder {
  font-size: 48px;
  opacity: 0.6;
}

.food-card__body {
  padding: var(--space-md);
}

.food-card__name {
  font-size: var(--fs-lg);
  font-weight: var(--fw-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-xs);
  line-height: var(--lh-tight);
}

.food-card__meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.food-card__score {
  color: var(--brand-amber);
  font-size: var(--fs-sm);
  font-weight: var(--fw-medium);
}

.food-card__price {
  color: var(--brand-red);
  font-size: var(--fs-xs);
  font-weight: var(--fw-semibold);
  background: var(--brand-red-light);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.food-card__desc {
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  margin: 0;
  line-height: var(--lh-base);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Favorite button ── */
.food-card__fav {
  position: absolute;
  top: 48px;
  right: var(--space-sm);
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  border: none;
  background: oklch(1 0 0 / 0.85);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-spring),
              background var(--duration-fast);
  box-shadow: 0 1px 4px oklch(0 0 0 / 0.1);
}

.food-card__fav:hover {
  transform: scale(1.15);
  background: var(--brand-red-light);
}

.food-card__fav-icon {
  color: var(--brand-red);
  font-size: var(--fs-sm);
  line-height: 1;
}

/* ── Collection mode ── */
.food-card--collection {
  padding-bottom: var(--space-md);
}

.food-card__summary {
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  margin: 0;
  padding: var(--space-sm) var(--space-md) 0;
}

.food-card__scroll {
  display: flex;
  gap: var(--space-sm);
  overflow-x: auto;
  padding: var(--space-md);
  scroll-snap-type: x mandatory;
}

.food-card__item {
  flex: 0 0 200px;
  background: var(--bg-page);
  border-radius: var(--radius-md);
  padding: var(--space-sm);
  cursor: pointer;
  position: relative;
  scroll-snap-align: start;
  transition: box-shadow var(--duration-fast);
  border: 1px solid var(--border-light);
}

.food-card__item:hover {
  box-shadow: var(--shadow-md);
}

.food-card__item-img {
  width: 100%;
  height: 100px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-bottom: var(--space-sm);
  background: var(--bg-surface-alt);
  display: flex;
  align-items: center;
  justify-content: center;
}

.food-card__item-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.food-card__item-info strong {
  display: block;
  font-size: var(--fs-sm);
  color: var(--text-primary);
  margin-bottom: 4px;
}

/* ── Reduced motion ── */
@media (prefers-reduced-motion: reduce) {
  .food-card:hover {
    transform: none;
  }
}
</style>
