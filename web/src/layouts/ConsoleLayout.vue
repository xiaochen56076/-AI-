<script setup lang="ts">
import { computed, ref, watch, type Component } from 'vue'
import { useRoute, useRouter, RouterLink, RouterView } from 'vue-router'
import {
  ArrowDown,
  Bell,
  Calendar,
  Collection,
  DataAnalysis,
  House,
  Menu,
  Stamp,
  SwitchButton,
  User,
} from '@element-plus/icons-vue'

import UserAvatar from '@/components/UserAvatar.vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { roleLabel } from '@/utils/format'

interface NavItem {
  label: string
  to: string
  icon: Component
  permission: string
  match: string[]
}

interface NavSection {
  label: string
  items: NavItem[]
}

const auth = useAuthStore()
const notifications = useNotificationsStore()
const route = useRoute()
const router = useRouter()

const drawerOpen = ref(false)

const sections = computed<NavSection[]>(() => {
  const all: NavSection[] = [
    {
      label: '数据洞察',
      items: [
        {
          label: '全站看板',
          to: '/console/dashboard',
          icon: DataAnalysis,
          permission: 'analytics:global',
          match: ['/console/dashboard'],
        },
      ],
    },
    {
      label: '活动运营',
      items: [
        {
          label: '我的活动',
          to: '/console/activities',
          icon: Calendar,
          permission: 'activity:create',
          match: ['/console/activities'],
        },
        {
          label: '审核工作台',
          to: '/console/audit',
          icon: Stamp,
          permission: 'activity:audit',
          match: ['/console/audit'],
        },
      ],
    },
    {
      label: '平台管理',
      items: [
        {
          label: '用户管理',
          to: '/console/users',
          icon: User,
          permission: 'user:manage',
          match: ['/console/users'],
        },
        {
          label: '字典管理',
          to: '/console/dictionaries',
          icon: Collection,
          permission: 'dict:manage',
          match: ['/console/dictionaries'],
        },
      ],
    },
  ]

  return all
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => auth.hasPermission(item.permission)),
    }))
    .filter((section) => section.items.length > 0)
})

const pageTitle = computed(() => route.meta.title || '工作台')
const pageSection = computed(() => route.meta.section || 'CampusHub 工作台')

function isActive(item: NavItem) {
  return item.match.some((prefix) => route.path.startsWith(prefix))
}

watch(
  () => route.fullPath,
  () => {
    drawerOpen.value = false
  },
)

async function handleCommand(command: string) {
  if (command === 'logout') {
    await auth.logout()
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'front') {
    router.push('/')
  } else if (command === 'notifications') {
    router.push('/notifications')
  }
}
</script>

<template>
  <div class="console-layout">
    <aside class="console-sidebar">
      <RouterLink to="/console" class="console-brand">
        <span class="console-brand__mark">C</span>
        <span class="console-brand__text">
          <strong>CampusHub</strong>
          <small>运营工作台</small>
        </span>
      </RouterLink>

      <div class="console-role">
        <span class="console-role__label">当前身份</span>
        <div class="console-role__tags">
          <span v-for="role in auth.roles" :key="role.code">{{ roleLabel(role.code) }}</span>
          <span v-if="!auth.roles.length">访客</span>
        </div>
      </div>

      <nav class="console-nav">
        <div v-for="section in sections" :key="section.label" class="console-nav__section">
          <span class="console-nav__label">{{ section.label }}</span>
          <RouterLink
            v-for="item in section.items"
            :key="item.to"
            :to="item.to"
            class="console-nav__item"
            :class="{ 'is-active': isActive(item) }"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
            <span class="console-nav__indicator"></span>
          </RouterLink>
        </div>
      </nav>

      <div class="console-sidebar__bottom">
        <RouterLink to="/" class="console-exit">
          <el-icon><House /></el-icon>
          返回活动广场
        </RouterLink>
        <div class="console-user">
          <UserAvatar :name="auth.displayName" :src="auth.user?.avatar_url" :size="38" />
          <div class="console-user__meta">
            <strong>{{ auth.displayName }}</strong>
            <span>{{ auth.user?.student_no }}</span>
          </div>
          <button type="button" title="退出登录" @click="handleCommand('logout')">
            <el-icon><SwitchButton /></el-icon>
          </button>
        </div>
      </div>
    </aside>

    <div class="console-main">
      <header class="console-topbar">
        <button class="console-menu-button" type="button" @click="drawerOpen = true">
          <el-icon><Menu /></el-icon>
        </button>
        <div class="console-breadcrumb">
          <span>{{ pageSection }}</span>
          <span class="console-breadcrumb__sep">/</span>
          <strong>{{ pageTitle }}</strong>
        </div>

        <div class="console-topbar__actions">
          <RouterLink to="/notifications" class="console-icon-button" aria-label="消息中心">
            <el-badge
              :value="notifications.unread > 99 ? '99+' : notifications.unread"
              :hidden="notifications.unread === 0"
              :max="99"
            >
              <el-icon><Bell /></el-icon>
            </el-badge>
          </RouterLink>

          <el-dropdown trigger="click" @command="handleCommand">
            <button class="console-user-trigger" type="button">
              <UserAvatar :name="auth.displayName" :src="auth.user?.avatar_url" :size="32" />
              <span>{{ auth.displayName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile" :icon="User">个人中心</el-dropdown-item>
                <el-dropdown-item command="notifications" :icon="Bell">消息中心</el-dropdown-item>
                <el-dropdown-item command="front" :icon="House" divided>返回活动广场</el-dropdown-item>
                <el-dropdown-item command="logout" :icon="SwitchButton" divided>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="console-content">
        <RouterView />
      </main>
    </div>

    <el-drawer v-model="drawerOpen" direction="ltr" size="280px" :with-header="false">
      <div class="console-mobile-menu">
        <RouterLink to="/console" class="console-brand">
          <span class="console-brand__mark">C</span>
          <span class="console-brand__text">
            <strong>CampusHub</strong>
            <small>运营工作台</small>
          </span>
        </RouterLink>
        <nav class="console-nav">
          <div v-for="section in sections" :key="section.label" class="console-nav__section">
            <span class="console-nav__label">{{ section.label }}</span>
            <RouterLink
              v-for="item in section.items"
              :key="item.to"
              :to="item.to"
              class="console-nav__item"
              :class="{ 'is-active': isActive(item) }"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </RouterLink>
          </div>
        </nav>
        <RouterLink to="/" class="console-exit">
          <el-icon><House /></el-icon>
          返回活动广场
        </RouterLink>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.console-layout {
  display: flex;
  min-height: 100vh;
  background: var(--ch-bg);
}

.console-sidebar {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  flex: 0 0 264px;
  width: 264px;
  height: 100vh;
  padding: 26px 18px 20px;
  background:
    radial-gradient(500px 300px at 0% 0%, rgba(55, 87, 232, 0.3), transparent 62%),
    radial-gradient(360px 260px at 100% 100%, rgba(122, 90, 248, 0.16), transparent 60%),
    #0b1328;
  color: rgba(255, 255, 255, 0.72);
  overflow-y: auto;
}

.console-brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0 8px;
}

.console-brand__mark {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 13px;
  background: linear-gradient(135deg, #5874f5, #3757e8 55%, #2439a8);
  color: #fff;
  font-size: 21px;
  font-weight: 800;
  box-shadow: 0 10px 26px rgba(55, 87, 232, 0.35);
}

.console-brand__text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}

.console-brand__text strong {
  color: #fff;
  font-size: 16px;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.console-brand__text small {
  color: rgba(255, 255, 255, 0.38);
  font-size: 9.5px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.console-role {
  margin: 26px 8px 10px;
  padding: 13px 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.04);
}

.console-role__label {
  color: rgba(255, 255, 255, 0.34);
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.console-role__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 7px;
}

.console-role__tags span {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(122, 144, 255, 0.16);
  color: #aebcff;
  font-size: 11px;
  font-weight: 600;
}

.console-nav {
  margin-top: 14px;
}

.console-nav__section {
  margin-bottom: 20px;
}

.console-nav__label {
  display: block;
  padding: 0 12px 7px;
  color: rgba(255, 255, 255, 0.28);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.console-nav__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 11px;
  margin-bottom: 3px;
  padding: 10px 12px;
  border-radius: 11px;
  color: rgba(255, 255, 255, 0.62);
  font-size: 13.5px;
  font-weight: 500;
  transition: background 0.2s ease, color 0.2s ease;
}

.console-nav__item .el-icon {
  font-size: 17px;
  color: rgba(255, 255, 255, 0.4);
}

.console-nav__item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.console-nav__item.is-active {
  background: linear-gradient(90deg, rgba(74, 104, 242, 0.28), rgba(74, 104, 242, 0.1));
  color: #fff;
}

.console-nav__item.is-active .el-icon {
  color: #a8b9ff;
}

.console-nav__indicator {
  position: absolute;
  right: 0;
  top: 50%;
  width: 3px;
  height: 18px;
  border-radius: 3px;
  background: #6e8aff;
  opacity: 0;
  transform: translateY(-50%);
}

.console-nav__item.is-active .console-nav__indicator {
  opacity: 1;
}

.console-sidebar__bottom {
  margin-top: auto;
  padding-top: 18px;
}

.console-exit {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 12px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.44);
  font-size: 12.5px;
  transition: color 0.2s ease, background 0.2s ease;
}

.console-exit:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

.console-user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.035);
}

.console-user__meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.3;
}

.console-user__meta strong {
  overflow: hidden;
  color: #fff;
  font-size: 12.5px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.console-user__meta span {
  color: rgba(255, 255, 255, 0.34);
  font-size: 10.5px;
}

.console-user button {
  margin-left: auto;
  padding: 5px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: rgba(255, 255, 255, 0.36);
  font-size: 15px;
  cursor: pointer;
}

.console-user button:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.console-main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.console-topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: 18px;
  height: 66px;
  padding: 0 32px;
  border-bottom: 1px solid var(--ch-border);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px);
}

.console-menu-button {
  display: none;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--ch-border);
  border-radius: 9px;
  background: #fff;
  color: var(--ch-ink);
  font-size: 18px;
  cursor: pointer;
}

.console-breadcrumb {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13px;
  color: var(--ch-muted-light);
}

.console-breadcrumb strong {
  color: var(--ch-ink);
  font-weight: 650;
}

.console-breadcrumb__sep {
  color: var(--ch-border-strong);
}

.console-topbar__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.console-icon-button {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: var(--ch-ink-soft);
  font-size: 17px;
}

.console-icon-button:hover {
  background: #f3f5fb;
}

.console-user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px 4px 4px;
  border: 1px solid var(--ch-border);
  border-radius: 999px;
  background: #fff;
  color: var(--ch-ink-soft);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
}

.console-user-trigger .el-icon {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.console-content {
  flex: 1;
  padding: 30px 32px 56px;
  min-width: 0;
}

.console-mobile-menu {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.console-mobile-menu .console-brand {
  margin-bottom: 22px;
}

.console-mobile-menu .console-brand__text strong {
  color: var(--ch-ink);
}

.console-mobile-menu .console-brand__text small {
  color: var(--ch-muted-light);
}

.console-mobile-menu .console-nav__label {
  color: var(--ch-muted-light);
}

.console-mobile-menu .console-nav__item {
  color: var(--ch-ink-soft);
}

.console-mobile-menu .console-nav__item .el-icon {
  color: var(--ch-muted);
}

.console-mobile-menu .console-nav__item:hover {
  background: #f3f5fb;
  color: var(--ch-ink);
}

.console-mobile-menu .console-nav__item.is-active {
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
}

.console-mobile-menu .console-nav__item.is-active .el-icon {
  color: var(--ch-primary);
}

.console-mobile-menu .console-exit {
  color: var(--ch-muted);
}

@media (max-width: 1080px) {
  .console-sidebar {
    display: none;
  }

  .console-menu-button {
    display: grid;
  }
}

@media (max-width: 640px) {
  .console-topbar {
    padding: 0 16px;
    height: 60px;
  }

  .console-breadcrumb span:first-child,
  .console-breadcrumb__sep {
    display: none;
  }

  .console-user-trigger span {
    display: none;
  }

  .console-content {
    padding: 20px 16px 40px;
  }
}
</style>
