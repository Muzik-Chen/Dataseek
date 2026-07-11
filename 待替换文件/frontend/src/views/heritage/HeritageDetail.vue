<template>
  <div class="heritage-detail-page">
    <LoadingSkeleton v-if="loading" type="detail" />

    <div v-else-if="error" class="error-state">
      <el-result icon="error" :title="error" sub-title="请重试">
        <template #extra>
          <el-button type="primary" @click="fetchDetail">重新加载</el-button>
          <el-button @click="$router.back()">返回</el-button>
        </template>
      </el-result>
    </div>

    <template v-else-if="heritage">
      <!-- 头图 -->
      <div class="hero-image" @click="heritage.image_url && viewer.open([heritage.image_url])">
        <el-image v-if="heritage.image_url" :src="heritage.image_url" fit="cover" class="cover-img" />
        <div v-else class="cover-placeholder">🎭</div>
      </div>
      <ImageViewer ref="viewer" />

      <div class="content-wrap">
        <div class="main-info">
          <div class="title-row">
            <h1 class="display-text--section">{{ heritage.name }}</h1>
            <el-button
              :type="isFavorited ? 'danger' : 'default'"
              :icon="isFavorited ? StarFilled : Star"
              round
              @click="toggleFavorite"
            >
              {{ isFavorited ? '已收藏' : '收藏' }}
            </el-button>
          </div>

          <div class="meta-tags">
            <el-tag :type="levelTagType" size="large">{{ heritage.category }}</el-tag>
            <el-tag type="info" size="large">{{ heritage.type }}</el-tag>
            <span class="region">📍 {{ heritage.region }}</span>
            <span class="views">👀 {{ heritage.view_count }} 次浏览</span>
          </div>

          <!-- 介绍 -->
          <section class="content-section">
            <h2>📖 项目介绍</h2>
            <p>{{ heritage.description || '暂无详细介绍' }}</p>
          </section>

          <!-- 传承人 -->
          <section v-if="heritage.inheritor" class="content-section">
            <h2>🧑‍🎓 传承人</h2>
            <p>{{ heritage.inheritor }}</p>
          </section>

          <!-- 视频 -->
          <section v-if="heritage.video_url" class="content-section">
            <h2>🎬 视频资料</h2>
            <div class="video-wrap">
              <video :src="heritage.video_url" controls class="heritage-video">
                您的浏览器不支持视频播放
              </video>
            </div>
          </section>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'
import { getHeritageDetail, addFavorite, removeFavorite, checkFavorite } from '@/api'
import { useUserStore } from '@/stores/user'
import LoadingSkeleton from '@/components/common/LoadingSkeleton.vue'
import ImageViewer from '@/components/common/ImageViewer.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const viewer = ref(null)
const heritage = ref(null)
const loading = ref(true)
const error = ref('')
const isFavorited = ref(false)
const favoriteId = ref(null)

const levelTagType = {
  '国家级': 'danger',
  '省级': 'primary',
  '市级': 'success',
}

async function fetchDetail() {
  loading.value = true
  error.value = ''
  try {
    heritage.value = await getHeritageDetail(route.params.id)
    document.title = `${heritage.value.name} - 潮汕文化宣传平台`
    // 登录后检查收藏状态
    if (userStore.isLoggedIn) {
      await checkFavoriteStatus()
    }
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function checkFavoriteStatus() {
  try {
    const res = await checkFavorite({ item_type: 'heritage', item_id: heritage.value.id })
    isFavorited.value = res.is_favorited
    favoriteId.value = res.favorite_id
  } catch {
    // 未登录或检查失败时保持默认状态
  }
}

async function toggleFavorite() {
  // 未登录时引导登录
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再收藏')
    router.push('/login')
    return
  }

  try {
    if (isFavorited.value) {
      await removeFavorite(favoriteId.value)
      isFavorited.value = false
      favoriteId.value = null
      ElMessage.success('已取消收藏')
    } else {
      const res = await addFavorite({ item_type: 'heritage', item_id: heritage.value.id })
      isFavorited.value = true
      favoriteId.value = res.id
      ElMessage.success('已收藏')
    }
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

onMounted(() => fetchDetail())
</script>

<style scoped>
.heritage-detail-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 var(--space-md) var(--space-3xl);
}

.hero-image {
  position: relative;
  width: 100%;
  height: 400px;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: var(--space-2xl);
}

/* 底部渐变叠层 */
.hero-image::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: var(--gradient-card-overlay);
  pointer-events: none;
  z-index: 1;
}

.cover-img { width: 100%; height: 100%; }
.cover-placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface); font-size: 64px;
}

.content-wrap {
  max-width: 720px;
  margin: 0 auto;
}

.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-lg);
  margin-bottom: var(--space-md);
}

.title-row h1 {
  font-size: var(--fs-3xl);
  color: var(--ink);
  margin: 0;
}

.meta-tags {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-2xl);
  padding-bottom: var(--space-xl);
  border-bottom: 1px solid oklch(0 0 0 / 0.08);
}

.region, .views {
  color: var(--muted);
  font-size: var(--fs-sm);
}

.content-section {
  margin-bottom: var(--space-2xl);
}

.content-section h2 {
  font-size: var(--fs-xl);
  color: var(--ink);
  margin: 0 0 var(--space-md);
}

.content-section p {
  color: var(--muted);
  line-height: 1.9;
  font-size: var(--fs-base);
  margin: 0;
}

.video-wrap {
  border-radius: 12px;
  overflow: hidden;
}

.heritage-video {
  width: 100%;
  border-radius: 12px;
}

.error-state {
  padding: var(--space-3xl);
}

@media (max-width: 640px) {
  .hero-image {
    height: 240px;
    border-radius: 0;
    margin: 0 calc(-1 * var(--space-md)) var(--space-xl);
  }

  .title-row { flex-direction: column; }
  .title-row h1 { font-size: var(--fs-2xl); }
}
</style>
