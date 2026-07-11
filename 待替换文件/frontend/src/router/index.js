import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/foods',
    name: 'FoodList',
    component: () => import('@/views/food/FoodList.vue'),
    meta: { title: '美食推荐' },
  },
  {
    path: '/foods/:id',
    name: 'FoodDetail',
    component: () => import('@/views/food/FoodDetail.vue'),
    meta: { title: '美食详情' },
  },
  {
    path: '/heritages',
    name: 'HeritageList',
    component: () => import('@/views/heritage/HeritageList.vue'),
    meta: { title: '非遗民俗' },
  },
  {
    path: '/heritages/:id',
    name: 'HeritageDetail',
    component: () => import('@/views/heritage/HeritageDetail.vue'),
    meta: { title: '非遗详情' },
  },
  {
    path: '/festival',
    name: 'FestivalCalendar',
    component: () => import('@/views/festival/FestivalCalendar.vue'),
    meta: { title: '节日日历' },
  },
  {
    path: '/trip/create',
    name: 'TripCreate',
    component: () => import('@/views/trip/TripCreate.vue'),
    meta: { title: '创建行程', requiresAuth: true, fullMap: true },
  },
  {
    path: '/trip/:id',
    name: 'TripDetail',
    component: () => import('@/views/trip/TripDetail.vue'),
    meta: { title: '行程详情', requiresAuth: true },
  },
  {
    path: '/community',
    name: 'CommunityFeed',
    component: () => import('@/views/community/CommunityFeed.vue'),
    meta: { title: '社区推荐' },
  },
  {
    path: '/community/post/:id',
    name: 'PostDetail',
    component: () => import('@/views/community/PostDetail.vue'),
    meta: { title: '动态详情' },
  },
  {
    path: '/community/create',
    name: 'PostCreate',
    component: () => import('@/views/community/PostCreate.vue'),
    meta: { title: '发布动态', requiresAuth: true },
  },
  {
    path: '/messages',
    name: 'Messages',
    component: () => import('@/views/community/Messages.vue'),
    meta: { title: '私信', requiresAuth: true },
  },
  {
    path: '/dashboard',
    name: 'DashboardSmall',
    component: () => import('@/views/dashboard/DashboardSmall.vue'),
    meta: { title: '数据大屏' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/user/Login.vue'),
    meta: { title: '登录', guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/user/Register.vue'),
    meta: { title: '注册', guest: true },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/user/ForgotPassword.vue'),
    meta: { title: '找回密码', guest: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/user/Profile.vue'),
    meta: { title: '个人中心', requiresAuth: true },
  },
  {
    path: '/chat',
    name: 'CustomerService',
    component: () => import('@/views/CustomerService.vue'),
    meta: { title: '智能客服' },
  },
  {
    path: '/search',
    name: 'SearchResult',
    component: () => import('@/views/SearchResult.vue'),
    meta: { title: '搜索结果' },
  },
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/AdminDashboard.vue'),
        meta: { title: '管理后台' },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/AdminUsers.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'foods',
        name: 'AdminFoods',
        component: () => import('@/views/admin/AdminFoods.vue'),
        meta: { title: '美食管理' },
      },
      {
        path: 'heritages',
        name: 'AdminHeritages',
        component: () => import('@/views/admin/AdminHeritages.vue'),
        meta: { title: '非遗管理' },
      },
      {
        path: 'events',
        name: 'AdminEvents',
        component: () => import('@/views/admin/EventManage.vue'),
        meta: { title: '节日管理' },
      },
      {
        path: 'posts',
        name: 'AdminPosts',
        component: () => import('@/views/admin/AdminPosts.vue'),
        meta: { title: '社区审核' },
      },
      {
        path: 'dashboard-data',
        name: 'AdminDashboardData',
        component: () => import('@/views/admin/AdminDashboardData.vue'),
        meta: { title: '数据管理' },
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/AdminSettings.vue'),
        meta: { title: '系统设置' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '404' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  document.title = to.meta.title ? `${to.meta.title} - 潮汕文化宣传平台` : '潮汕文化宣传平台'

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return next('/login?redirect=' + encodeURIComponent(to.fullPath))
  }

  if (to.meta.guest && userStore.isLoggedIn) {
    return next('/')
  }

  if (to.meta.requiresAdmin && userStore.user?.role !== 'admin') {
    return next('/')
  }

  next()
})

export default router
