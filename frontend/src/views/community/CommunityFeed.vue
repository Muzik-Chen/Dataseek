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
      <SortDropdown v-model="sort" :options="sortOptions" width="150px" @change="fetchPosts" />
    </div>

    <!-- 加载 -->
    <LoadingSkeleton v-if="loading" type="card" :count="4" />

    <!-- 空 -->
    <EmptyState v-else-if="!loading && posts.length === 0" description="暂无动态，快来发布第一条吧！">
      <template #action>
        <el-button type="primary" @click="$router.push('/community/create')">发布动态</el-button>
      </template>
    </EmptyState>

    <!-- 社区动态列表 -->
    <div v-else class="post-grid">
      <PostCard
        v-for="post in posts"
        :key="post.id"
        :post="post"
        @click="goDetail"
      />
    </div>

    <!-- 分页 -->
    <Pagination
      v-model:page="page"
      :total="total"
      :page-size="pageSize"
      @change="fetchPosts"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Edit } from '@element-plus/icons-vue'
import { getPosts } from '@/api'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PostCard from '@/components/business/PostCard.vue'
import Pagination from '@/components/common/Pagination.vue'
import SortDropdown from '@/components/common/SortDropdown.vue'
import BackButton from '@/components/common/BackButton.vue'

const router = useRouter()

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

const sortOptions = [
  { label: '🕐 最新', value: 'created_at' },
  { label: '🔥 最热', value: 'like_count' },
  { label: '💬 最多评论', value: 'comment_count' },
]

function goDetail(postId) {
  router.push(`/community/post/${postId}`)
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

.post-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

@media (max-width: 640px) {
  .page-header { flex-direction: column; gap: var(--space-md); align-items: flex-start; }
  .feed-toolbar { flex-direction: column; gap: var(--space-md); align-items: flex-start; }
  .type-tabs { flex-wrap: wrap; }
}
</style>
