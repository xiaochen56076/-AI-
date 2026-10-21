<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Camera,
  Download,
  Location,
  Search,
  User,
} from '@element-plus/icons-vue'

import { getActivity } from '@/api/activities'
import { activityRoster, exportRoster } from '@/api/signups'
import EmptyState from '@/components/EmptyState.vue'
import StatCard from '@/components/StatCard.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import type { ActivityDetail, Signup } from '@/types'
import {
  activityStatusMeta,
  downloadBlob,
  formatDateTime,
  formatTimeRange,
  signupStatusMeta,
} from '@/utils/format'

const route = useRoute()
const router = useRouter()
const activityId = Number(route.params.id)

const loading = ref(true)
const rosterLoading = ref(false)
const exporting = ref(false)
const activity = ref<ActivityDetail | null>(null)
const rows = ref<Signup[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const status = ref('all')
const keyword = ref('')
const appliedKeyword = ref('')

const statusOptions = [
  { value: 'all', label: '全部状态' },
  { value: '0', label: '候补中' },
  { value: '1', label: '报名成功' },
  { value: '3', label: '已签到' },
  { value: '4', label: '未签到' },
  { value: '2', label: '已取消' },
]

const fillPercent = computed(() => {
  if (!activity.value?.capacity) return '0%'
  return `${Math.min(100, Math.round((activity.value.signup_count / activity.value.capacity) * 100))}%`
})

async function loadActivity() {
  try {
    activity.value = await getActivity(activityId)
  } catch {
    activity.value = null
  }
}

async function loadRoster() {
  rosterLoading.value = true
  try {
    const data = await activityRoster(activityId, {
      status: status.value === 'all' ? undefined : Number(status.value),
      keyword: appliedKeyword.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    rows.value = data.results
    total.value = data.total
  } catch {
    rows.value = []
    total.value = 0
  } finally {
    rosterLoading.value = false
  }
}

async function load() {
  loading.value = true
  await Promise.all([loadActivity(), loadRoster()])
  loading.value = false
}

function applyFilters() {
  appliedKeyword.value = keyword.value.trim()
  page.value = 1
  loadRoster()
}

function handleStatusChange() {
  page.value = 1
  loadRoster()
}

function handlePageChange(value: number) {
  page.value = value
  loadRoster()
}

async function handleExport() {
  exporting.value = true
  try {
    const response = await exportRoster(activityId)
    downloadBlob(response.data, `活动${activityId}-报名名单.csv`)
    ElMessage.success('报名名单已导出')
  } catch {
    // 接口错误由拦截器提示
  } finally {
    exporting.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="roster-page" v-loading="loading">
    <div class="page-head">
      <div>
        <button type="button" class="back-link" @click="router.push('/console/activities')">
          <el-icon><ArrowLeft /></el-icon>
          返回我的活动
        </button>
        <div class="page-head__title">
          <h1>{{ activity?.title || '报名名单' }}</h1>
          <span
            v-if="activity"
            class="status-pill"
            :class="activityStatusMeta(activity.status).className"
          >
            {{ activity.status_text }}
          </span>
        </div>
        <p v-if="activity" class="page-head__meta">
          <span><el-icon><Location /></el-icon>{{ activity.location }}</span>
          <span>{{ formatTimeRange(activity.start_time, activity.end_time) }}</span>
        </p>
      </div>
      <div class="page-head__actions">
        <el-button :icon="Camera" round @click="router.push(`/console/activities/${activityId}/checkin`)">
          签到管理
        </el-button>
        <el-button type="primary" :icon="Download" round :loading="exporting" @click="handleExport">
          导出 CSV
        </el-button>
      </div>
    </div>

    <div class="stat-grid">
      <StatCard
        label="报名成功"
        :value="activity?.signup_count ?? 0"
        icon="Tickets"
        tone="primary"
        :hint="`总名额 ${activity?.capacity ?? 0} 人`"
      />
      <StatCard
        label="已签到"
        :value="activity?.checked_in_count ?? 0"
        icon="CircleCheck"
        tone="success"
        :hint="activity?.signup_count ? `签到率 ${Math.round(((activity.checked_in_count || 0) / activity.signup_count) * 100)}%` : '暂无报名'"
      />
      <StatCard
        label="候补队列"
        :value="activity?.waitlist_count ?? 0"
        icon="Clock"
        tone="warning"
        hint="有空位时自动递补"
      />
      <div class="fill-card">
        <div class="fill-card__head">
          <span>名额使用</span>
          <strong>{{ fillPercent }}</strong>
        </div>
        <div class="fill-track">
          <span :style="{ width: fillPercent }"></span>
        </div>
        <p>剩余 {{ activity?.remaining ?? 0 }} 个名额</p>
      </div>
    </div>

    <div class="filter-bar">
      <el-select v-model="status" style="width: 150px" @change="handleStatusChange">
        <el-option
          v-for="option in statusOptions"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </el-select>
      <el-input
        v-model="keyword"
        placeholder="搜索学号、姓名或学院"
        :prefix-icon="Search"
        clearable
        style="width: 280px"
        @keyup.enter="applyFilters"
        @clear="applyFilters"
      />
      <el-button type="primary" @click="applyFilters">搜索</el-button>
      <div class="filter-spacer"></div>
      <span class="total-hint">共 {{ total }} 条报名记录</span>
    </div>

    <div class="table-card" v-loading="rosterLoading">
      <el-table v-if="rows.length" :data="rows" style="width: 100%">
        <el-table-column label="学生" min-width="220">
          <template #default="{ row }">
            <div class="student-cell">
              <UserAvatar :name="row.user.real_name" :src="row.user.avatar_url" :size="38" />
              <div>
                <strong>{{ row.user.real_name }}</strong>
                <span>{{ row.user.student_no }} · {{ row.user.nickname || '未设置昵称' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="学院 / 专业" min-width="200">
          <template #default="{ row }">
            <div class="dept-cell">
              <span>{{ row.user.college || '未填写学院' }}</span>
              <small>{{ row.user.major || '未填写专业' }}<template v-if="row.user.grade"> · {{ row.user.grade }} 级</template></small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="118">
          <template #default="{ row }">
            <span class="status-pill" :class="signupStatusMeta(row.status).className">
              {{ row.status_text }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="候补序号" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.status === 0" class="queue-pill">#{{ row.queue_position ?? row.queue_no ?? '-' }}</span>
            <span v-else class="muted-light">—</span>
          </template>
        </el-table-column>
        <el-table-column label="报名时间" min-width="160">
          <template #default="{ row }">
            <span class="table-muted">{{ formatDateTime(row.signup_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="签到情况" min-width="170">
          <template #default="{ row }">
            <div v-if="row.checked_in_at" class="checkin-cell">
              <strong>{{ formatDateTime(row.checked_in_at) }}</strong>
              <small>{{ row.checkin_method_text }}</small>
            </div>
            <span v-else class="muted-light">尚未签到</span>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="table-muted">{{ row.remark || '—' }}</span>
          </template>
        </el-table-column>
      </el-table>

      <EmptyState
        v-else-if="!rosterLoading"
        title="暂无报名记录"
        description="活动发布后，同学完成报名就会出现在这里。也可以切换筛选条件再试试。"
      >
        <el-button round :icon="User" @click="router.push(`/activities/${activityId}`)">查看活动详情</el-button>
      </EmptyState>
    </div>

    <div v-if="total > pageSize" class="pager-row">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.roster-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-height: 460px;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
}

.page-head__title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

.page-head h1 {
  max-width: 640px;
  font-size: 28px;
  letter-spacing: -0.03em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-head__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 8px;
  color: var(--ch-muted);
  font-size: 13px;
}

.page-head__meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.page-head__actions {
  display: flex;
  gap: 10px;
  flex: 0 0 auto;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: none;
  background: none;
  color: var(--ch-muted);
  font-family: inherit;
  font-size: 13px;
  cursor: pointer;
}

.back-link:hover {
  color: var(--ch-primary);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) 1.2fr;
  gap: 16px;
}

.fill-card {
  padding: 22px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.fill-card__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  color: var(--ch-muted);
  font-size: 13px;
}

.fill-card__head strong {
  color: var(--ch-ink);
  font-size: 24px;
  letter-spacing: -0.02em;
}

.fill-track {
  height: 8px;
  margin: 16px 0 10px;
  border-radius: 999px;
  background: #edf0f7;
  overflow: hidden;
}

.fill-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6b83f0, #3757e8);
  transition: width 0.4s ease;
}

.fill-card p {
  color: var(--ch-muted-light);
  font-size: 12px;
}

.total-hint {
  color: var(--ch-muted-light);
  font-size: 12px;
}

.student-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.student-cell div {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.student-cell strong {
  font-size: 13px;
  font-weight: 650;
}

.student-cell span {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.dept-cell {
  display: flex;
  flex-direction: column;
  font-size: 13px;
}

.dept-cell small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.queue-pill {
  display: inline-flex;
  padding: 2px 9px;
  border-radius: 999px;
  background: #fff6e6;
  color: #b77400;
  font-size: 12px;
  font-weight: 700;
}

.table-muted {
  color: var(--ch-muted);
  font-size: 12px;
}

.checkin-cell {
  display: flex;
  flex-direction: column;
}

.checkin-cell strong {
  font-size: 12px;
  font-weight: 600;
}

.checkin-cell small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.muted-light {
  color: var(--ch-muted-light);
  font-size: 12px;
}

@media (max-width: 1100px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-head h1 {
    white-space: normal;
  }

  .page-head__actions {
    width: 100%;
  }

  .stat-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .filter-bar :deep(.el-input),
  .filter-bar :deep(.el-select) {
    width: 100% !important;
  }
}
</style>
