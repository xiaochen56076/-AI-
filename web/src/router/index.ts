import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    section?: string
    requiresAuth?: boolean
    guestOnly?: boolean
    permissions?: string[]
  }
}

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth', top: 96 }
    return { top: 0 }
  },
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { title: '登录', guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { title: '注册', guestOnly: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/PublicLayout.vue'),
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/public/HomeView.vue'),
          meta: { title: '首页' },
        },
        {
          path: 'activities',
          name: 'activities',
          component: () => import('@/views/public/ActivityListView.vue'),
          meta: { title: '活动广场' },
        },
        {
          path: 'activities/:id(\\d+)',
          name: 'activity-detail',
          component: () => import('@/views/public/ActivityDetailView.vue'),
          meta: { title: '活动详情' },
        },
        {
          path: 'my/signups',
          name: 'my-signups',
          component: () => import('@/views/public/MySignupsView.vue'),
          meta: { title: '我的报名', requiresAuth: true },
        },
        {
          path: 'my/favorites',
          name: 'my-favorites',
          component: () => import('@/views/public/FavoritesView.vue'),
          meta: { title: '我的收藏', requiresAuth: true },
        },
        {
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/views/public/NotificationsView.vue'),
          meta: { title: '消息中心', requiresAuth: true },
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/public/ProfileView.vue'),
          meta: { title: '个人中心', requiresAuth: true },
        },
        {
          path: 'checkin',
          name: 'checkin',
          component: () => import('@/views/public/CheckinView.vue'),
          meta: { title: '扫码签到', requiresAuth: true },
        },
        {
          path: 'forbidden',
          name: 'forbidden',
          component: () => import('@/views/public/ForbiddenView.vue'),
          meta: { title: '无权访问' },
        },
      ],
    },
    {
      path: '/console',
      component: () => import('@/layouts/ConsoleLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'console-home',
          component: () => import('@/views/console/ConsoleHomeView.vue'),
          meta: { title: '工作台' },
        },
        {
          path: 'activities',
          name: 'console-activities',
          component: () => import('@/views/console/OrganizerActivitiesView.vue'),
          meta: { title: '我的活动', section: '活动运营', permissions: ['activity:create'] },
        },
        {
          path: 'activities/new',
          name: 'console-activity-create',
          component: () => import('@/views/console/OrganizerActivityFormView.vue'),
          meta: { title: '发布活动', section: '活动运营', permissions: ['activity:create'] },
        },
        {
          path: 'activities/:id(\\d+)/edit',
          name: 'console-activity-edit',
          component: () => import('@/views/console/OrganizerActivityFormView.vue'),
          meta: { title: '编辑活动', section: '活动运营', permissions: ['activity:create'] },
        },
        {
          path: 'activities/:id(\\d+)/roster',
          name: 'console-activity-roster',
          component: () => import('@/views/console/OrganizerRosterView.vue'),
          meta: { title: '报名名单', section: '活动运营', permissions: ['activity:create'] },
        },
        {
          path: 'activities/:id(\\d+)/checkin',
          name: 'console-activity-checkin',
          component: () => import('@/views/console/OrganizerCheckinView.vue'),
          meta: { title: '签到管理', section: '活动运营', permissions: ['activity:create'] },
        },
        {
          path: 'activities/:id(\\d+)/stats',
          name: 'console-activity-stats',
          component: () => import('@/views/console/OrganizerStatsView.vue'),
          meta: { title: '活动数据', section: '活动运营', permissions: ['analytics:activity'] },
        },
        {
          path: 'audit',
          name: 'console-audit',
          component: () => import('@/views/console/AuditView.vue'),
          meta: { title: '审核工作台', section: '内容治理', permissions: ['activity:audit'] },
        },
        {
          path: 'dashboard',
          name: 'console-dashboard',
          component: () => import('@/views/console/AdminDashboardView.vue'),
          meta: { title: '全站看板', section: '数据洞察', permissions: ['analytics:global'] },
        },
        {
          path: 'users',
          name: 'console-users',
          component: () => import('@/views/console/AdminUsersView.vue'),
          meta: { title: '用户管理', section: '平台管理', permissions: ['user:manage'] },
        },
        {
          path: 'dictionaries',
          name: 'console-dictionaries',
          component: () => import('@/views/console/AdminDictionaryView.vue'),
          meta: { title: '字典管理', section: '平台管理', permissions: ['dict:manage'] },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/public/NotFoundView.vue'),
      meta: { title: '页面不存在' },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.initialized) {
    await auth.bootstrap()
  }

  document.title = to.meta.title ? `${to.meta.title} · CampusHub` : 'CampusHub 校园活动平台'

  if (to.meta.guestOnly && auth.isAuthenticated) {
    const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : '/'
    return redirect.startsWith('/') ? redirect : '/'
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.permissions && !to.meta.permissions.some((item) => auth.hasPermission(item))) {
    return { name: 'forbidden', query: { from: to.fullPath } }
  }

  return true
})

export default router
