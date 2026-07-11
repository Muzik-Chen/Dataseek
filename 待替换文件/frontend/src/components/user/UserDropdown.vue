<template>
  <div class="user-dropdown">
    <!-- 未登录 -->
    <template v-if="!userStore.isLoggedIn">
      <el-button size="small" @click="router.push('/login')">登录</el-button>
      <el-button size="small" type="primary" @click="router.push('/register')">注册</el-button>
    </template>

    <!-- 已登录 -->
    <el-dropdown v-else trigger="click">
      <div class="user-dropdown__trigger">
        <el-avatar :size="32" :src="userStore.user?.avatar_url" :icon="UserFilled" />
        <span class="user-dropdown__name">{{ userStore.user?.nickname || '用户' }}</span>
        <el-icon class="user-dropdown__arrow"><ArrowDown /></el-icon>
      </div>

      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item @click="router.push('/profile')">
            <el-icon><User /></el-icon> 个人中心
          </el-dropdown-item>
          <el-dropdown-item @click="router.push('/trip/create')">
            <el-icon><Guide /></el-icon> 我的行程
          </el-dropdown-item>
          <el-dropdown-item v-if="userStore.isAdmin" @click="router.push('/admin')">
            <el-icon><Setting /></el-icon> 管理后台
          </el-dropdown-item>
          <el-dropdown-item divided @click="handleLogout">
            <el-icon><SwitchButton /></el-icon> 退出登录
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { User, UserFilled, ArrowDown, Guide, Setting, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { toast } from '@/utils/toast'

const router = useRouter()
const userStore = useUserStore()

function handleLogout() {
  userStore.logout()
  toast.success('已退出登录')
  router.push('/')
}
</script>

<style scoped>
.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-dropdown__trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-full);
  transition: background 0.2s;
}

.user-dropdown__trigger:hover {
  background: var(--surface);
}

.user-dropdown__name {
  font-size: var(--fs-sm);
  color: var(--ink);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-dropdown__arrow {
  font-size: 12px;
  color: var(--muted);
}
</style>
