<script setup lang="ts">
import { computed, onMounted, ref, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  AlarmClock,
  Bell,
  CircleCheck,
  Clock,
  Promotion,
  Select,
  Stamp,
  Warning,
} from '@element-plus/icons-vue'

import EmptyState from '@/components/EmptyState.vue'
import { listNotifications } from '@/api/notifications'
import { useNotificationsStore } from '@/stores/notifications'
import type { Notification, NotificationQuery, Paginated } from '@/types'
import { notificationMeta, relativeTime } from '@/utils/format'

type StatusFilter = '' | 'unread' | 'read'

const router = useRouter()
const store = useNotificationsStore()

const status = ref<StatusFilter>('')
const type = ref('')
const page = ref(1)
const pageData = ref<Paginated<Notification>>({ total: 0, page: 1, page_size: 10, results: [] })
const loading = ref(true)
const markingAll = ref(false)

const iconMap: Record<string, Component> = {
  Bell,
  CircleCheck,
  Clock,
  Promotion,
  AlarmClock,
  Warning,
  Stamp,
  Select,
}

const typeOptions = [
  { value: '', label: '全部类型' },
  ...[0, 1, 2, 3, 4, 5, 6, 7].map((item) => ({ value: String(item), label: notificationMeta(item).label })),
]

const tabs: { value: StatusFilter; label: string }[] = [
  { value: '', label: '全部消息' },
  { value: 'unread', label: '未读' },
  { value: 'read', label: '已读' },
]

const unreadLabel = computed(() => (store.unread > 0 ? `未读 ${store.unread}` : '暂无未读'))

async function load() {
  loading.value = true
  const query: NotificationQuery = { page: page.value, page_size: 10 }
  if (status.value) query.status = status.value
  if (type.value) query.type = Number(type.value)
  try {
    pageData.value = await listNotifications(query)
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    loading.value = false
  }
}

function changeStatus(value: StatusFilter) {
  status.value = value
  page.value = 1
  void load()
}

function changeType(value: string) {
  type.value = value
  page.value = 1
  void load()
}

function changePage(value: number) {
  page.value = value
  void load()
}

function metaFor(item: Notification) {
  return notificationMeta(item.type)
}

async function openNotification(item: Notification) {
  if (!item.is_read) {
    try {
      await store.markRead(item.id)
      item.is_read = true
    } catch {
      // 已读标记失败不阻塞跳转
    }
  }
  if (item.activity_id) {
    router.push(`/activities/${item.activity_id}`)
  }
}

async function markItemRead(item: Notification) {
  try {
    await store.markRead(item.id)
    item.is_read = true
    ElMessage.success('已标记为已读')
    if (status.value === 'unread') await load()
  } catch {
    // 错误提示由请求拦截器统一处理
  }
}

async function markAll() {
  if (store.unread === 0) return
  markingAll.value = true
  try {
    const result = await store.markAllRead()
    ElMessage.success(`已将 ${result.updated} 条消息标记为已读`)
    await load()
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    markingAll.value = false
  }
}

onMounted(async () => {
  await load()
  await store.refreshUnread()
})
</script>

<template>
  <div class="notifications-page">
    <section class="page-hero">
      <div class="page-container notifications-hero">
        <div>
          <span class="eyebrow">Inbox</span>
          <h1>消息中心</h1>
          <p>报名结果、候补转正、活动提醒与审核通知，都会在这里找到。</p>
        </div>
        <div class="hero-bell">
          <el-badge :value="store.unread" :hidden="store.unread === 0" :max="99">
            <span class="hero-bell__icon"><el-icon><Bell /></el-icon></span>
          </el-badge>
          <span>{{ unreadLabel }}</span>
        </div>
      </div>
    </section>

    <section class="page-container page-block">
      <div class="notifications-toolbar surface">
        <div class="status-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            type="button"
            class="status-tab"
            :class="{ 'is-active': status === tab.value }"
            @click="changeStatus(tab.value)"
          >
            {{ tab.label }}
          </button>
        </div>
        <div class="toolbar-right">
          <el-select :model-value="type" class="type-select" @update:model-value="changeType">
            <el-option
              v-for="item in typeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-button
            plain
            :loading="markingAll"
            :disabled="store.unread === 0"
            :icon="Select"
            @click="markAll"
          >
            全部已读
          </el-button>
        </div>
      </div>

      <div v-if="loading" class="notification-list">
        <div v-for="item in 4" :key="item" class="notification-skeleton skeleton-block"></div>
      </div>

      <div v-else-if="pageData.results.length" class="notification-list">
        <article
          v-for="item in pageData.results"
          :key="item.id"
          class="notification-item surface"
          :class="{ 'is-unread': !item.is_read }"
          @click="openNotification(item)"
        >
          <span
            class="notification-icon"
            :style="{
              background: metaFor(item).background,
              color: metaFor(item).color,
            }"
          >
            <el-icon><component :is="iconMap[metaFor(item).icon]" /></el-icon>
          </span>

          <div class="notification-body">
            <div class="notification-head">
              <div class="notification-title">
                <span class="type-label" :style="{ color: metaFor(item).color }">
                  {{ metaFor(item).label }}
                </span>
                <strong>{{ item.title }}</strong>
                <span v-if="!item.is_read" class="unread-dot"></span>
              </div>
              <span class="notification-time">{{ relativeTime(item.created_at) }}</span>
            </div>
            <p>{{ item.content }}</p>
            <div class="notification-foot">
              <span v-if="item.activity_title" class="activity-link">
                <el-icon><Link /></el-icon>
                {{ item.activity_title }}
              </span>
              <button
                v-if="!item.is_read"
                type="button"
                class="read-button"
                @click.stop="markItemRead(item)"
              >
                标记已读
              </button>
            </div>
          </div>
        </article>
      </div>

      <EmptyState
        v-else
        title="暂无消息"
        description="报名活动或等待审核结果时，相关通知会出现在这里。"
      >
        <RouterLink to="/activities">
          <el-button round>去逛逛活动</el-button>
        </RouterLink>
      </EmptyState>

      <div v-if="pageData.total > pageData.page_size" class="pager-row">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="pageData.total"
          :page-size="pageData.page_size"
          :current-page="pageData.page"
          @current-change="changePage"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
.notifications-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.hero-bell {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid var(--ch-border);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.8);
  color: var(--ch-muted);
  font-size: 12px;
  backdrop-filter: blur(10px);
}

.hero-bell__icon {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  font-size: 18px;
}

.notifications-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  padding: 14px 16px;
}

.status-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: 10px;
  background: #f4f6fb;
}

.status-tab {
  padding: 7px 15px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--ch-muted);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.status-tab.is-active {
  background: #fff;
  color: var(--ch-primary);
  box-shadow: 0 2px 8px rgba(16, 26, 51, 0.08);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.type-select {
  width: 130px;
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-skeleton {
  height: 130px;
}

.notification-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.notification-item:hover {
  transform: translateY(-2px);
  border-color: rgba(55, 87, 232, 0.2);
  box-shadow: var(--ch-shadow);
}

.notification-item.is-unread {
  border-left: 3px solid var(--ch-primary);
  background: linear-gradient(90deg, rgba(238, 242, 255, 0.55), #fff 32%);
}

.notification-icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  font-size: 20px;
}

.notification-body {
  flex: 1;
  min-width: 0;
}

.notification-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.notification-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.type-label {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.notification-title strong {
  font-size: 14px;
  font-weight: 650;
  line-height: 1.45;
}

.unread-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ch-primary);
}

.notification-time {
  flex: 0 0 auto;
  color: var(--ch-muted-light);
  font-size: 11px;
}

.notification-body > p {
  margin-top: 6px;
  color: var(--ch-muted);
  font-size: 12.5px;
  line-height: 1.7;
}

.notification-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
}

.activity-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ch-primary);
  font-size: 11.5px;
  font-weight: 500;
}

.read-button {
  padding: 3px 8px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--ch-muted-light);
  font-size: 11.5px;
  cursor: pointer;
}

.read-button:hover {
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
}

@media (max-width: 720px) {
  .notifications-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .notifications-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .status-tabs {
    width: 100%;
  }

  .status-tab {
    flex: 1;
  }

  .toolbar-right {
    justify-content: space-between;
  }

  .notification-item {
    padding: 16px;
  }

  .notification-time {
    display: none;
  }
}
</style>
