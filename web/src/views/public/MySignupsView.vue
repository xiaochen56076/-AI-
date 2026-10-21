<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Camera, Clock, Location, Tickets } from '@element-plus/icons-vue'

import EmptyState from '@/components/EmptyState.vue'
import { cancelSignup, mySignups } from '@/api/signups'
import type { MySignup, MySignupQuery, Paginated } from '@/types'
import {
  categoryGradient,
  formatDateTime,
  formatMonthDay,
  formatTimeRange,
  formatWeekday,
  signupStatusMeta,
} from '@/utils/format'

type Group = 'all' | 'upcoming' | 'waitlist' | 'attended' | 'cancelled'

const router = useRouter()
const group = ref<Group>('all')
const page = ref(1)
const pageData = ref<Paginated<MySignup>>({ total: 0, page: 1, page_size: 8, results: [] })
const loading = ref(true)
const now = ref(Date.now())
let clock: number | null = null

const tabs: { value: Group; label: string; hint: string }[] = [
  { value: 'all', label: '全部', hint: '所有报名记录' },
  { value: 'upcoming', label: '待参加', hint: '已报名且未结束' },
  { value: 'waitlist', label: '候补中', hint: '等待名额释放' },
  { value: 'attended', label: '已参与', hint: '签到与未签到记录' },
  { value: 'cancelled', label: '已取消', hint: '取消的报名' },
]

const currentTab = computed(() => tabs.find((item) => item.value === group.value) ?? tabs[0])

function canCancel(item: MySignup) {
  const activity = item.activity
  return (
    [0, 1].includes(item.status) &&
    activity.status === 2 &&
    now.value <= Date.parse(activity.signup_end)
  )
}

function canCheckin(item: MySignup) {
  const activity = item.activity
  if (item.status !== 1 || activity.checkin_mode === 0 || activity.status !== 2) return false
  const start = Date.parse(activity.start_time) - 30 * 60 * 1000
  const end = Date.parse(activity.end_time)
  return now.value >= start && now.value <= end
}

async function load() {
  loading.value = true
  const query: MySignupQuery = { page: page.value, page_size: 8 }
  if (group.value !== 'all') query.group = group.value
  try {
    pageData.value = await mySignups(query)
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    loading.value = false
  }
}

function changeGroup(value: Group) {
  group.value = value
  page.value = 1
  void load()
}

function changePage(value: number) {
  page.value = value
  void load()
}

async function handleCancel(item: MySignup) {
  try {
    await ElMessageBox.confirm(
      `确认取消「${item.activity.title}」的报名吗？名额将释放给候补同学。`,
      '取消报名',
      { confirmButtonText: '取消报名', cancelButtonText: '保留报名', type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await cancelSignup(item.activity.id)
    ElMessage.success('报名已取消')
    if (pageData.value.results.length === 1 && page.value > 1) page.value -= 1
    await load()
  } catch {
    // 错误提示由请求拦截器统一处理
  }
}

function goCheckin(item: MySignup) {
  router.push({ name: 'checkin', query: { activity: String(item.activity.id) } })
}

onMounted(() => {
  void load()
  clock = window.setInterval(() => {
    now.value = Date.now()
  }, 30000)
})

onBeforeUnmount(() => {
  if (clock !== null) window.clearInterval(clock)
})
</script>

<template>
  <div class="my-signups">
    <section class="page-hero">
      <div class="page-container">
        <span class="eyebrow">My participation</span>
        <h1>我的报名</h1>
        <p>查看已报名的活动、候补进度与签到记录，不错过每一场期待。</p>
      </div>
    </section>

    <section class="page-container page-block">
      <div class="tab-row">
        <div class="group-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            type="button"
            class="group-tab"
            :class="{ 'is-active': group === tab.value }"
            @click="changeGroup(tab.value)"
          >
            <span>{{ tab.label }}</span>
            <small>{{ tab.hint }}</small>
          </button>
        </div>
      </div>

      <div v-if="loading" class="signup-list">
        <div v-for="item in 3" :key="item" class="signup-skeleton skeleton-block"></div>
      </div>

      <div v-else-if="pageData.results.length" class="signup-list">
        <article v-for="item in pageData.results" :key="item.id" class="signup-item surface">
          <RouterLink
            :to="`/activities/${item.activity.id}`"
            class="signup-cover"
            :style="{ background: categoryGradient(item.activity.category?.color) }"
          >
            <span class="signup-cover__date">
              <strong>{{ formatMonthDay(item.activity.start_time).replace('月', '/').replace('日', '') }}</strong>
              <small>{{ formatWeekday(item.activity.start_time) }}</small>
            </span>
          </RouterLink>

          <div class="signup-body">
            <div class="signup-head">
              <div class="signup-title">
                <span class="signup-category">{{ item.activity.category?.name }}</span>
                <RouterLink :to="`/activities/${item.activity.id}`">
                  {{ item.activity.title }}
                </RouterLink>
              </div>
              <span class="status-pill" :class="signupStatusMeta(item.status).className">
                {{ item.status_text }}
              </span>
            </div>

            <div class="signup-meta">
              <span>
                <el-icon><Calendar /></el-icon>
                {{ formatTimeRange(item.activity.start_time, item.activity.end_time) }}
              </span>
              <span>
                <el-icon><Location /></el-icon>
                {{ item.activity.location }}
              </span>
              <span>
                <el-icon><Clock /></el-icon>
                报名于 {{ formatDateTime(item.signup_at) }}
              </span>
            </div>

            <div v-if="item.status === 0" class="signup-note is-waitlist">
              当前候补序号 <strong>{{ item.queue_no ?? '—' }}</strong>，名额释放后将自动转正并发送通知。
            </div>
            <div v-else-if="item.status === 3" class="signup-note is-success">
              已于 {{ formatDateTime(item.checked_in_at) }} 完成签到
              <template v-if="item.checkin_method_text">（{{ item.checkin_method_text }}）</template>
            </div>

            <div class="signup-actions">
              <RouterLink :to="`/activities/${item.activity.id}`">
                <el-button text>查看活动</el-button>
              </RouterLink>
              <el-button v-if="canCheckin(item)" type="success" plain @click="goCheckin(item)">
                <el-icon style="margin-right: 4px"><Camera /></el-icon>
                去签到
              </el-button>
              <el-button v-if="canCancel(item)" text type="danger" @click="handleCancel(item)">
                取消报名
              </el-button>
            </div>
          </div>
        </article>
      </div>

      <EmptyState
        v-else
        :title="group === 'all' ? '还没有报名记录' : `暂无${currentTab.label}的活动`"
        :description="
          group === 'all'
            ? '去活动广场挑一场感兴趣的活动，开启你的校园体验。'
            : '换一个分类看看，或者去活动广场发现更多内容。'
        "
      >
        <RouterLink to="/activities">
          <el-button type="primary" round :icon="Tickets">去活动广场</el-button>
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
.tab-row {
  margin-bottom: 24px;
}

.group-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px;
  border: 1px solid var(--ch-border);
  border-radius: 14px;
  background: #fff;
}

.group-tab {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
  flex: 1;
  min-width: 120px;
  padding: 10px 16px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--ch-muted);
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.group-tab span {
  font-size: 13.5px;
  font-weight: 600;
}

.group-tab small {
  color: var(--ch-muted-light);
  font-size: 10.5px;
}

.group-tab:hover {
  background: #f7f9fe;
  color: var(--ch-ink);
}

.group-tab.is-active {
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
}

.group-tab.is-active small {
  color: #7b8fdc;
}

.signup-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.signup-skeleton {
  height: 176px;
}

.signup-item {
  display: flex;
  gap: 20px;
  padding: 18px;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.signup-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--ch-shadow);
}

.signup-cover {
  position: relative;
  flex: 0 0 112px;
  height: 140px;
  border-radius: 13px;
  overflow: hidden;
}

.signup-cover::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.18) 1px, transparent 1px);
  background-size: 16px 16px;
}

.signup-cover__date {
  position: absolute;
  left: 12px;
  top: 12px;
  z-index: 1;
  display: flex;
  flex-direction: column;
  color: #fff;
  line-height: 1.2;
}

.signup-cover__date strong {
  font-size: 21px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.signup-cover__date small {
  font-size: 10px;
  opacity: 0.7;
}

.signup-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.signup-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.signup-title {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.signup-category {
  color: var(--ch-primary);
  font-size: 11px;
  font-weight: 700;
}

.signup-title a {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 16.5px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.signup-title a:hover {
  color: var(--ch-primary);
}

.signup-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 10px;
  color: var(--ch-muted);
  font-size: 12px;
}

.signup-meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.signup-meta .el-icon {
  color: var(--ch-muted-light);
}

.signup-note {
  align-self: flex-start;
  margin-top: 10px;
  padding: 6px 11px;
  border-radius: 8px;
  font-size: 11.5px;
}

.signup-note.is-waitlist {
  background: #fff8ea;
  color: #9b701f;
}

.signup-note.is-success {
  background: #effaf6;
  color: #0b8a5f;
}

.signup-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  margin-top: auto;
  padding-top: 10px;
}

.signup-actions .el-button {
  margin-left: 0;
}

@media (max-width: 720px) {
  .group-tabs {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .group-tab {
    min-width: 0;
  }

  .signup-item {
    gap: 14px;
    padding: 14px;
  }

  .signup-cover {
    flex-basis: 78px;
    height: 106px;
  }

  .signup-cover__date strong {
    font-size: 17px;
  }

  .signup-meta {
    flex-direction: column;
    gap: 5px;
  }

  .signup-actions {
    justify-content: flex-start;
  }
}
</style>
