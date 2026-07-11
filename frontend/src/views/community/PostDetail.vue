<template>
  <div class="post-detail-page">
<<<<<<< HEAD
=======
    <BackButton />
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    <LoadingSkeleton v-if="loading" type="detail" />

    <div v-else-if="error" class="error-state">
      <el-result icon="error" :title="error">
        <template #extra>
          <el-button type="primary" @click="fetchPost">重新加载</el-button>
          <el-button @click="$router.push('/community')">返回社区</el-button>
        </template>
      </el-result>
    </div>

    <template v-else-if="post">
      <!-- 动态内容 -->
      <article class="post-full">
        <div class="post-header">
          <el-avatar :size="48" :src="post.user_avatar">
            {{ post.user_nickname?.[0] || 'U' }}
          </el-avatar>
          <div class="author-info">
            <strong>{{ post.user_nickname || '匿名用户' }}</strong>
            <span>{{ post.created_at?.slice(0, 10) }}</span>
          </div>
          <el-tag>{{ postTypeLabel(post.post_type) }}</el-tag>
        </div>

        <h1 class="display-text--section">{{ post.title }}</h1>
        <div class="post-body">{{ post.content }}</div>

        <div v-if="post.images?.length" class="post-images">
          <el-image
            v-for="(img, i) in post.images"
            :key="i"
            :src="img"
            fit="cover"
            class="detail-img"
<<<<<<< HEAD
            @click="viewer.open(post.images, i)"
          />
        </div>
        <ImageViewer ref="viewer" />
=======
            :preview-src-list="post.images"
            :initial-index="i"
          />
        </div>
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22

        <div v-if="post.tags?.length" class="post-tags">
          <el-tag v-for="tag in post.tags" :key="tag" round>{{ tag }}</el-tag>
        </div>

        <div class="post-stats">
          <el-button
            :type="post.is_liked ? 'danger' : 'default'"
            :icon="post.is_liked ? StarFilled : Star"
            round
            @click="toggleLike"
          >
            {{ post.like_count || 0 }}
          </el-button>
          <span>👀 {{ post.view_count || 0 }} 浏览</span>
          <span>💬 {{ post.comment_count || 0 }} 评论</span>
        </div>
      </article>

      <!-- 评论列表 -->
      <section class="comments-section">
        <div class="section-divider section-divider--left"></div>
        <h2>评论 ({{ comments.length }})</h2>

        <div class="comment-form">
          <el-input
            v-model="commentText"
            type="textarea"
            :rows="3"
            placeholder="写下你的评论..."
            maxlength="2000"
            show-word-limit
          />
          <div class="comment-form-actions">
            <el-button
              type="primary"
              :disabled="!commentText.trim()"
              :loading="submitting"
              @click="submitComment"
            >发表评论</el-button>
          </div>
        </div>

        <div v-if="comments.length === 0" class="no-comments">
          <p>暂无评论，来发表第一条吧</p>
        </div>

        <div v-else class="comment-list">
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <el-avatar :size="36" :src="c.user_avatar">
              {{ c.user_nickname?.[0] || 'U' }}
            </el-avatar>
            <div class="comment-body">
              <div class="comment-top">
                <strong>{{ c.user_nickname || '匿名' }}</strong>
                <span class="comment-time">{{ c.created_at?.slice(0, 16) }}</span>
              </div>
              <p>{{ c.content }}</p>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'
import { getPostDetail, getComments, createComment, likePost, unlikePost } from '@/api'
<<<<<<< HEAD
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ImageViewer from '@/components/common/ImageViewer.vue'

const route = useRoute()

const viewer = ref(null)
=======
import BackButton from '@/components/common/BackButton.vue'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'

const route = useRoute()

>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
const post = ref(null)
const comments = ref([])
const commentText = ref('')
const loading = ref(true)
const submitting = ref(false)
const error = ref('')

function postTypeLabel(type) {
  return { recommend: '推荐', challenge: '挑战', social: '社交', study: '文化' }[type] || type
}

async function fetchPost() {
  loading.value = true
  error.value = ''
  try {
    const id = route.params.id
    post.value = await getPostDetail(id)
    const commentData = await getComments(id, { page_size: 50 })
    comments.value = commentData.items || []
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function toggleLike() {
  try {
    if (post.value.is_liked) {
      await unlikePost(post.value.id)
      post.value.is_liked = false
      post.value.like_count = Math.max(0, (post.value.like_count || 0) - 1)
    } else {
      await likePost(post.value.id)
      post.value.is_liked = true
      post.value.like_count = (post.value.like_count || 0) + 1
    }
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

async function submitComment() {
  if (!commentText.value.trim()) return
  submitting.value = true
  try {
    await createComment(post.value.id, { content: commentText.value })
    ElMessage.success('评论成功')
    commentText.value = ''
    // 重新获取评论
    const commentData = await getComments(post.value.id, { page_size: 50 })
    comments.value = commentData.items || []
    post.value.comment_count = (post.value.comment_count || 0) + 1
  } catch (e) {
    ElMessage.error(e.message || '评论失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => fetchPost())
</script>

<style scoped>
.post-detail-page { max-width: 800px; margin: 0 auto; padding: var(--space-2xl) var(--space-md); }

.post-full {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-2xl);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
  margin-bottom: var(--space-2xl);
}

.post-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xl);
}

.author-info { flex: 1; }
.author-info strong { display: block; color: var(--ink); }
.author-info span { font-size: var(--fs-xs); color: var(--muted); }

.post-full h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-lg); }

.post-body {
  color: var(--ink);
  font-size: var(--fs-base);
  line-height: 1.9;
  white-space: pre-wrap;
  margin-bottom: var(--space-lg);
}

.post-images { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--space-sm); margin-bottom: var(--space-lg); }
.detail-img { width: 100%; height: 200px; border-radius: 8px; cursor: pointer; }

.post-tags { display: flex; gap: var(--space-xs); margin-bottom: var(--space-lg); flex-wrap: wrap; }

.post-stats {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid oklch(0 0 0 / 0.06);
  color: var(--muted);
  font-size: var(--fs-sm);
}

/* Comments */
.comments-section { padding: 0; }

.comments-section .section-divider {
  margin-bottom: var(--space-lg);
}

.comments-section h2 { font-size: var(--fs-xl); color: var(--ink); margin: 0 0 var(--space-lg); }

.comment-form { margin-bottom: var(--space-xl); }
.comment-form-actions { display: flex; justify-content: flex-end; margin-top: var(--space-sm); }

.no-comments { text-align: center; padding: var(--space-2xl); color: var(--muted); }

.comment-list { display: flex; flex-direction: column; gap: var(--space-md); }

.comment-item { display: flex; gap: var(--space-md); padding: var(--space-md); background: var(--surface); border-radius: 10px; }

.comment-body { flex: 1; }
.comment-top { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: 4px; }
.comment-top strong { color: var(--ink); font-size: var(--fs-sm); }
.comment-time { color: var(--muted); font-size: var(--fs-xs); }
.comment-body p { color: var(--ink); font-size: var(--fs-sm); line-height: 1.6; margin: 0; }

.error-state { padding: var(--space-3xl); }
</style>
