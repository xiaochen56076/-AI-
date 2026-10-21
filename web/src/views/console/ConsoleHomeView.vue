<script setup lang="ts">
import { computed, onMounted, ref, type Component } from 'vue'
import { RouterLink } from 'vue-router'
import {
  ArrowRight,
  Calendar,
  Collection,
  DataAnalysis,
  Plus,
  Stamp,
  User,
} from '@element-plus/icons-vue'

import { myActivities } from '@/api/activities'
import { getDashboard } from '@/api/analytics'
import StatCard from '@/components/StatCard.vue'
import { useAuthStore } from '@/stores/auth'
import type { ActivityBrief, Dashboard } from '@/types'
import { activityStatusMeta, formatDateTime, formatPercent } from '@/utils/format'

interface QuickAction {
  title: string
  description: string
  to: string
  icon: Component
  permission: string
  accent: string
}

const auth = useAuthStore()

const loading = ref(false)
const dashboard = ref<Dashboard | null>(null)
const recent = ref<ActivityBrief[]>([])
const myTotal = ref(0)
const pendingTotal = ref(0)
const draftTotal = ref(0)
const publishedTotal = ref(0)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const today = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
}).format(new Date())

const actions = computed<QuickAction[]>(() =>
  [
    {
      title: '发布新活动',
      description: '创建草稿，完善信息后提交审核',
      to: '/console/activities/new',
      icon: Plus,
      permission: 'activity:create',
      accent: '#3757e8',
    },
    {
      title: '活动运营',
      description: '管理名下活动的名单、签到与数据',
      to: '/console/activities',
      icon: Calendar,
      permission: 'activity:create',
      accent: '#0d9488',
    },
    {
      title: '审核工作台',
      description: '处理待审核活动，给出审核意见',
      to: '/console/audit',
      icon: Stamp,
      permission: 'activity:audit',
      accent: '#d98a00',
    },
    {
      title: '全站看板',
      description: '掌握活动、报名与签到整体走势',
      to: '/console/dashboard',
      icon: DataAnalysis,
      permission: 'analytics:global',
      accent: '#7a5af8',
    },
    {
      title: '用户管理',
      description: '维护账号状态与角色分配',
      to: '/console/users',
      icon: User,
      permission: 'user:manage',
      accent: '#df5077',
    },
    {
      title: '字典管理',
      description: '管理活动分类与公共标签',
      to: '/console/dictionaries',
      icon: Collection,
      permission: 'dict:manage',
      accent: '#0f9f6e',
    },
  ].filter((item) => auth.hasPermission(item.permission)),
)

const hasWorkspace = computed(() => actions.value.length > 0)

async function loadOverview() {
  loading.value = true
  try {
    const tasks: Promise<unknown>[] = []
    if (auth.hasPermission('analytics:global')) {
      tasks.push(
        getDashboard().then((data) => {
          dashboard.value = data
        }),
      )
    }
    if (auth.hasPermission('activity:create')) {
      tasks.push(
        myActivities({ page: 1, page_size: 5 }).then((data) => {
          myTotal.value = data.total
          recent.value = data.results
        }),
        myActivities({ status: 1, page: 1, page_size: 1 }).then((data) => {
          pendingTotal.value = data.total
        }),
        myActivities({ status: 0, page: 1, page_size: 1 }).then((data) => {
          draftTotal.value = data.total
        }),
        myActivities({ status: 2, page: 1, page_size: 1 }).then((data) => {
          publishedTotal.value = data.total
        }),
      )
    }
    await Promise.all(tasks)
  } finally {
    loading.value = false
  }
}

onMounted(loadOverview)
</script>

<template>
  <div class="console-home" v-loading="loading">
    <section class="welcome-card">
      <div class="welcome-card__content">
        <span class="welcome-card__eyebrow">{{ today }} · CampusHub</span>
        <h1>{{ greeting }}，{{ auth.displayName }}</h1>
        <p>
          {{
            hasWorkspace
              ? '这里汇总了你可以使用的运营能力。选择一项任务继续，或先查看最近的活动进展。'
              : '当前账号还没有运营权限，你仍然可以浏览活动、报名和签到。'
          }}
        </p>
        <div class="welcome-card__actions">
          <el-button
            v-if="auth.hasPermission('activity:create')"
            type="primary"
            size="large"
            round
            :icon="Plus"
            @click="$router.push('/console/activities/new')"
          >
            发布活动
          </el-button>
          <el-button
            v-if="auth.hasPermission('activity:audit')"
            size="large"
            round
            :icon="Stamp"
            @click="$router.push('/console/audit')"
          >
            处理审核
          </el-button>
          <el-button v-if="!hasWorkspace" size="large" round @click="$router.push('/activities')">
            去活动广场
          </el-button>
        </div>
      </div>
      <div class="welcome-card__art">
        <div class="welcome-card__orbit orbit-one"></div>
        <div class="welcome-card__orbit orbit-two"></div>
        <div class="welcome-card__badge">
          <span>{{ auth.roles.map((role) => role.name).join(' · ') || '学生' }}</span>
          <strong>{{ auth.user?.college || 'CampusHub' }}</strong>
        </div>
      </div>
    </section>

    <template v-if="dashboard">
      <div class="console-section-head">
        <div>
          <h2>平台运行速览</h2>
          <p>数据每 5 分钟更新，进入全站看板可查看完整趋势。</p>
        </div>
        <RouterLink to="/console/dashboard" class="text-link">
          查看全站看板
          <el-icon><ArrowRight /></el-icon>
        </RouterLink>
      </div>
      <div class="stat-grid">
        <StatCard
          label="平台用户"
          :value="dashboard.totals.users"
          icon="User"
          tone="primary"
          hint="已注册账号"
        />
        <StatCard
          label="活动总数"
          :value="dashboard.totals.activities"
          icon="Calendar"
          tone="violet"
          hint="含草稿与历史活动"
        />
        <StatCard
          label="报名总量"
          :value="dashboard.totals.signups"
          icon="Tickets"
          tone="success"
          hint="全站累计报名"
        />
        <StatCard
          label="整体签到率"
          :value="formatPercent(dashboard.rates.checkin_rate)"
          icon="CircleCheck"
          tone="teal"
          :hint="`${dashboard.totals.checked_in} 人已完成签到`"
        />
      </div>
    </template>

    <template v-if="auth.hasPermission('activity:create')">
      <div class="console-section-head">
        <div>
          <h2>我的活动</h2>
          <p>草稿、待审核与已发布活动的实时状态。</p>
        </div>
        <RouterLink to="/console/activities" class="text-link">
          管理全部活动
          <el-icon><ArrowRight /></el-icon>
        </RouterLink>
      </div>
      <div class="stat-grid stat-grid--compact">
        <StatCard label="活动总数" :value="myTotal" icon="Files" tone="primary" hint="我创建的全部活动" />
        <StatCard label="待提交" :value="draftTotal" icon="EditPen" tone="warning" hint="草稿状态" />
        <StatCard label="待审核" :value="pendingTotal" icon="Clock" tone="violet" hint="等待审核结果" />
        <StatCard label="已发布" :value="publishedTotal" icon="Promotion" tone="success" hint="正在对外展示" />
      </div>

      <div class="recent-card">
        <div class="recent-card__head">
          <h3>最近编辑</h3>
          <RouterLink to="/console/activities" class="text-link">全部活动</RouterLink>
        </div>
        <div v-if="recent.length" class="recent-list">
          <RouterLink
            v-for="item in recent"
            :key="item.id"
            :to="`/console/activities/${item.id}/edit`"
            class="recent-item"
          >
            <div class="recent-item__main">
              <div class="recent-item__title">
                <span>{{ item.title }}</span>
                <span class="status-pill" :class="activityStatusMeta(item.status).className">
                  {{ item.status_text }}
                </span>
              </div>
              <div class="recent-item__meta">
                <span>{{ item.category.name }}</span>
                <span class="dot-separator"></span>
                <span>{{ formatDateTime(item.start_time) }}</span>
                <span class="dot-separator"></span>
                <span>{{ item.location }}</span>
              </div>
            </div>
            <div class="recent-item__side">
              <span>{{ item.signup_count }}/{{ item.capacity }}</span>
              <small>已报名</small>
            </div>
            <el-icon class="recent-item__arrow"><ArrowRight /></el-icon>
          </RouterLink>
        </div>
        <div v-else class="recent-empty">
          <p>还没有创建过活动，先发布一个试试？</p>
          <el-button type="primary" round @click="$router.push('/console/activities/new')">
            创建第一个活动
          </el-button>
        </div>
      </div>
    </template>

    <template v-if="hasWorkspace">
      <div class="console-section-head">
        <div>
          <h2>快捷入口</h2>
          <p>根据你的角色自动展示可用功能。</p>
        </div>
      </div>
      <div class="quick-grid">
        <button
          v-for="action in actions"
          :key="action.to"
          type="button"
          class="quick-card"
          :style="{ '--quick-accent': action.accent }"
          @click="$router.push(action.to)"
        >
          <span class="quick-card__icon">
            <el-icon><component :is="action.icon" /></el-icon>
          </span>
          <strong>{{ action.title }}</strong>
          <p>{{ action.description }}</p>
          <span class="quick-card__link">
            进入
            <el-icon><ArrowRight /></el-icon>
          </span>
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.console-home {
  display: flex;
  flex-direction: column;
  gap: 26px;
  min-height: 420px;
}

.welcome-card {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 32px;
  overflow: hidden;
  padding: 38px 42px;
  border-radius: 24px;
  background:
    radial-gradient(700px 300px at 8% -20%, rgba(255, 255, 255, 0.26), transparent 60%),
    linear-gradient(120deg, #1c2f6b 0%, #2444b8 52%, #3757e8 100%);
  color: #fff;
  box-shadow: 0 24px 60px rgba(36, 57, 168, 0.28);
}

.welcome-card__content {
  position: relative;
  z-index: 1;
  max-width: 620px;
}

.welcome-card__eyebrow {
  display: inline-flex;
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.82);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.06em;
}

.welcome-card h1 {
  margin-top: 16px;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.15;
  letter-spacing: -0.03em;
}

.welcome-card p {
  margin-top: 12px;
  max-width: 520px;
  color: rgba(255, 255, 255, 0.74);
  font-size: 14px;
  line-height: 1.7;
}

.welcome-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 26px;
}

.welcome-card__actions :deep(.el-button:not(.el-button--primary)) {
  border-color: rgba(255, 255, 255, 0.34);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.welcome-card__actions :deep(.el-button:not(.el-button--primary):hover) {
  border-color: #fff;
  background: rgba(255, 255, 255, 0.16);
}

.welcome-card__art {
  position: relative;
  flex: 0 0 220px;
  align-self: center;
  height: 180px;
}

.welcome-card__orbit {
  position: absolute;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 50%;
}

.orbit-one {
  inset: 8px 26px 8px 0;
  animation: float 6s ease-in-out infinite;
}

.orbit-two {
  inset: 42px 0 42px 52px;
  border-style: dashed;
  opacity: 0.6;
  animation: float 8s ease-in-out infinite reverse;
}

.welcome-card__badge {
  position: absolute;
  right: 18px;
  bottom: 22px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 18px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(12px);
}

.welcome-card__badge span {
  font-size: 11px;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.7);
}

.welcome-card__badge strong {
  font-size: 14px;
}

.console-section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: -8px;
}

.console-section-head h2 {
  font-size: 20px;
  letter-spacing: -0.01em;
}

.console-section-head p {
  margin-top: 3px;
  color: var(--ch-muted);
  font-size: 13px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-grid--compact :deep(.stat-card__value) {
  font-size: 24px;
}

.recent-card {
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  overflow: hidden;
}

.recent-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--ch-border);
}

.recent-card__head h3 {
  font-size: 15px;
}

.recent-list {
  display: flex;
  flex-direction: column;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 16px 22px;
  border-bottom: 1px solid #f1f4fa;
  transition: background 0.2s ease;
}

.recent-item:last-child {
  border-bottom: none;
}

.recent-item:hover {
  background: #f8faff;
}

.recent-item__main {
  flex: 1;
  min-width: 0;
}

.recent-item__title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 650;
  font-size: 14px;
}

.recent-item__title > span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-item__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 5px;
  color: var(--ch-muted-light);
  font-size: 12px;
}

.recent-item__side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex: 0 0 auto;
}

.recent-item__side span {
  font-weight: 700;
  font-size: 15px;
}

.recent-item__side small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.recent-item__arrow {
  color: var(--ch-muted-light);
}

.recent-empty {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 30px 22px;
  color: var(--ch-muted);
  font-size: 14px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.quick-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 22px;
  text-align: left;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.quick-card::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(120deg, color-mix(in srgb, var(--quick-accent) 7%, transparent), transparent 60%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.quick-card:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--quick-accent) 30%, var(--ch-border));
  box-shadow: var(--ch-shadow);
}

.quick-card:hover::after {
  opacity: 1;
}

.quick-card__icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 13px;
  background: color-mix(in srgb, var(--quick-accent) 12%, #fff);
  color: var(--quick-accent);
  font-size: 20px;
}

.quick-card strong {
  margin-top: 14px;
  font-size: 15px;
}

.quick-card p {
  margin-top: 6px;
  color: var(--ch-muted);
  font-size: 13px;
  line-height: 1.6;
}

.quick-card__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 16px;
  color: var(--quick-accent);
  font-size: 12px;
  font-weight: 700;
}

@media (max-width: 1080px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .welcome-card {
    padding: 28px 24px;
  }

  .welcome-card__art {
    display: none;
  }

  .stat-grid,
  .quick-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .recent-empty {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
