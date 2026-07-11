<template>
  <div class="community-page">
    <BackButton />
    <div class="page-header">
      <div>
        <h1 class="display-text--section">💬 社区推荐</h1>
        <p>发现潮汕好去处，分享你的探索故事</p>
        <div class="section-divider section-divider--left"></div>
      </div>
      <el-button type="primary" :icon="Edit" @click="$router.push('/community/create')">
        发布动态
      </el-button>
    </div>

    <!-- 分类 + 排序 -->
    <div class="feed-toolbar">
      <div class="type-tabs">
        <button
          v-for="t in postTypes"
          :key="t.value"
          :class="['tea-pill', { active: activeType === t.value }]"
          @click="activeType = t.value; fetchPosts()"
        >{{ t.label }}</button>
      </div>
      <el-select v-model="sort" style="width:140px" @change="fetchPosts">
        <el-option label="🕐 最新" value="created_at" />
        <el-option label="🔥 最热" value="like_count" />
        <el-option label="💬 最多评论" value="comment_count" />
      </el-select>
    </div>

    <!-- 加载 -->
    <LoadingSkeleton v-if="loading" type="card" :count="4" />

    <!-- 空 -->
    <EmptyState v-else-if="!loading && posts.length === 0" description="暂无动态，快来发布第一条吧！">
      <template #action>
        <el-button type="primary" @click="$router.push('/community/create')">发布动态</el-button>
      </template>
    </EmptyState>

    <!-- 社区动态瀑布流 -->
    <div v-else class="masonry-container">
      <article
        v-for="post in posts"
        :key="post.id"
        :class="['post-card', 'post-card--' + post.post_type]"
        @click="$router.push(`/community/post/${post.id}`)"
      >
        <div class="post-header">
          <el-avatar :size="40" :src="post.user_avatar">
            {{ post.user_nickname?.[0] || 'U' }}
          </el-avatar>
          <div class="post-author">
            <span class="author-name">{{ post.user_nickname || '匿名用户' }}</span>
            <span class="post-time">{{ post.created_at?.slice(0, 10) }}</span>
          </div>
          <el-tag size="small">{{ postTypeLabel(post.post_type) }}</el-tag>
        </div>

        <h3 class="post-title">{{ post.title }}</h3>
        <p class="post-excerpt">{{ post.content?.slice(0, 200) }}</p>

        <!-- 图片预览 -->
        <div v-if="post.images?.length" class="post-images">
          <el-image
            v-for="(img, i) in post.images.slice(0, 3)"
            :key="i"
            :src="img"
            fit="cover"
            class="post-img"
            lazy
          />
        </div>

        <!-- 标签 -->
        <div v-if="post.tags?.length" class="post-tags">
          <el-tag v-for="tag in post.tags" :key="tag" size="small" round>{{ tag }}</el-tag>
        </div>

        <div class="post-actions">
          <span class="action-item">
            <el-icon><component :is="post.is_liked ? 'StarFilled' : 'Star'" /></el-icon>
            {{ post.like_count || 0 }}
          </span>
          <span class="action-item">
            <el-icon><ChatDotRound /></el-icon>
            {{ post.comment_count || 0 }}
          </span>
          <span class="action-item">
            <el-icon><View /></el-icon>
            {{ post.view_count || 0 }}
          </span>
        </div>
      </article>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-wrap">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        background
        @current-change="fetchPosts"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Edit, ChatDotRound, View } from '@element-plus/icons-vue'
import { getPosts } from '@/api'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BackButton from '@/components/common/BackButton.vue'

const loading = ref(true)
const posts = ref([])
const activeType = ref('')
const sort = ref('created_at')
const page = ref(1)
const pageSize = 20
const total = ref(0)

const postTypes = [
  { value: '', label: '全部' },
  { value: 'recommend', label: '👍 推荐' },
  { value: 'challenge', label: '🎯 挑战' },
  { value: 'social', label: '👋 社交' },
  { value: 'study', label: '📚 文化' },
]

function postTypeLabel(type) {
  return { recommend: '推荐', challenge: '挑战', social: '社交', study: '文化' }[type] || type
}

async function fetchPosts() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize, sort: sort.value }
    if (activeType.value) params.post_type = activeType.value

    const data = await getPosts(params)
    posts.value = data.items || []
    total.value = data.total || 0
  } catch {
    posts.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchPosts())
</script>

<style scoped>
.community-page {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-md);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-xl);
}

.page-header h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-xs); }
.page-header p { color: var(--muted); margin: 0 0 var(--space-md); font-size: var(--fs-sm); }

.feed-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-xl);
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-surface-alt);
  border-radius: var(--radius-lg);
}

.type-tabs { display: flex; gap: var(--space-sm); }

/* tea-pill & masonry styles from global.css */

.post-card {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-xl);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

/* 类型左边框色标 — 推荐=红、挑战=amber、文化=jade */
.post-card--recommend { border-left: 4px solid var(--brand-red); }
.post-card--challenge { border-left: 4px solid var(--brand-amber); }
.post-card--study { border-left: 4px solid var(--brand-jade); }

.post-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px oklch(0 0 0 / 0.08);
}

.post-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.post-author { flex: 1; }
.author-name { display: block; font-size: var(--fs-sm); font-weight: 600; color: var(--ink); }
.post-time { font-size: var(--fs-xs); color: var(--muted); }

.post-title {
  font-size: var(--fs-lg);
  color: var(--ink);
  margin: 0 0 var(--space-sm);
}

.post-excerpt {
  color: var(--muted);
  font-size: var(--fs-sm);
  line-height: 1.6;
  margin: 0 0 var(--space-md);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-images {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.post-img {
  width: 120px;
  height: 90px;
  border-radius: 8px;
}

.post-tags {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.post-actions {
  display: flex;
  gap: var(--space-xl);
  padding-top: var(--space-md);
  border-top: 1px solid oklch(0 0 0 / 0.04);
}

.action-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--muted);
  font-size: var(--fs-sm);
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: var(--space-2xl);
}

@media (max-width: 640px) {
  .page-header { flex-direction: column; gap: var(--space-md); align-items: flex-start; }
  .feed-toolbar { flex-direction: column; gap: var(--space-md); align-items: flex-start; }
  .type-tabs { flex-wrap: wrap; }
  .post-img { width: 80px; height: 60px; }
}
</style>
