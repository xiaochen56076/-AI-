<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import QRCode from 'qrcode'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Camera,
  CircleCheck,
  Clock,
  Document,
  Location,
  Refresh,
  Search,
  User,
} from '@element-plus/icons-vue'

import { getActivity } from '@/api/activities'
import { getCheckinCode, manualCheckin } from '@/api/signups'
import EmptyState from '@/components/EmptyState.vue'
import StatCard from '@/components/StatCard.vue'
import type { ActivityDetail, CheckinCode, CheckinResult } from '@/types'
import {
  activityStatusMeta,
  checkinModeLabel,
  formatDateTime,
  formatTimeRange,
} from '@/utils/format'

const route = useRoute()
const router = useRouter()
const activityId = Number(route.params.id)

const loading = ref(true)
const codeLoading = ref(false)
const codeError = ref(false)
const activity = ref<ActivityDetail | null>(null)
const checkinCode = ref<CheckinCode | null>(null)
const qrImage = ref('')
const now = ref(Date.now())

const manual = reactive({ student_no: '', reason: '' })
const manualLoading = ref(false)
const manualRecord = ref<CheckinResult | null>(null)

let refreshTimer: number | null = null
let tickTimer: number | null = null

const canGenerate = computed(
  () => activity.value?.status === 2 && activity.value?.checkin_mode !== 0,
)
const isDynamic = computed(() => checkinCode.value?.checkin_mode === 2)
const checkedInCount = computed(
  () => checkinCode.value?.checked_in_count ?? activity.value?.checked_in_count ?? 0,
)
const signupCount = computed(
  () => checkinCode.value?.signup_count ?? activity.value?.signup_count ?? 0,
)
const pendingCount = computed(() => Math.max(signupCount.value - checkedInCount.value, 0))
const checkinProgress = computed(() => {
  if (!signupCount.value) return '0%'
  return `${Math.min(100, Math.round((checkedInCount.value / signupCount.value) * 100))}%`
})
const codeCountdown = computed(() => {
  if (!checkinCode.value?.expires_at) return ''
  const diff = dayjs(checkinCode.value.expires_at).valueOf() - now.value
  if (diff <= 0) return '正在刷新'
  return `${Math.ceil(diff / 1000)} 秒`
})
const windowOpen = computed(() => {
  const data = checkinCode.value
  if (!data) return activity.value?.checkin_open ?? false
  const at = now.value
  return (
    dayjs(at).valueOf() >= dayjs(data.checkin_window_start).valueOf() &&
    dayjs(at).valueOf() <= dayjs(data.checkin_window_end).valueOf()
  )
})

function formatWindow(start?: string, end?: string) {
  if (!start || !end) return '—'
  return `${formatDateTime(start)} 至 ${formatDateTime(end)}`
}

async function loadActivity() {
  try {
    activity.value = await getActivity(activityId)
  } catch {
    activity.value = null
  }
}

async function loadCode(silent = false) {
  if (!canGenerate.value) return
  if (!silent) codeLoading.value = true
  try {
    const data = await getCheckinCode(activityId)
    checkinCode.value = data
    codeError.value = false
    qrImage.value = await QRCode.toDataURL(data.qr_content, {
      width: 420,
      margin: 1,
      color: { dark: '#101a33', light: '#ffffff' },
    })
    if (activity.value) {
      activity.value.checked_in_count = data.checked_in_count
    }
  } catch {
    if (!checkinCode.value) codeError.value = true
  } finally {
    if (!silent) codeLoading.value = false
  }
}

function startTimers() {
  stopTimers()
  tickTimer = window.setInterval(() => {
    now.value = Date.now()
  }, 1000)
  refreshTimer = window.setInterval(() => {
    loadCode(true)
  }, 15000)
}

function stopTimers() {
  if (refreshTimer) window.clearInterval(refreshTimer)
  if (tickTimer) window.clearInterval(tickTimer)
  refreshTimer = null
  tickTimer = null
}

async function submitManual() {
  if (!manual.student_no.trim()) {
    ElMessage.warning('请输入学生学号')
    return
  }
  if (manual.reason.trim().length < 2) {
    ElMessage.warning('补签原因至少需要 2 个字')
    return
  }
  manualLoading.value = true
  try {
    const record = await manualCheckin(activityId, manual.student_no.trim(), manual.reason.trim())
    manualRecord.value = record
    manual.student_no = ''
    manual.reason = ''
    ElMessage.success(`已为 ${record.real_name} 完成补签`)
    if (activity.value) activity.value.checked_in_count = record.checked_in_count
    await loadCode(true)
  } catch {
    // 接口错误由拦截器提示
  } finally {
    manualLoading.value = false
  }
}

onMounted(async () => {
  loading.value = true
  await loadActivity()
  loading.value = false
  now.value = Date.now()
  if (canGenerate.value) {
    await loadCode()
    startTimers()
  }
})

onBeforeUnmount(stopTimers)
</script>

<template>
  <div class="checkin-page" v-loading="loading">
    <div class="page-head">
      <div>
        <button type="button" class="back-link" @click="router.push('/console/activities')">
          <el-icon><ArrowLeft /></el-icon>
          返回我的活动
        </button>
        <div class="page-head__title">
          <h1>{{ activity?.title || '签到管理' }}</h1>
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
          <span><el-icon><Camera /></el-icon>{{ checkinModeLabel(activity.checkin_mode) }}</span>
        </p>
      </div>
      <div class="page-head__actions">
        <el-button round :icon="Document" @click="router.push(`/console/activities/${activityId}/roster`)">
          报名名单
        </el-button>
        <el-button round @click="router.push(`/activities/${activityId}`)">活动详情</el-button>
      </div>
    </div>

    <div v-if="activity?.checkin_mode === 0" class="empty-card">
      <EmptyState
        title="该活动设置为无需签到"
        description="当前活动只统计报名，不记录到场情况。如需启用签到，请在活动仍为草稿或刚发布时调整签到方式。"
      >
        <el-button round @click="router.push('/console/activities')">返回活动列表</el-button>
      </EmptyState>
    </div>

    <div v-else-if="activity && !canGenerate" class="empty-card">
      <EmptyState
        title="暂不可生成签到码"
        description="只有已发布的活动才能生成签到码。活动结束后签到入口会自动关闭，请确认活动状态。"
      >
        <el-button round @click="router.push('/console/activities')">返回活动列表</el-button>
      </EmptyState>
    </div>

    <template v-else>
      <div class="stat-grid">
        <StatCard
          label="报名成功"
          :value="signupCount"
          icon="Tickets"
          tone="primary"
          hint="具备签到资格的人数"
        />
        <StatCard
          label="已签到"
          :value="checkedInCount"
          icon="CircleCheck"
          tone="success"
          :hint="`签到率 ${signupCount ? Math.round((checkedInCount / signupCount) * 100) : 0}%`"
        />
        <StatCard
          label="待签到"
          :value="pendingCount"
          icon="Clock"
          tone="warning"
          hint="可扫码或手动补签"
        />
        <div class="progress-card">
          <div class="progress-card__head">
            <span>现场进度</span>
            <strong>{{ checkinProgress }}</strong>
          </div>
          <div class="progress-track">
            <span :style="{ width: checkinProgress }"></span>
          </div>
          <p>
            <i class="live-dot" :class="{ 'is-open': windowOpen }"></i>
            {{ windowOpen ? '签到窗口开放中' : '当前不在签到时间内' }}
          </p>
        </div>
      </div>

      <div class="checkin-layout">
        <section class="code-card">
          <div class="code-card__head">
            <div>
              <span class="code-card__eyebrow">
                <i class="live-dot" :class="{ 'is-open': windowOpen }"></i>
                {{ checkinCode?.checkin_mode_text || '签到码' }}
              </span>
              <h2>现场签到二维码</h2>
              <p>同学使用 CampusHub 扫码签到，也可在「扫码签到」页面手动输入下方代码。</p>
            </div>
            <el-button
              :icon="Refresh"
              circle
              :loading="codeLoading"
              title="立即刷新签到码"
              @click="loadCode()"
            />
          </div>

          <div class="code-body" v-loading="codeLoading">
            <div v-if="qrImage" class="qr-frame">
              <img :src="qrImage" alt="活动签到二维码" />
              <span class="qr-corner qr-corner--tl"></span>
              <span class="qr-corner qr-corner--tr"></span>
              <span class="qr-corner qr-corner--bl"></span>
              <span class="qr-corner qr-corner--br"></span>
            </div>
            <div v-else-if="codeError" class="qr-placeholder">
              <el-icon><Refresh /></el-icon>
              <p>签到码加载失败</p>
              <el-button size="small" round @click="loadCode()">重新加载</el-button>
            </div>
            <div v-else class="qr-placeholder">
              <el-icon><Camera /></el-icon>
              <p>正在生成签到码</p>
            </div>

            <div v-if="checkinCode" class="code-side">
              <span class="code-label">签到代码</span>
              <div class="code-value">{{ checkinCode.code }}</div>
              <div class="code-expire">
                <template v-if="isDynamic">
                  <el-icon><Clock /></el-icon>
                  剩余 <strong>{{ codeCountdown }}</strong>，过期后自动刷新
                </template>
                <template v-else>
                  <el-icon><CircleCheck /></el-icon>
                  静态码长期有效，活动结束后失效
                </template>
              </div>

              <div class="code-window">
                <span>签到开放时间</span>
                <strong>{{ formatWindow(checkinCode.checkin_window_start, checkinCode.checkin_window_end) }}</strong>
                <small>活动开始前 30 分钟开放，活动结束时关闭</small>
              </div>
            </div>
          </div>
        </section>

        <section class="manual-card">
          <div class="manual-card__head">
            <div class="manual-card__icon">
              <el-icon><Search /></el-icon>
            </div>
            <div>
              <h2>手动补签</h2>
              <p>为已成功报名但无法扫码的同学补录签到，操作会记录补签原因。</p>
            </div>
          </div>

          <div v-if="manualRecord" class="manual-success">
            <el-icon><CircleCheck /></el-icon>
            <div>
              <strong>{{ manualRecord.real_name }} 补签成功</strong>
              <span>{{ manualRecord.student_no }} · {{ formatDateTime(manualRecord.checked_in_at) }}</span>
            </div>
            <button type="button" @click="manualRecord = null">关闭</button>
          </div>

          <el-form label-position="top" class="manual-form" @submit.prevent="submitManual">
            <el-form-item label="学生学号">
              <el-input
                v-model="manual.student_no"
                placeholder="请输入学生学号"
                :prefix-icon="User"
                clearable
              />
            </el-form-item>
            <el-form-item label="补签原因">
              <el-input
                v-model="manual.reason"
                type="textarea"
                :rows="3"
                maxlength="255"
                show-word-limit
                placeholder="例如：现场网络故障，无法扫码"
              />
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              round
              class="manual-submit"
              :loading="manualLoading"
              @click="submitManual"
            >
              确认补签
            </el-button>
          </el-form>

          <div class="manual-tips">
            <span>补签须知</span>
            <ul>
              <li>仅支持已成功报名且尚未签到的学生。</li>
              <li>补签时间必须处于活动签到窗口内。</li>
              <li>补签记录会标记为「手动补签」并保留操作原因。</li>
            </ul>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.checkin-page {
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

.empty-card {
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  padding: 12px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr)) 1.2fr;
  gap: 16px;
}

.progress-card {
  padding: 22px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.progress-card__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  color: var(--ch-muted);
  font-size: 13px;
}

.progress-card__head strong {
  color: var(--ch-ink);
  font-size: 24px;
  letter-spacing: -0.02em;
}

.progress-track {
  height: 8px;
  margin: 16px 0 10px;
  border-radius: 999px;
  background: #edf0f7;
  overflow: hidden;
}

.progress-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #34c38f, #0f9f6e);
  transition: width 0.4s ease;
}

.progress-card p {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--ch-muted-light);
  font-size: 12px;
}

.live-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #b9c2d8;
}

.live-dot.is-open {
  background: var(--ch-success);
  box-shadow: 0 0 0 4px rgba(15, 159, 110, 0.16);
  animation: pulse 2s ease-in-out infinite;
}

.checkin-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(300px, 1fr);
  gap: 20px;
  align-items: start;
}

.code-card,
.manual-card {
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  overflow: hidden;
}

.code-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 24px 26px 18px;
}

.code-card__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--ch-primary);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.code-card__head h2 {
  margin-top: 8px;
  font-size: 20px;
  letter-spacing: -0.01em;
}

.code-card__head p {
  margin-top: 5px;
  max-width: 480px;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.6;
}

.code-body {
  display: flex;
  gap: 26px;
  align-items: center;
  padding: 26px;
  background:
    radial-gradient(420px 220px at 10% 100%, rgba(55, 87, 232, 0.07), transparent 65%),
    #fbfcff;
  border-top: 1px solid var(--ch-border);
}

.qr-frame {
  position: relative;
  flex: 0 0 auto;
  padding: 16px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 14px 40px rgba(20, 34, 79, 0.1);
}

.qr-frame img {
  width: 228px;
  height: 228px;
  border-radius: 6px;
}

.qr-corner {
  position: absolute;
  width: 18px;
  height: 18px;
  border: 3px solid var(--ch-primary);
}

.qr-corner--tl {
  top: 8px;
  left: 8px;
  border-right: none;
  border-bottom: none;
  border-radius: 6px 0 0 0;
}

.qr-corner--tr {
  top: 8px;
  right: 8px;
  border-left: none;
  border-bottom: none;
  border-radius: 0 6px 0 0;
}

.qr-corner--bl {
  bottom: 8px;
  left: 8px;
  border-right: none;
  border-top: none;
  border-radius: 0 0 0 6px;
}

.qr-corner--br {
  bottom: 8px;
  right: 8px;
  border-left: none;
  border-top: none;
  border-radius: 0 0 6px 0;
}

.qr-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 260px;
  height: 260px;
  border: 1px dashed var(--ch-border-strong);
  border-radius: 18px;
  background: #fff;
  color: var(--ch-muted-light);
  font-size: 12px;
}

.qr-placeholder .el-icon {
  font-size: 36px;
}

.code-side {
  flex: 1;
  min-width: 0;
}

.code-label {
  color: var(--ch-muted);
  font-size: 12px;
}

.code-value {
  margin: 6px 0 10px;
  color: var(--ch-ink);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: clamp(26px, 3.4vw, 38px);
  font-weight: 800;
  letter-spacing: 0.16em;
}

.code-expire {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ch-muted);
  font-size: 12px;
}

.code-expire strong {
  color: var(--ch-primary);
}

.code-window {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 20px;
  padding: 14px 16px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--ch-border);
}

.code-window span {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.code-window strong {
  font-size: 12px;
  font-weight: 600;
}

.code-window small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.manual-card {
  padding: 24px;
}

.manual-card__head {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.manual-card__icon {
  display: grid;
  place-items: center;
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  border-radius: 13px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  font-size: 19px;
}

.manual-card__head h2 {
  font-size: 18px;
}

.manual-card__head p {
  margin-top: 4px;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.6;
}

.manual-success {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 16px;
  padding: 13px 14px;
  border-radius: 12px;
  background: #e8f8f2;
  color: #0b8a5f;
}

.manual-success .el-icon {
  margin-top: 2px;
  font-size: 18px;
}

.manual-success div {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.manual-success strong {
  font-size: 13px;
}

.manual-success span {
  margin-top: 2px;
  color: #3d8a70;
  font-size: 11px;
}

.manual-success button {
  border: none;
  background: none;
  color: #3d8a70;
  font-size: 11px;
  cursor: pointer;
}

.manual-form {
  margin-top: 18px;
}

.manual-submit {
  width: 100%;
  margin-top: 4px;
}

.manual-tips {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px dashed var(--ch-border);
}

.manual-tips > span {
  color: var(--ch-muted-light);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
}

.manual-tips ul {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 8px;
}

.manual-tips li {
  position: relative;
  padding-left: 13px;
  color: var(--ch-muted);
  font-size: 11px;
  line-height: 1.6;
}

.manual-tips li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 7px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--ch-muted-light);
}

@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 0 4px rgba(15, 159, 110, 0.16);
  }
  50% {
    box-shadow: 0 0 0 7px rgba(15, 159, 110, 0.04);
  }
}

@media (max-width: 1080px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .checkin-layout {
    grid-template-columns: minmax(0, 1fr);
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

  .stat-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .code-body {
    flex-direction: column;
    align-items: stretch;
  }

  .qr-frame {
    align-self: center;
  }

  .qr-frame img {
    width: 200px;
    height: 200px;
  }

  .code-side {
    text-align: center;
  }

  .code-expire {
    justify-content: center;
  }
}
</style>
