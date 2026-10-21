<script setup lang="ts">
import { computed, onMounted, ref, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Calendar,
  Clock,
  Close,
  DataLine,
  Document,
  EditPen,
  Flag,
  Location,
  MoreFilled,
  Plus,
  Promotion,
  Search,
  Tickets,
  View,
} from '@element-plus/icons-vue'

import {
  cancelActivity,
  myActivities,
  submitActivity,
} from '@/api/activities'
import EmptyState from '@/components/EmptyState.vue'
import type { ActivityBrief } from '@/types'
import {
  activityStatusMeta,
  categoryGradient,
  formatTimeRange,
} from '@/utils/format'

const router = useRouter()

const statusTabs = [
  { value: 'all', label: '全部活动' },
  { value: '0', label: '草稿' },
  { value: '1', label: '待审核' },
  { value: '2', label: '已发布' },
  { value: '3', label: '已结束' },
  { value: '5', label: '已驳回' },
  { value: '4', label: '已取消' },
]

const loading = ref(false)
const list = ref<ActivityBrief[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const activeStatus = ref('all')
const keyword = ref('')
const appliedKeyword = ref('')

const cancelVisible = ref(false)
const cancelTarget = ref<ActivityBrief | null>(null)
const cancelReason = ref('')
const cancelLoading = ref(false)

const statusFilter = computed(() =>
  activeStatus.value === 'all' ? undefined : Number(activeStatus.value),
)

const cancelNeedsReason = computed(() =>
  cancelTarget.value ? [1, 2].includes(cancelTarget.value.status) : false,
)

const iconMap: Record<string, Component> = {
  Calendar,
  Promotion,
  Flag,
  Tickets,
  Document,
}

function categoryIcon(item: ActivityBrief) {
  return iconMap[item.category?.icon || ''] ?? Calendar
}

function percentOf(item: ActivityBrief) {
  if (!item.capacity) return 0
  return Math.min(100, Math.round((item.signup_count / item.capacity) * 100))
}

function canEdit(item: ActivityBrief) {
  return [0, 2, 5].includes(item.status)
}

function canSubmit(item: ActivityBrief) {
  return [0, 5].includes(item.status)
}

function canCancel(item: ActivityBrief) {
  return ![3, 4].includes(item.status)
}

function statusHint(item: ActivityBrief) {
  if (item.status === 1) return '已进入审核队列，审核期间暂不可编辑。'
  if (item.status === 2) return '已发布活动仅支持修改简介、详情、封面和标签。'
  if (item.status === 5) return '根据审核意见调整后，可重新提交审核。'
  if (item.status === 0) return '完善活动信息并提交审核后，活动才会对外展示。'
  return ''
}

async function load() {
  loading.value = true
  try {
    const data = await myActivities({
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

function selectStatus(value: string) {
  if (activeStatus.value === value) return
  activeStatus.value = value
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
  activeStatus.value = 'all'
  page.value = 1
  load()
}

function handlePageChange(value: number) {
  page.value = value
  load()
}

function goDetail(item: ActivityBrief) {
  router.push(`/activities/${item.id}`)
}

function goEdit(item: ActivityBrief) {
  router.push(`/console/activities/${item.id}/edit`)
}

async function handleCommand(command: string, item: ActivityBrief) {
  if (command === 'view') return goDetail(item)
  if (command === 'edit') return goEdit(item)
  if (command === 'roster') return router.push(`/console/activities/${item.id}/roster`)
  if (command === 'checkin') return router.push(`/console/activities/${item.id}/checkin`)
  if (command === 'stats') return router.push(`/console/activities/${item.id}/stats`)
  if (command === 'submit') {
    try {
      await ElMessageBox.confirm(
        '提交后活动将进入审核队列，审核期间不可编辑。确认提交吗？',
        '提交审核',
        { type: 'warning', confirmButtonText: '提交审核', cancelButtonText: '再检查一下' },
      )
      await submitActivity(item.id)
      ElMessage.success('已提交审核，请等待审核结果')
      await load()
    } catch {
      // 用户取消或接口已提示错误
    }
    return
  }
  if (command === 'cancel') {
    cancelTarget.value = item
    cancelReason.value = ''
    cancelVisible.value = true
  }
}

async function confirmCancel() {
  if (!cancelTarget.value) return
  if (cancelNeedsReason.value && !cancelReason.value.trim()) {
    ElMessage.warning('下架已进入审核或已发布的活动需要填写原因')
    return
  }
  cancelLoading.value = true
  try {
    await cancelActivity(cancelTarget.value.id, cancelReason.value.trim())
    ElMessage.success('活动已取消，相关报名已同步处理')
    cancelVisible.value = false
    cancelTarget.value = null
    cancelReason.value = ''
    await load()
  } catch {
    // 接口错误已由拦截器提示
  } finally {
    cancelLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="organizer-activities">
    <div class="page-head">
      <div>
        <span class="eyebrow">Activity operations</span>
        <h1>我的活动</h1>
        <p>创建、提交审核并运营你名下的全部校园活动。</p>
      </div>
      <el-button
        type="primary"
        size="large"
        round
        :icon="Plus"
        @click="router.push('/console/activities/new')"
      >
        发布新活动
      </el-button>
    </div>

    <div class="toolbar">
      <div class="scope-tabs">
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          type="button"
          class="scope-tab"
          :class="{ 'is-active': activeStatus === tab.value }"
          @click="selectStatus(tab.value)"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="toolbar__search">
        <el-input
          v-model="keyword"
          placeholder="搜索活动标题或地点"
          :prefix-icon="Search"
          clearable
          @keyup.enter="applyFilters"
          @clear="applyFilters"
        />
        <el-button @click="applyFilters">搜索</el-button>
        <el-button text :icon="Close" @click="resetFilters">重置</el-button>
      </div>
    </div>

    <div v-loading="loading" class="activity-stack">
      <article v-for="item in list" :key="item.id" class="org-activity">
        <div class="org-activity__thumb" :style="{ background: categoryGradient(item.category?.color) }">
          <img v-if="item.cover_url" :src="item.cover_url" :alt="item.title" loading="lazy" />
          <template v-else>
            <el-icon><component :is="categoryIcon(item)" /></el-icon>
            <span>{{ item.category?.name }}</span>
          </template>
          <span class="status-pill org-activity__status" :class="activityStatusMeta(item.status).className">
            {{ item.status_text }}
          </span>
        </div>

        <div class="org-activity__main">
          <div class="org-activity__title">
            <button type="button" class="title-link" @click="goDetail(item)">{{ item.title }}</button>
            <span class="soft-chip">{{ item.category?.name }}</span>
          </div>
          <div class="org-activity__meta">
            <span><el-icon><Clock /></el-icon>{{ formatTimeRange(item.start_time, item.end_time) }}</span>
            <span><el-icon><Location /></el-icon>{{ item.location }}</span>
            <span><el-icon><Tickets /></el-icon>{{ item.signup_count }}/{{ item.capacity }} 人报名</span>
          </div>
          <p v-if="statusHint(item)" class="org-activity__hint">{{ statusHint(item) }}</p>
          <div class="org-activity__capacity">
            <div class="capacity-track">
              <span :style="{ width: `${percentOf(item)}%` }"></span>
            </div>
            <small>
              剩余 {{ item.remaining }} 个名额
              <template v-if="item.waitlist_count">· 候补 {{ item.waitlist_count }} 人</template>
            </small>
          </div>
        </div>

        <div class="org-activity__actions">
          <el-button
            v-if="canEdit(item)"
            size="small"
            round
            :icon="EditPen"
            @click="goEdit(item)"
          >
            编辑
          </el-button>
          <el-button
            v-if="canSubmit(item)"
            type="primary"
            size="small"
            round
            :icon="Promotion"
            @click="handleCommand('submit', item)"
          >
            提交审核
          </el-button>
          <el-button size="small" round :icon="Tickets" @click="goDetail(item)">
            查看
          </el-button>
          <el-dropdown trigger="click" @command="(command: string) => handleCommand(command, item)">
            <el-button size="small" round :icon="MoreFilled" aria-label="更多操作" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="roster" :icon="Document">报名名单</el-dropdown-item>
                <el-dropdown-item command="checkin" :icon="View">签到管理</el-dropdown-item>
                <el-dropdown-item command="stats" :icon="DataLine">活动数据</el-dropdown-item>
                <el-dropdown-item
                  v-if="canCancel(item)"
                  command="cancel"
                  :icon="Close"
                  divided
                >
                  取消活动
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </article>

      <EmptyState
        v-if="!loading && !list.length"
        :title="appliedKeyword ? '没有匹配的活动' : '这里还没有活动'"
        :description="
          appliedKeyword
            ? '试试其他关键词，或切换到全部状态。'
            : '创建第一个活动草稿，完善信息后提交审核。'
        "
      >
        <el-button v-if="appliedKeyword" round @click="resetFilters">重置筛选</el-button>
        <el-button v-else type="primary" round :icon="Plus" @click="router.push('/console/activities/new')">
          发布新活动
        </el-button>
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

    <el-dialog
      v-model="cancelVisible"
      title="取消活动"
      width="min(480px, 92vw)"
      :close-on-click-modal="false"
    >
      <template v-if="cancelTarget">
        <div class="cancel-dialog__summary">
          <span>{{ cancelTarget.title }}</span>
          <p>取消后，已成功报名的同学将收到活动取消通知，且活动不可恢复。</p>
        </div>
        <el-form label-position="top">
          <el-form-item
            :label="cancelNeedsReason ? '取消原因（必填）' : '取消原因（选填）'"
          >
            <el-input
              v-model="cancelReason"
              type="textarea"
              :rows="4"
              maxlength="255"
              show-word-limit
              placeholder="例如：场地临时调整，活动改期举行"
            />
          </el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="cancelVisible = false">返回</el-button>
        <el-button type="danger" :loading="cancelLoading" @click="confirmCancel">
          确认取消活动
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.organizer-activities {
  display: flex;
  flex-direction: column;
  gap: 22px;
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

.toolbar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 18px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.scope-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 4px;
  border-radius: 12px;
  background: var(--ch-bg);
  align-self: flex-start;
}

.scope-tab {
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

.scope-tab:hover {
  color: var(--ch-ink);
}

.scope-tab.is-active {
  background: #fff;
  color: var(--ch-primary);
  box-shadow: 0 3px 10px rgba(20, 34, 79, 0.1);
}

.toolbar__search {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 520px;
}

.activity-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 180px;
}

.org-activity {
  display: flex;
  align-items: stretch;
  gap: 20px;
  padding: 16px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.org-activity:hover {
  border-color: var(--ch-border-strong);
  box-shadow: var(--ch-shadow);
}

.org-activity__thumb {
  position: relative;
  display: grid;
  place-items: center;
  flex: 0 0 148px;
  min-height: 118px;
  border-radius: 14px;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.92);
}

.org-activity__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.org-activity__thumb > .el-icon {
  font-size: 34px;
  opacity: 0.92;
}

.org-activity__thumb > span:not(.status-pill) {
  position: absolute;
  bottom: 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  opacity: 0.8;
}

.org-activity__status {
  position: absolute;
  top: 9px;
  left: 9px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
}

.org-activity__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.org-activity__title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.title-link {
  max-width: 100%;
  padding: 0;
  border: none;
  background: none;
  color: var(--ch-ink);
  font-family: inherit;
  font-size: 16px;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.title-link:hover {
  color: var(--ch-primary);
}

.org-activity__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 9px;
  color: var(--ch-muted);
  font-size: 12px;
}

.org-activity__meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.org-activity__meta .el-icon {
  color: var(--ch-muted-light);
}

.org-activity__hint {
  margin-top: 8px;
  color: var(--ch-muted-light);
  font-size: 12px;
}

.org-activity__capacity {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.capacity-track {
  width: 150px;
  height: 5px;
  border-radius: 999px;
  background: #edf0f7;
  overflow: hidden;
}

.capacity-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6b83f0, #3757e8);
}

.org-activity__capacity small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.org-activity__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  align-content: center;
  gap: 8px;
  flex: 0 0 auto;
  max-width: 250px;
}

.cancel-dialog__summary {
  padding: 14px 16px;
  margin-bottom: 18px;
  border-radius: 12px;
  background: #fff6f6;
  border: 1px solid #f8dada;
}

.cancel-dialog__summary span {
  font-weight: 700;
  font-size: 14px;
}

.cancel-dialog__summary p {
  margin-top: 5px;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 900px) {
  .org-activity {
    flex-wrap: wrap;
  }

  .org-activity__thumb {
    flex: 0 0 120px;
    min-height: 100px;
  }

  .org-activity__actions {
    flex: 1 0 100%;
    justify-content: flex-start;
    max-width: none;
    padding-top: 4px;
  }
}

@media (max-width: 640px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .org-activity__thumb {
    flex: 1 0 100%;
    min-height: 140px;
  }

  .toolbar__search {
    flex-wrap: wrap;
  }
}
</style>
