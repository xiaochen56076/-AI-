<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Calendar,
  CircleCheck,
  CircleClose,
  Clock,
  Document,
  Location,
  Search,
  Stamp,
  Tickets,
  User,
} from '@element-plus/icons-vue'

import { listAudits, reviewActivity } from '@/api/activities'
import EmptyState from '@/components/EmptyState.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import type { ActivityDetail } from '@/types'
import {
  activityStatusMeta,
  formatDateTime,
  formatTimeRange,
} from '@/utils/format'

const tabs = [
  { value: '1', label: '待审核', tone: 'pending' },
  { value: '2', label: '已通过', tone: 'approved' },
  { value: '5', label: '已驳回', tone: 'rejected' },
  { value: 'all', label: '全部', tone: 'all' },
]

const loading = ref(true)
const list = ref<ActivityDetail[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const activeTab = ref('1')
const keyword = ref('')
const appliedKeyword = ref('')
const counts = ref({ pending: 0, approved: 0, rejected: 0 })

const drawerVisible = ref(false)
const selected = ref<ActivityDetail | null>(null)
const auditComment = ref('')
const actionLoading = ref<'approve' | 'reject' | null>(null)

const statusFilter = computed(() =>
  activeTab.value === 'all' ? 'all' : activeTab.value,
)

function tabCount(value: string) {
  if (value === '1') return counts.value.pending
  if (value === '2') return counts.value.approved
  if (value === '5') return counts.value.rejected
  return null
}

async function loadCounts() {
  try {
    const [pending, approved, rejected] = await Promise.all([
      listAudits({ status: 1, page: 1, page_size: 1 }),
      listAudits({ status: 2, page: 1, page_size: 1 }),
      listAudits({ status: 5, page: 1, page_size: 1 }),
    ])
    counts.value = {
      pending: pending.total,
      approved: approved.total,
      rejected: rejected.total,
    }
  } catch {
    // 接口错误由拦截器提示
  }
}

async function load() {
  loading.value = true
  try {
    const data = await listAudits({
      status: statusFilter.value,
      keyword: appliedKeyword.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    list.value = data.results
    total.value = data.total
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await Promise.all([load(), loadCounts()])
}

function selectTab(value: string) {
  if (activeTab.value === value) return
  activeTab.value = value
  page.value = 1
  load()
}

function applyFilters() {
  appliedKeyword.value = keyword.value.trim()
  page.value = 1
  load()
}

function resetFilters() {
  keyword.value = ''
  appliedKeyword.value = ''
  page.value = 1
  load()
}

function handlePageChange(value: number) {
  page.value = value
  load()
}

function openDetail(item: ActivityDetail) {
  selected.value = item
  auditComment.value = ''
  drawerVisible.value = true
}

async function handleReview(action: 1 | 2) {
  if (!selected.value) return
  if (action === 2 && auditComment.value.trim().length < 2) {
    ElMessage.warning('驳回活动时请填写至少 2 个字的审核意见')
    return
  }
  actionLoading.value = action === 1 ? 'approve' : 'reject'
  try {
    await reviewActivity(selected.value.id, action, auditComment.value.trim())
    ElMessage.success(action === 1 ? '活动已通过审核并发布' : '活动已驳回，主办方将收到通知')
    drawerVisible.value = false
    selected.value = null
    auditComment.value = ''
    await refreshAll()
  } catch {
    // 接口错误由拦截器提示
  } finally {
    actionLoading.value = null
  }
}

onMounted(refreshAll)
</script>

<template>
  <div class="audit-page">
    <div class="page-head">
      <div>
        <span class="eyebrow">Content review</span>
        <h1>审核工作台</h1>
        <p>审核主办方提交的活动，确保信息真实、合规、完整。</p>
      </div>
      <div class="pending-badge">
        <span class="pending-badge__dot"></span>
        当前待审核 <strong>{{ counts.pending }}</strong> 个活动
      </div>
    </div>

    <div class="toolbar">
      <div class="audit-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          type="button"
          class="audit-tab"
          :class="[`tone-${tab.tone}`, { 'is-active': activeTab === tab.value }]"
          @click="selectTab(tab.value)"
        >
          {{ tab.label }}
          <span v-if="tabCount(tab.value) !== null">{{ tabCount(tab.value) }}</span>
        </button>
      </div>
      <div class="toolbar__search">
        <el-input
          v-model="keyword"
          placeholder="搜索活动标题或主办方"
          :prefix-icon="Search"
          clearable
          @keyup.enter="applyFilters"
          @clear="applyFilters"
        />
        <el-button @click="applyFilters">搜索</el-button>
        <el-button v-if="appliedKeyword" text @click="resetFilters">重置</el-button>
      </div>
    </div>

    <div v-loading="loading" class="audit-stack">
      <article v-for="item in list" :key="item.id" class="audit-card">
        <div class="audit-card__main">
          <div class="audit-card__title">
            <span class="status-pill" :class="activityStatusMeta(item.status).className">
              {{ item.status_text }}
            </span>
            <h2>{{ item.title }}</h2>
          </div>
          <p class="audit-card__summary">
            {{ item.summary || item.description.slice(0, 120) || '主办方暂未填写活动简介。' }}
          </p>
          <div class="audit-card__meta">
            <span><el-icon><Calendar /></el-icon>{{ formatTimeRange(item.start_time, item.end_time) }}</span>
            <span><el-icon><Location /></el-icon>{{ item.location }}</span>
            <span><el-icon><Tickets /></el-icon>{{ item.capacity }} 人</span>
            <span><el-icon><Clock /></el-icon>更新于 {{ formatDateTime(item.updated_at) }}</span>
          </div>
          <div class="audit-card__tags">
            <span class="soft-chip">{{ item.category.name }}</span>
            <span v-for="tag in item.tags" :key="tag.id" class="tag-chip">{{ tag.name }}</span>
          </div>
        </div>

        <div class="audit-card__side">
          <div class="organizer">
            <UserAvatar
              :name="item.organizer.display_name"
              :src="item.organizer.avatar_url"
              :size="34"
            />
            <div>
              <strong>{{ item.organizer.display_name }}</strong>
              <span>{{ item.organizer.college || '未填写学院' }}</span>
            </div>
          </div>
          <el-button
            type="primary"
            round
            :icon="item.status === 1 ? Stamp : Document"
            @click="openDetail(item)"
          >
            {{ item.status === 1 ? '进入审核' : '查看详情' }}
          </el-button>
        </div>
      </article>

      <EmptyState
        v-if="!loading && !list.length"
        :title="appliedKeyword ? '没有匹配的审核记录' : activeTab === '1' ? '审核队列已清空' : '这里还没有审核记录'"
        :description="
          appliedKeyword
            ? '试试其他关键词，或清空搜索条件。'
            : activeTab === '1'
              ? '所有提交的活动都已完成审核，做得不错。'
              : '主办方提交审核后，记录会出现在这里。'
        "
      >
        <el-button v-if="appliedKeyword" round @click="resetFilters">清空搜索</el-button>
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

    <el-drawer
      v-model="drawerVisible"
      title="活动审核"
      size="min(680px, 94%)"
      :destroy-on-close="true"
    >
      <div v-if="selected" class="audit-detail">
        <div class="audit-detail__header">
          <span class="status-pill" :class="activityStatusMeta(selected.status).className">
            {{ selected.status_text }}
          </span>
          <h2>{{ selected.title }}</h2>
          <div class="audit-detail__organizer">
            <UserAvatar
              :name="selected.organizer.display_name"
              :src="selected.organizer.avatar_url"
              :size="36"
            />
            <div>
              <strong>{{ selected.organizer.display_name }}</strong>
              <span>
                {{ selected.organizer.college || '未填写学院' }}
                <template v-if="selected.club?.name">· {{ selected.club.name }}</template>
              </span>
            </div>
          </div>
        </div>

        <div class="detail-grid">
          <div>
            <span>活动分类</span>
            <strong>{{ selected.category.name }}</strong>
          </div>
          <div>
            <span>活动时间</span>
            <strong>{{ formatTimeRange(selected.start_time, selected.end_time) }}</strong>
          </div>
          <div>
            <span>报名时间</span>
            <strong>{{ formatTimeRange(selected.signup_start, selected.signup_end) }}</strong>
          </div>
          <div>
            <span>活动地点</span>
            <strong>{{ selected.location }}</strong>
          </div>
          <div>
            <span>人数上限</span>
            <strong>{{ selected.capacity }} 人</strong>
          </div>
          <div>
            <span>签到方式</span>
            <strong>{{ selected.checkin_mode_text }}</strong>
          </div>
        </div>

        <div class="detail-section">
          <h3>活动简介</h3>
          <p>{{ selected.summary || '主办方未填写简介。' }}</p>
        </div>

        <div class="detail-section">
          <h3>活动详情</h3>
          <p class="detail-description">{{ selected.description || '主办方未填写活动详情。' }}</p>
        </div>

        <div v-if="selected.tags.length" class="detail-section">
          <h3>活动标签</h3>
          <div class="detail-tags">
            <span v-for="tag in selected.tags" :key="tag.id" class="tag-chip">{{ tag.name }}</span>
          </div>
        </div>

        <div v-if="selected.audit_records.length" class="detail-section">
          <h3>审核记录</h3>
          <div class="audit-timeline">
            <div v-for="record in selected.audit_records" :key="record.id" class="audit-timeline__item">
              <div class="timeline-head">
                <strong>{{ record.action_text }}</strong>
                <span>{{ formatDateTime(record.created_at) }}</span>
              </div>
              <p v-if="record.comment">{{ record.comment }}</p>
              <small>审核人：{{ record.auditor_name }}</small>
            </div>
          </div>
        </div>

        <div v-if="selected.status === 1" class="review-panel">
          <h3>审核意见</h3>
          <el-input
            v-model="auditComment"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            placeholder="通过时可选填建议；驳回时请说明具体原因，至少 2 个字。"
          />
          <div class="review-actions">
            <el-button
              type="danger"
              plain
              round
              :icon="CircleClose"
              :loading="actionLoading === 'reject'"
              :disabled="Boolean(actionLoading)"
              @click="handleReview(2)"
            >
              驳回活动
            </el-button>
            <el-button
              type="primary"
              round
              :icon="CircleCheck"
              :loading="actionLoading === 'approve'"
              :disabled="Boolean(actionLoading)"
              @click="handleReview(1)"
            >
              通过并发布
            </el-button>
          </div>
        </div>

        <div v-else class="review-note">
          <el-icon><User /></el-icon>
          该活动已于 {{ formatDateTime(selected.updated_at) }} 完成审核，当前状态为「{{ selected.status_text }}」。
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.audit-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-height: 460px;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.page-head h1 {
  margin-top: 10px;
  font-size: 30px;
  letter-spacing: -0.03em;
}

.page-head p {
  margin-top: 6px;
  color: var(--ch-muted);
  font-size: 14px;
}

.pending-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 999px;
  background: #fff6e6;
  color: #a56a00;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.pending-badge__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #d98a00;
  box-shadow: 0 0 0 4px rgba(217, 138, 0, 0.16);
}

.pending-badge strong {
  font-size: 15px;
}

.toolbar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 18px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.audit-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-self: flex-start;
  padding: 4px;
  border-radius: 12px;
  background: var(--ch-bg);
}

.audit-tab {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 15px;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: var(--ch-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
}

.audit-tab span {
  display: inline-grid;
  place-items: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(16, 26, 51, 0.06);
  font-size: 11px;
}

.audit-tab:hover {
  color: var(--ch-ink);
}

.audit-tab.is-active {
  background: #fff;
  color: var(--ch-primary);
  box-shadow: 0 3px 10px rgba(20, 34, 79, 0.1);
}

.audit-tab.is-active span {
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
}

.audit-tab.tone-approved.is-active {
  color: var(--ch-success);
}

.audit-tab.tone-rejected.is-active {
  color: var(--ch-danger);
}

.toolbar__search {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 520px;
}

.audit-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 160px;
}

.audit-card {
  display: flex;
  gap: 24px;
  padding: 22px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.audit-card:hover {
  border-color: var(--ch-border-strong);
  box-shadow: var(--ch-shadow);
}

.audit-card__main {
  flex: 1;
  min-width: 0;
}

.audit-card__title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.audit-card__title h2 {
  font-size: 17px;
  letter-spacing: -0.01em;
}

.audit-card__summary {
  margin-top: 8px;
  color: var(--ch-muted);
  font-size: 13px;
  line-height: 1.65;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.audit-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 10px;
  color: var(--ch-muted-light);
  font-size: 12px;
}

.audit-card__meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.audit-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.audit-card__side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex: 0 0 180px;
}

.organizer {
  display: flex;
  align-items: center;
  gap: 9px;
}

.organizer div {
  display: flex;
  flex-direction: column;
  text-align: left;
}

.organizer strong {
  font-size: 12px;
  font-weight: 650;
}

.organizer span {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.audit-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 20px;
}

.audit-detail__header h2 {
  margin-top: 10px;
  font-size: 22px;
  letter-spacing: -0.02em;
}

.audit-detail__organizer {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}

.audit-detail__organizer div {
  display: flex;
  flex-direction: column;
}

.audit-detail__organizer strong {
  font-size: 13px;
}

.audit-detail__organizer span {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 16px;
  border-radius: 14px;
  background: #fafbfe;
  border: 1px solid #eff2f9;
}

.detail-grid div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.detail-grid span {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.detail-grid strong {
  font-size: 12px;
  font-weight: 600;
}

.detail-section h3 {
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-section p {
  color: var(--ch-muted);
  font-size: 13px;
  line-height: 1.8;
}

.detail-description {
  white-space: pre-wrap;
  padding: 16px;
  border-radius: 12px;
  background: #fafbfe;
  border: 1px solid #eff2f9;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.timeline-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.timeline-head strong {
  font-size: 13px;
}

.timeline-head span,
.audit-timeline__item small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.audit-timeline__item p {
  margin: 5px 0;
  color: var(--ch-muted);
  font-size: 12px;
}

.review-panel {
  padding: 18px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid var(--ch-border);
  box-shadow: 0 10px 30px rgba(20, 34, 79, 0.06);
}

.review-panel h3 {
  margin-bottom: 10px;
  font-size: 14px;
}

.review-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 14px;
}

.review-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 12px;
  background: #fafbfe;
  border: 1px dashed var(--ch-border);
  color: var(--ch-muted);
  font-size: 12px;
}

@media (max-width: 820px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .audit-card {
    flex-direction: column;
  }

  .audit-card__side {
    flex-direction: row;
    align-items: center;
    flex: auto;
  }

  .detail-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .toolbar__search {
    flex-wrap: wrap;
  }
}
</style>
