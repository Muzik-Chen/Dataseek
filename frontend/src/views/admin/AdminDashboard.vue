<template>
  <div class="admin-dashboard">
    <h1>管理后台</h1>

    <div class="stat-grid">
      <div class="stat-card">
        <strong>{{ stats.totalUsers }}</strong>
        <span>注册用户</span>
      </div>
      <div class="stat-card">
        <strong>{{ stats.totalFoods }}</strong>
        <span>美食条目</span>
      </div>
      <div class="stat-card">
        <strong>{{ stats.totalHeritages }}</strong>
        <span>非遗项目</span>
      </div>
      <div class="stat-card">
<<<<<<< HEAD
        <strong>{{ stats.totalEvents }}</strong>
        <span>民俗活动</span>
      </div>
      <div class="stat-card">
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
        <strong>{{ stats.totalPosts }}</strong>
        <span>社区动态</span>
      </div>
    </div>

    <div class="admin-sections">
      <div class="admin-card">
        <h3>快捷操作</h3>
        <div class="quick-actions">
          <el-button type="primary" @click="$router.push('/admin/foods')">管理美食</el-button>
          <el-button type="primary" @click="$router.push('/admin/heritages')">管理非遗</el-button>
          <el-button @click="$router.push('/admin/users')">管理用户</el-button>
          <el-button @click="$router.push('/admin/posts')">管理社区</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
<<<<<<< HEAD
import adminApi from '@/api/admin'
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22

const stats = ref({
  totalUsers: 0,
  totalFoods: 0,
  totalHeritages: 0,
<<<<<<< HEAD
  totalEvents: 0,
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
  totalPosts: 0,
})

onMounted(async () => {
  try {
<<<<<<< HEAD
    const data = await adminApi.stats()
    if (data) {
      stats.value.totalUsers = data.total_users ?? 0
      stats.value.totalFoods = data.total_foods ?? 0
      stats.value.totalHeritages = data.total_heritages ?? 0
      stats.value.totalEvents = data.total_events ?? 0
      stats.value.totalPosts = data.total_posts ?? 0
    }
  } catch { /* handled by interceptor */ }
=======
    const resp = await fetch('/api/v1/dashboard/overview')
    const data = await resp.json()
    if (data.code === 0) {
      stats.value.totalUsers = data.data.total_users
      stats.value.totalFoods = data.data.total_foods
      stats.value.totalHeritages = data.data.total_heritages
      stats.value.totalPosts = data.data.total_posts
    }
  } catch { /* 静默 */ }
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
})
</script>

<style scoped>
.admin-dashboard { max-width: 1000px; }
<<<<<<< HEAD
=======

>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
.admin-dashboard h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-2xl); }

.stat-grid {
  display: grid;
<<<<<<< HEAD
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
=======
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
  gap: var(--space-lg);
  margin-bottom: var(--space-2xl);
}

.stat-card {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-xl);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
}

.stat-card strong { display: block; font-size: var(--fs-3xl); color: var(--primary); margin-bottom: var(--space-xs); }
.stat-card span { color: var(--muted); font-size: var(--fs-sm); }

.admin-sections { display: flex; flex-direction: column; gap: var(--space-xl); }

.admin-card {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-xl);
  box-shadow: 0 2px 8px oklch(0 0 0 / 0.03);
}

.admin-card h3 { font-size: var(--fs-lg); color: var(--ink); margin: 0 0 var(--space-lg); }

.quick-actions { display: flex; gap: var(--space-md); flex-wrap: wrap; }

@media (max-width: 768px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
