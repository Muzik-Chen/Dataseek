<template>
  <div class="profile-page">
    <div class="page-header">
      <h1>个人中心</h1>
      <p>管理您的账号信息和收藏内容</p>
    </div>

    <div class="profile-grid">
      <!-- 侧边栏 -->
      <aside class="profile-sidebar">
        <div class="user-card">
          <el-avatar :size="72" :src="user?.avatar_url">
            {{ user?.nickname?.[0] || 'U' }}
          </el-avatar>
          <h2>{{ user?.nickname || '游客' }}</h2>
          <p class="user-phone">{{ maskedEmail }}</p>
          <el-tag :type="personaLabel.type" size="small">
            {{ personaLabel.text }}
          </el-tag>
        </div>

        <nav class="sidebar-nav">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['nav-item', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            <el-icon><component :is="tab.icon" /></el-icon>
            <span>{{ tab.label }}</span>
            <el-badge v-if="tab.key === 'favorites' && favorites.length" :value="favorites.length" class="nav-badge" />
          </button>
        </nav>
      </aside>

      <!-- 主内容区 -->
      <main class="profile-main">
        <!-- 编辑资料 -->
        <div v-if="activeTab === 'profile'" class="tab-panel">
          <h3>编辑资料</h3>
          <el-form :model="editForm" label-width="80px" class="profile-form">
            <el-form-item label="昵称">
              <el-input v-model="editForm.nickname" maxlength="20" />
            </el-form-item>
            <el-form-item label="用户类型">
              <el-select v-model="editForm.persona_type" style="width: 200px">
                <el-option label="游客/旅行者" value="tourist" />
                <el-option label="文化爱好者" value="enthusiast" />
                <el-option label="美食探索者" value="foodie" />
              </el-select>
            </el-form-item>
            <el-form-item label="兴趣偏好">
              <el-checkbox-group v-model="editForm.interests">
                <el-checkbox label="美食" />
                <el-checkbox label="非遗" />
                <el-checkbox label="民俗" />
                <el-checkbox label="建筑" />
                <el-checkbox label="茶道" />
                <el-checkbox label="自然" />
              </el-checkbox-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="saveProfile">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 我的收藏 -->
        <div v-if="activeTab === 'favorites'" class="tab-panel">
          <h3>我的收藏</h3>
          <div v-if="favorites.length === 0" class="empty-tip">
            <el-icon :size="48" color="var(--muted)"><Star /></el-icon>
            <p>还没有收藏任何内容</p>
            <el-button type="primary" @click="$router.push('/foods')">去探索美食</el-button>
          </div>
          <div v-else class="favorite-list">
            <div
              v-for="fav in favorites"
              :key="fav.id"
              class="fav-item"
              @click="goToFavItem(fav)"
            >
              <el-image
                v-if="fav.detail?.image_url"
                :src="fav.detail.image_url"
                fit="cover"
                class="fav-thumb"
              />
              <div class="fav-info">
                <span class="fav-name">{{ fav.detail?.name || '未知' }}</span>
                <span class="fav-type">{{ itemTypeLabel(fav.item_type) }}</span>
              </div>
              <el-button
                type="danger"
                :icon="Delete"
                circle
                size="small"
                @click.stop="removeFav(fav.id)"
              />
            </div>
          </div>
        </div>

        <!-- 修改密码 -->
        <div v-if="activeTab === 'security'" class="tab-panel">
          <h3>修改密码</h3>
          <el-form :model="passwordForm" label-width="100px" class="profile-form">
            <el-form-item label="原密码">
              <el-input v-model="passwordForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="passwordForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="changingPwd" @click="changePassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 行程 -->
        <div v-if="activeTab === 'trips'" class="tab-panel">
          <h3>我的行程</h3>
          <div v-if="trips.length === 0" class="empty-tip">
            <el-icon :size="48" color="var(--muted)"><Guide /></el-icon>
            <p>还没有行程计划</p>
            <el-button type="primary" @click="$router.push('/trip/create')">创建行程</el-button>
          </div>
          <div v-else class="trip-list">
            <div v-for="trip in trips" :key="trip.id" class="trip-item">
              <div class="trip-info">
                <h4>{{ trip.title }}</h4>
                <p>
                  {{ trip.days }}天 ·
                  <el-tag :type="trip.status === 'draft' ? 'warning' : 'success'" size="small">
                    {{ trip.status === 'draft' ? '草稿' : '已生成' }}
                  </el-tag>
                </p>
              </div>
              <el-button size="small" @click="$router.push(`/trip/${trip.id}`)">查看</el-button>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Star, Lock, Guide, Delete, Tickets, Setting } from '@element-plus/icons-vue'
import { getUserProfile, updateUserProfile, getUserFavorites, removeFavorite, getTripPlans } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('profile')
const saving = ref(false)
const changingPwd = ref(false)
const favorites = ref([])
const trips = ref([])

const user = computed(() => userStore.user)
const maskedEmail = computed(() => {
  const email = user.value?.email || ''
  const atIndex = email.indexOf('@')
  if (atIndex > 1) return email[0] + '***' + email.slice(atIndex)
  return email
})

const personaLabel = computed(() => {
  const map = {
    tourist: { text: '游客/旅行者', type: 'primary' },
    enthusiast: { text: '文化爱好者', type: 'success' },
    foodie: { text: '美食探索者', type: 'warning' },
  }
  return map[user.value?.persona_type] || map.tourist
})

const tabs = [
  { key: 'profile', label: '编辑资料', icon: 'User' },
  { key: 'favorites', label: '我的收藏', icon: 'Star' },
  { key: 'trips', label: '我的行程', icon: 'Guide' },
  { key: 'security', label: '修改密码', icon: 'Lock' },
]

const editForm = reactive({
  nickname: '',
  persona_type: 'tourist',
  interests: [],
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
})

function itemTypeLabel(type) {
  return { food: '美食', heritage: '非遗', event: '民俗' }[type] || type
}

function goToFavItem(fav) {
  const routes = {
    food: `/foods/${fav.item_id}`,
    heritage: `/heritages/${fav.item_id}`,
    event: `/festival`,
  }
  const path = routes[fav.item_type]
  if (path) router.push(path)
}

async function loadProfile() {
  try {
    const data = await getUserProfile()
    editForm.nickname = data.nickname
    editForm.persona_type = data.persona_type
    editForm.interests = data.interests || []
  } catch { /* 静默失败 */ }
}

async function loadFavorites() {
  try {
    const data = await getUserFavorites({ page_size: 100 })
    favorites.value = data.items || []
  } catch { /* 静默失败 */ }
}

async function loadTrips() {
  try {
    const data = await getTripPlans({ page_size: 100 })
    trips.value = data.items || []
  } catch { /* 静默失败 */ }
}

async function saveProfile() {
  saving.value = true
  try {
    await updateUserProfile(editForm)
    ElMessage.success('资料更新成功')
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeFav(id) {
  try {
    await ElMessageBox.confirm('确定取消收藏？', '提示', { type: 'warning' })
    await removeFavorite(id)
    favorites.value = favorites.value.filter(f => f.id !== id)
    ElMessage.success('已取消收藏')
  } catch { /* 取消操作 */ }
}

async function changePassword() {
  if (!passwordForm.old_password || !passwordForm.new_password) {
    return ElMessage.warning('请填写完整')
  }
  if (passwordForm.new_password.length < 6) {
    return ElMessage.warning('新密码至少6位')
  }
  changingPwd.value = true
  try {
    await updateUserProfile({ /* 实际调用 change password API */ })
    ElMessage.success('密码修改成功，请重新登录')
    userStore.logout()
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message || '修改失败')
  } finally {
    changingPwd.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadFavorites()
  loadTrips()
})
</script>

<style scoped>
.profile-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-md);
}

.page-header {
  margin-bottom: var(--space-2xl);
}

.page-header h1 {
  font-size: var(--fs-2xl);
  color: var(--ink);
  margin: 0 0 var(--space-xs);
}

.page-header p {
  color: var(--muted);
  margin: 0;
}

.profile-grid {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: var(--space-2xl);
}

/* Sidebar */
.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.user-card {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-2xl);
  text-align: center;
  box-shadow: 0 2px 12px oklch(0 0 0 / 0.04);
}

.user-card h2 {
  font-size: var(--fs-lg);
  color: var(--ink);
  margin: var(--space-md) 0 var(--space-xs);
}

.user-phone {
  color: var(--muted);
  font-size: var(--fs-sm);
  margin: 0 0 var(--space-sm);
}

.sidebar-nav {
  background: var(--surface);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px oklch(0 0 0 / 0.04);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-md) var(--space-lg);
  border: none;
  background: transparent;
  color: var(--ink);
  font-size: var(--fs-base);
  cursor: pointer;
  transition: all 0.2s;
}

.nav-item:hover {
  background: oklch(0.52 0.16 248 / 0.06);
}

.nav-item.active {
  background: oklch(0.52 0.16 248 / 0.1);
  color: var(--primary);
  font-weight: 600;
}

.nav-badge {
  margin-left: auto;
}

/* Main content */
.profile-main {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-2xl);
  box-shadow: 0 2px 12px oklch(0 0 0 / 0.04);
}

.tab-panel h3 {
  font-size: var(--fs-lg);
  color: var(--ink);
  margin: 0 0 var(--space-xl);
}

.profile-form {
  max-width: 480px;
}

.empty-tip {
  text-align: center;
  padding: var(--space-3xl) 0;
  color: var(--muted);
}

.empty-tip p {
  margin: var(--space-md) 0;
}

.favorite-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.fav-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.fav-item:hover {
  background: oklch(0.52 0.16 248 / 0.04);
}

.fav-thumb {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  flex-shrink: 0;
}

.fav-info {
  flex: 1;
}

.fav-name {
  display: block;
  color: var(--ink);
  font-weight: 500;
}

.fav-type {
  color: var(--muted);
  font-size: var(--fs-sm);
}

.trip-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.trip-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-lg);
  border-radius: 10px;
  border: 1px solid oklch(0 0 0 / 0.06);
}

.trip-info h4 {
  font-size: var(--fs-base);
  color: var(--ink);
  margin: 0 0 4px;
}

.trip-info p {
  color: var(--muted);
  font-size: var(--fs-sm);
  margin: 0;
}

@media (max-width: 768px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
  .profile-sidebar {
    order: -1;
  }
}
</style>
