<template>
  <!-- 侨批印记 -->
  <article class="post-card" @click="$emit('click', post.id)">
    <!-- 封面图 + 邮戳 -->
    <div class="post-card__cover">
      <img
        v-if="post.images && post.images.length > 0"
        :src="post.images[0]"
        :alt="post.title"
        class="post-card__img"
        loading="lazy"
      />
      <div v-else class="post-card__img-placeholder">
        <span>📮</span>
      </div>

      <!-- 邮戳标签 — 左下角叠印 -->
      <span v-if="post.post_type" class="post-card__stamp">
        {{ stampLabel(post.post_type) }}
      </span>
    </div>

    <div class="post-card__body">
      <h3 class="post-card__title">{{ post.title }}</h3>
      <p class="post-card__excerpt">{{ excerpt }}</p>

      <div v-if="post.tags && post.tags.length > 0" class="post-card__tags">
        <span v-for="tag in post.tags.slice(0, 3)" :key="tag" class="post-card__tag">#{{ tag }}</span>
      </div>

      <div class="post-card__meta">
        <div class="post-card__stats">
          <span class="post-card__stat">
            <span class="post-card__stat-icon">♥</span>
            {{ post.like_count || 0 }}
          </span>
          <span class="post-card__stat">
            <span class="post-card__stat-icon">💬</span>
            {{ post.comment_count || 0 }}
          </span>
        </div>
        <time class="post-card__time" :datetime="post.created_at">{{ timeAgo }}</time>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  post: { type: Object, required: true },
})

defineEmits(['click'])

const excerpt = computed(() => {
  const text = props.post.content || ''
  return text.length > 80 ? text.slice(0, 80) + '...' : text
})

const timeAgo = computed(() => {
  const created = new Date(props.post.created_at)
  const now = new Date()
  const diff = Math.floor((now - created) / 1000)

  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 2592000) return `${Math.floor(diff / 86400)}天前`
  return created.toLocaleDateString('zh-CN')
})

function stampLabel(type) {
  const map = { recommend: '推荐', challenge: '挑战', social: '社交', study: '文化' }
  return map[type] || type
}
</script>

<style scoped>
/* ── 侨批卡片 — 老信件质感 ── */
.post-card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--duration-base) var(--ease-out),
              box-shadow var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
}

.post-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}

/* ── Cover image + postmark ── */
.post-card__cover {
  position: relative;
  height: 180px;
  overflow: hidden;
  background: var(--bg-surface-alt);
}

.post-card__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-slow) var(--ease-out);
}

.post-card:hover .post-card__img {
  transform: scale(1.04);
}

.post-card__img-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  opacity: 0.5;
}

/* ── 邮戳印记 — 左下角叠印 ── */
.post-card__stamp {
  position: absolute;
  bottom: 12px;
  left: 12px;
  padding: 4px 12px;
  background: oklch(0.15 0.01 25 / 0.72);
  backdrop-filter: blur(6px);
  color: oklch(1 0 0);
  font-size: var(--fs-xs);
  font-weight: var(--fw-semibold);
  font-family: var(--font-display);
  letter-spacing: 0.08em;
  border-radius: 3px;
  border: 1px solid oklch(1 0 0 / 0.2);
  text-transform: uppercase;
}

/* ── Body ── */
.post-card__body {
  padding: var(--space-md);
}

.post-card__title {
  font-size: var(--fs-lg);
  font-weight: var(--fw-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-sm);
  line-height: var(--lh-tight);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-card__excerpt {
  font-size: var(--fs-sm);
  color: var(--text-secondary);
  line-height: var(--lh-base);
  margin: 0 0 var(--space-sm);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Tags ── */
.post-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
}

.post-card__tag {
  font-size: var(--fs-xs);
  color: var(--brand-amber);
  background: var(--brand-amber-light);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

/* ── Meta ── */
.post-card__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border-light);
}

.post-card__stats {
  display: flex;
  gap: var(--space-lg);
}

.post-card__stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--fs-sm);
  color: var(--text-secondary);
}

.post-card__stat-icon {
  font-size: var(--fs-sm);
}

.post-card__time {
  font-size: var(--fs-xs);
  color: var(--text-tertiary);
}

/* ── Reduced motion ── */
@media (prefers-reduced-motion: reduce) {
  .post-card:hover {
    transform: none;
  }

  .post-card:hover .post-card__img {
    transform: none;
  }
}
</style>
