<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink, RouterView } from 'vue-router'
import {
  ArrowDown,
  ArrowRight,
  Bell,
  Camera,
  Menu,
  Monitor,
  Star,
  SwitchButton,
  Tickets,
  User,
} from '@element-plus/icons-vue'

import UserAvatar from '@/components/UserAvatar.vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDate } from '@/utils/format'

const auth = useAuthStore()
const notifications = useNotificationsStore()
const route = useRoute()
const router = useRouter()

const mobileOpen = ref(false)
const scrolled = ref(false)

const navLinks = computed(() => [
  { label: '首页', to: '/' },
  { label: '活动广场', to: '/activities' },
  ...(auth.isAuthenticated
    ? [
        { label: '我的报名', to: '/my/signups' },
        { label: '消息中心', to: '/notifications' },
      ]
    : []),
])

const hostLinks = computed(() => {
  if (!auth.isAuthenticated) {
    return [
      { label: '发布活动', to: '/login' },
      { label: '我的活动', to: '/login' },
      { label: '报名名单', to: '/login' },
    ]
  }
  const links: { label: string; to: string }[] = []
  if (auth.hasPermission('activity:create')) {
    links.push({ label: '发布活动', to: '/console/activities/new' })
    links.push({ label: '我的活动', to: '/console/activities' })
  }
  if (auth.hasPermission('activity:audit')) {
    links.push({ label: '审核工作台', to: '/console/audit' })
  }
  if (auth.hasPermission('analytics:global')) {
    links.push({ label: '全站看板', to: '/console/dashboard' })
  }
  if (!links.length) {
    links.push({ label: '个人中心', to: '/profile' })
  }
  return links
})

const hostTitle = computed(() =>
  auth.isAuthenticated && auth.canUseConsole ? '工作台' : '主办方'
)

function isActive(to: string) {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}

function handleScroll() {
  scrolled.value = window.scrollY > 8
}

async function handleCommand(command: string) {
  if (command === 'logout') {
    await auth.logout()
    notifications.stopPolling()
    notifications.setUnread(0)
    router.push('/')
    return
  }
  if (command === 'console') {
    if (auth.consoleEntry) router.push(auth.consoleEntry)
    return
  }
  const routes: Record<string, string> = {
    profile: '/profile',
    signups: '/my/signups',
    favorites: '/my/favorites',
    checkin: '/checkin',
  }
  if (routes[command]) router.push(routes[command])
}

watch(
  () => route.fullPath,
  () => {
    mobileOpen.value = false
  },
)

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div class="public-layout">
    <div class="top-strip">
      <div class="page-container top-strip__inner">
        <span>2026 秋季学期 · 校园活动，一站直达</span>
        <span class="top-strip__right">
          <span class="live-dot"></span>
          活动报名与签到服务运行中
        </span>
      </div>
    </div>

    <header class="site-header" :class="{ 'is-scrolled': scrolled }">
      <div class="page-container header-inner">
        <RouterLink to="/" class="brand">
          <span class="brand-mark"><span>C</span></span>
          <span class="brand-text">
            <strong>CampusHub</strong>
            <small>校园活动平台</small>
          </span>
        </RouterLink>

        <nav class="main-nav">
          <RouterLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="nav-link"
            :class="{ 'is-active': isActive(link.to) }"
          >
            {{ link.label }}
          </RouterLink>
        </nav>

        <div class="header-actions">
          <template v-if="auth.isAuthenticated">
            <RouterLink to="/notifications" class="icon-button" aria-label="消息中心">
              <el-badge
                :value="notifications.unread > 99 ? '99+' : notifications.unread"
                :hidden="notifications.unread === 0"
                :max="99"
              >
                <el-icon><Bell /></el-icon>
              </el-badge>
            </RouterLink>

            <el-dropdown trigger="click" @command="handleCommand">
              <button class="user-trigger" type="button">
                <UserAvatar :name="auth.displayName" :src="auth.user?.avatar_url" :size="34" />
                <span class="user-trigger__name">{{ auth.displayName }}</span>
                <el-icon class="user-trigger__arrow"><ArrowDown /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <div class="dropdown-profile">
                    <strong>{{ auth.displayName }}</strong>
                    <span>{{ auth.user?.student_no }} · {{ auth.user?.roles.map((r) => r.name).join(' / ') }}</span>
                  </div>
                  <el-dropdown-item command="profile" :icon="User">个人中心</el-dropdown-item>
                  <el-dropdown-item command="signups" :icon="Tickets">我的报名</el-dropdown-item>
                  <el-dropdown-item command="favorites" :icon="Star">我的收藏</el-dropdown-item>
                  <el-dropdown-item command="checkin" :icon="Camera">扫码签到</el-dropdown-item>
                  <el-dropdown-item
                    v-if="auth.consoleEntry"
                    command="console"
                    :icon="Monitor"
                    divided
                  >
                    进入工作台
                  </el-dropdown-item>
                  <el-dropdown-item command="logout" :icon="SwitchButton" divided>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>

          <template v-else>
            <RouterLink to="/login" class="login-link">登录</RouterLink>
            <RouterLink to="/register">
              <el-button type="primary" round class="ch-button-gradient">加入 CampusHub</el-button>
            </RouterLink>
          </template>

          <button class="mobile-toggle" type="button" aria-label="打开菜单" @click="mobileOpen = true">
            <el-icon><Menu /></el-icon>
          </button>
        </div>
      </div>
    </header>

    <main class="site-main">
      <RouterView />
    </main>

    <footer class="site-footer">
      <div class="page-container footer-grid">
        <div class="footer-brand">
          <RouterLink to="/" class="brand brand--footer">
            <span class="brand-mark"><span>C</span></span>
            <span class="brand-text">
              <strong>CampusHub</strong>
              <small>校园活动平台</small>
            </span>
          </RouterLink>
          <p>让每一场校园活动被看见，让每一次参与都简单。浏览、报名、候补、签到，一站完成。</p>
          <span class="footer-date">当前日期 · {{ formatDate(new Date().toISOString()) }}</span>
        </div>

        <div class="footer-column">
          <h4>探索</h4>
          <RouterLink to="/activities">活动广场</RouterLink>
          <RouterLink to="/activities?scope=upcoming&sort=deadline">报名截止</RouterLink>
          <RouterLink to="/activities?scope=past">往期活动</RouterLink>
        </div>

        <div class="footer-column">
          <h4>服务</h4>
          <RouterLink to="/my/signups">我的报名</RouterLink>
          <RouterLink to="/checkin">扫码签到</RouterLink>
          <RouterLink to="/notifications">消息中心</RouterLink>
        </div>

        <div class="footer-column">
          <h4>{{ hostTitle }}</h4>
          <RouterLink v-for="link in hostLinks" :key="link.label" :to="link.to">{{ link.label }}</RouterLink>
        </div>
      </div>
      <div class="page-container footer-bottom">
        <span>© 2026 CampusHub · 校园活动平台</span>
        <span>Built for a better campus experience.</span>
      </div>
    </footer>

    <el-drawer v-model="mobileOpen" direction="rtl" size="300px" :with-header="false">
      <div class="mobile-menu">
        <div class="mobile-menu__top">
          <RouterLink to="/" class="brand">
            <span class="brand-mark"><span>C</span></span>
            <span class="brand-text">
              <strong>CampusHub</strong>
              <small>校园活动平台</small>
            </span>
          </RouterLink>
        </div>

        <div v-if="auth.isAuthenticated" class="mobile-user">
          <UserAvatar :name="auth.displayName" :src="auth.user?.avatar_url" :size="42" />
          <div>
            <strong>{{ auth.displayName }}</strong>
            <span>{{ auth.user?.student_no }}</span>
          </div>
        </div>

        <nav class="mobile-nav">
          <RouterLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            :class="{ 'is-active': isActive(link.to) }"
          >
            {{ link.label }}
            <el-icon><ArrowRight /></el-icon>
          </RouterLink>
          <template v-if="auth.isAuthenticated">
            <RouterLink to="/my/favorites">我的收藏</RouterLink>
            <RouterLink to="/profile">个人中心</RouterLink>
            <RouterLink to="/checkin">扫码签到</RouterLink>
            <RouterLink v-if="auth.consoleEntry" :to="auth.consoleEntry">工作台</RouterLink>
          </template>
        </nav>

        <div class="mobile-menu__footer">
          <template v-if="auth.isAuthenticated">
            <el-button plain round style="width: 100%" @click="handleCommand('logout')">
              退出登录
            </el-button>
          </template>
          <template v-else>
            <RouterLink to="/login" style="flex: 1">
              <el-button plain round style="width: 100%">登录</el-button>
            </RouterLink>
            <RouterLink to="/register" style="flex: 1">
              <el-button type="primary" round style="width: 100%">注册</el-button>
            </RouterLink>
          </template>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.public-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--ch-bg);
}

.top-strip {
  background: #0d1730;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
}

.top-strip__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 34px;
}

.top-strip__right {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38d39f;
  box-shadow: 0 0 0 3px rgba(56, 211, 159, 0.16);
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: rgba(255, 255, 255, 0.86);
  border-bottom: 1px solid transparent;
  backdrop-filter: blur(18px);
  transition: box-shadow 0.25s ease, border-color 0.25s ease;
}

.site-header.is-scrolled {
  border-bottom-color: var(--ch-border);
  box-shadow: 0 10px 30px rgba(16, 26, 51, 0.06);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 34px;
  height: 72px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  flex: 0 0 auto;
}

.brand-mark {
  position: relative;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 13px;
  background: linear-gradient(135deg, #5874f5, #3757e8 55%, #2439a8);
  color: #fff;
  font-size: 21px;
  font-weight: 800;
  box-shadow: 0 8px 20px rgba(55, 87, 232, 0.28);
  overflow: hidden;
}

.brand-mark::after {
  content: '';
  position: absolute;
  width: 24px;
  height: 24px;
  right: -8px;
  top: -8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
}

.brand-mark span {
  position: relative;
  z-index: 1;
  line-height: 1;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.12;
}

.brand-text strong {
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.brand-text small {
  color: var(--ch-muted-light);
  font-size: 9.5px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.main-nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-link {
  position: relative;
  padding: 8px 14px;
  border-radius: 10px;
  color: var(--ch-muted);
  font-size: 14px;
  font-weight: 600;
  transition: color 0.2s ease, background 0.2s ease;
}

.nav-link:hover {
  color: var(--ch-ink);
  background: #f3f5fb;
}

.nav-link.is-active {
  color: var(--ch-primary);
  background: var(--ch-primary-soft);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-left: auto;
}

.icon-button {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  color: var(--ch-ink-soft);
  font-size: 18px;
  transition: background 0.2s ease;
}

.icon-button:hover {
  background: #f1f4fb;
}

.icon-button :deep(.el-badge__content) {
  border: 2px solid #fff;
}

.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 5px 10px 5px 5px;
  border: 1px solid var(--ch-border);
  border-radius: 999px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.user-trigger:hover {
  border-color: var(--ch-border-strong);
  box-shadow: 0 6px 16px rgba(16, 26, 51, 0.06);
}

.user-trigger__name {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
}

.user-trigger__arrow {
  color: var(--ch-muted-light);
  font-size: 12px;
}

.login-link {
  color: var(--ch-ink-soft);
  font-size: 14px;
  font-weight: 600;
  padding: 8px 6px;
}

.login-link:hover {
  color: var(--ch-primary);
}

.mobile-toggle {
  display: none;
  place-items: center;
  width: 38px;
  height: 38px;
  border: 1px solid var(--ch-border);
  border-radius: 10px;
  background: #fff;
  color: var(--ch-ink);
  font-size: 19px;
  cursor: pointer;
}

.site-main {
  flex: 1;
}

.site-footer {
  margin-top: 40px;
  padding: 56px 0 26px;
  background: #0d1730;
  color: rgba(255, 255, 255, 0.66);
}

.footer-grid {
  display: grid;
  grid-template-columns: 1.7fr 1fr 1fr 1fr;
  gap: 40px;
}

.brand--footer .brand-text strong {
  color: #fff;
}

.brand--footer .brand-text small {
  color: rgba(255, 255, 255, 0.42);
}

.footer-brand p {
  max-width: 340px;
  margin-top: 18px;
  font-size: 13px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.52);
}

.footer-date {
  display: inline-block;
  margin-top: 16px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.34);
}

.footer-column {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 4px;
}

.footer-column h4 {
  margin-bottom: 6px;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.footer-column a {
  color: rgba(255, 255, 255, 0.52);
  font-size: 13px;
  transition: color 0.2s ease;
}

.footer-column a:hover {
  color: #fff;
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 46px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 12px;
  color: rgba(255, 255, 255, 0.32);
}

.dropdown-profile {
  display: flex;
  flex-direction: column;
  padding: 4px 16px 10px;
  min-width: 200px;
}

.dropdown-profile strong {
  font-size: 13px;
  color: var(--ch-ink);
}

.dropdown-profile span {
  margin-top: 2px;
  font-size: 11.5px;
  color: var(--ch-muted);
}

.mobile-menu {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.mobile-menu__top {
  padding-bottom: 18px;
  border-bottom: 1px solid var(--ch-border);
}

.mobile-user {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 18px 0;
  padding: 14px;
  border-radius: 14px;
  background: var(--ch-primary-soft);
}

.mobile-user div {
  display: flex;
  flex-direction: column;
}

.mobile-user strong {
  font-size: 14px;
}

.mobile-user span {
  color: var(--ch-muted);
  font-size: 12px;
}

.mobile-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mobile-nav a {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 4px;
  border-bottom: 1px solid #f1f3f9;
  color: var(--ch-ink-soft);
  font-size: 14px;
  font-weight: 600;
}

.mobile-nav a.is-active {
  color: var(--ch-primary);
}

.mobile-nav .el-icon {
  color: var(--ch-muted-light);
  font-size: 13px;
}

.mobile-menu__footer {
  display: flex;
  gap: 10px;
  margin-top: auto;
  padding-top: 24px;
}

@media (max-width: 960px) {
  .main-nav {
    display: none;
  }

  .mobile-toggle {
    display: grid;
  }

  .header-inner {
    height: 64px;
  }

  .footer-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 640px) {
  .top-strip__right {
    display: none;
  }

  .user-trigger__name,
  .user-trigger__arrow {
    display: none;
  }

  .user-trigger {
    padding: 3px;
    border: none;
    background: transparent;
  }

  .header-actions {
    gap: 8px;
  }

  .header-actions > a .el-button {
    padding: 9px 14px;
    font-size: 13px;
  }

  .footer-grid {
    grid-template-columns: 1fr;
    gap: 28px;
  }

  .footer-bottom {
    flex-direction: column;
    gap: 6px;
  }

  .site-footer {
    padding-top: 40px;
  }
}
</style>
