<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera, CircleCheck, Iphone, Refresh, Tickets } from '@element-plus/icons-vue'
import QrScanner from 'qr-scanner'

import { getActivity } from '@/api/activities'
import { submitCheckin } from '@/api/signups'
import { ApiError } from '@/api/http'
import { useNotificationsStore } from '@/stores/notifications'
import type { ActivityDetail, CheckinResult } from '@/types'
import { parseCheckinPayload } from '@/utils/checkin'
import { formatDateTime, formatTimeRange } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const notifications = useNotificationsStore()

const videoRef = ref<HTMLVideoElement | null>(null)
const scanning = ref(false)
const starting = ref(false)
const cameraError = ref('')
const processing = ref(false)
const result = ref<CheckinResult | null>(null)
const errorMessage = ref('')
const lastScanned = ref('')
const contextActivity = ref<ActivityDetail | null>(null)
let scanner: QrScanner | null = null
let lastScanAt = 0

const manualForm = reactive({
  activityId: null as number | null,
  code: '',
})

const activityQueryId = computed(() => {
  const raw = route.query.activity
  const value = Number(typeof raw === 'string' ? raw : '')
  return Number.isInteger(value) && value > 0 ? value : null
})

const contextWindowText = computed(() => {
  const item = contextActivity.value
  if (!item) return ''
  return `${formatDateTime(item.checkin_window_start)} 至 ${formatDateTime(item.checkin_window_end)}`
})

async function loadContext(activityId: number | null) {
  contextActivity.value = null
  if (!activityId) return
  try {
    contextActivity.value = await getActivity(activityId)
  } catch {
    // 上下文加载失败不影响签到本身
  }
}

async function submit(activityId: number, rawCode: string) {
  const code = rawCode.trim().toUpperCase()
  if (!activityId) {
    errorMessage.value = '无法识别活动 ID，请扫描主办方展示的完整签到码，或手动输入活动 ID。'
    return
  }
  if (!/^[0-9A-Z]{8}$/.test(code)) {
    errorMessage.value = '签到码应为 8 位字母或数字，请核对后重试。'
    return
  }
  if (processing.value) return

  processing.value = true
  errorMessage.value = ''
  try {
    result.value = await submitCheckin(activityId, code, {
      device_info: navigator.userAgent.slice(0, 240),
    })
    ElMessage.success('签到成功')
    stopScanner()
    void notifications.refreshUnread()
    await loadContext(activityId)
  } catch (error) {
    if (error instanceof ApiError) errorMessage.value = error.message
    else errorMessage.value = '签到失败，请稍后重试。'
  } finally {
    processing.value = false
  }
}

function handleScan(content: string) {
  const now = Date.now()
  if (now - lastScanAt < 1500) return
  lastScanAt = now
  lastScanned.value = content
  const payload = parseCheckinPayload(content)
  if (!payload) {
    ElMessage.warning('未识别到有效的 CampusHub 签到码')
    return
  }
  const activityId = payload.activityId || activityQueryId.value || manualForm.activityId
  if (!activityId) {
    errorMessage.value = '签到码中缺少活动信息，请让主办方刷新二维码后重试。'
    return
  }
  manualForm.activityId = activityId
  if (payload.activityId) manualForm.code = payload.code
  void submit(activityId, payload.code)
}

async function startScanner() {
  if (scanning.value) return
  if (!videoRef.value) return
  starting.value = true
  cameraError.value = ''
  try {
    const hasCamera = await QrScanner.hasCamera()
    if (!hasCamera) {
      cameraError.value = '未检测到可用摄像头，请使用手动输入签到码。'
      return
    }
    await nextTick()
    scanner = new QrScanner(
      videoRef.value,
      (scan) => handleScan(scan.data),
      {
        preferredCamera: 'environment',
        maxScansPerSecond: 5,
        highlightScanRegion: true,
        highlightCodeOutline: true,
        returnDetailedScanResult: true,
      },
    )
    await scanner.start()
    scanning.value = true
  } catch (error) {
    cameraError.value =
      error instanceof Error && /permission/i.test(error.message)
        ? '摄像头权限被拒绝，请在浏览器设置中允许访问摄像头。'
        : '摄像头启动失败，请确认设备可用，或改用手动输入。'
    stopScanner()
  } finally {
    starting.value = false
  }
}

function stopScanner() {
  if (scanner) {
    scanner.stop()
    scanner.destroy()
    scanner = null
  }
  scanning.value = false
}

function submitManual() {
  if (!manualForm.activityId) {
    errorMessage.value = '请输入活动 ID。'
    return
  }
  void submit(manualForm.activityId, manualForm.code)
}

function resetResult() {
  result.value = null
  errorMessage.value = ''
  manualForm.code = ''
  if (videoRef.value) void startScanner()
}

function viewActivity() {
  if (result.value) router.push(`/activities/${result.value.activity_id}`)
}

watch(
  () => route.query.activity,
  (value) => {
    const id = Number(typeof value === 'string' ? value : '')
    manualForm.activityId = Number.isInteger(id) && id > 0 ? id : null
    void loadContext(manualForm.activityId)
  },
  { immediate: true },
)

onMounted(() => {
  if (activityQueryId.value) manualForm.activityId = activityQueryId.value
})

onBeforeUnmount(stopScanner)
</script>

<template>
  <div class="checkin-page">
    <section class="page-hero checkin-hero">
      <div class="page-container">
        <span class="eyebrow">Check-in station</span>
        <h1>扫码签到</h1>
        <p>扫描主办方展示的二维码，或手动输入 8 位签到码，快速完成现场签到。</p>
      </div>
    </section>

    <section class="page-container page-block">
      <div v-if="contextActivity" class="context-banner surface">
        <div class="context-badge">
          <span :style="{ background: contextActivity.category?.color || '#3757e8' }">
            {{ contextActivity.category?.name }}
          </span>
          <strong>{{ contextActivity.title }}</strong>
        </div>
        <div class="context-meta">
          <span>{{ formatTimeRange(contextActivity.start_time, contextActivity.end_time) }}</span>
          <span>签到时段：{{ contextWindowText }}</span>
          <span
            class="status-pill"
            :class="contextActivity.checkin_open ? 'is-published' : 'is-ended'"
          >
            {{ contextActivity.checkin_open ? '签到通道开放中' : '当前不在签到时段' }}
          </span>
        </div>
      </div>

      <div class="checkin-grid">
        <div class="scanner-card surface">
          <div class="card-head">
            <div>
              <h2>扫描二维码</h2>
              <p>将主办方展示的签到二维码放入取景框内</p>
            </div>
            <span class="scan-state" :class="{ 'is-live': scanning }">
              <span class="scan-state__dot"></span>
              {{ scanning ? '识别中' : '摄像头未开启' }}
            </span>
          </div>

          <div class="video-shell">
            <video ref="videoRef" class="scanner-video" playsinline muted></video>

            <div v-if="!scanning" class="video-placeholder">
              <span class="placeholder-icon"><el-icon><Camera /></el-icon></span>
              <strong>{{ cameraError ? '摄像头暂不可用' : '准备扫码签到' }}</strong>
              <p>{{ cameraError || '点击下方按钮开启摄像头，扫描现场二维码即可签到。' }}</p>
              <el-button
                type="primary"
                round
                :loading="starting"
                class="ch-button-gradient"
                @click="startScanner"
              >
                {{ cameraError ? '重新尝试' : '开启摄像头' }}
              </el-button>
            </div>

            <div v-else class="scan-overlay">
              <span class="scan-corner scan-corner--tl"></span>
              <span class="scan-corner scan-corner--tr"></span>
              <span class="scan-corner scan-corner--bl"></span>
              <span class="scan-corner scan-corner--br"></span>
              <span class="scan-line"></span>
            </div>

            <div v-if="processing" class="processing-overlay">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在验证签到码…</span>
            </div>
          </div>

          <div class="scanner-footer">
            <span class="scanner-hint">
              <el-icon><InfoFilled /></el-icon>
              动态签到码每 30 秒刷新，请在有效期内完成扫描
            </span>
            <el-button v-if="scanning" plain round size="small" @click="stopScanner">
              关闭摄像头
            </el-button>
          </div>
        </div>

        <div class="checkin-side">
          <div v-if="result" class="success-card">
            <span class="success-icon"><el-icon><CircleCheck /></el-icon></span>
            <span class="success-eyebrow">CHECK-IN COMPLETE</span>
            <h2>签到成功</h2>
            <p>欢迎来到活动现场，祝你有一段愉快的体验。</p>

            <div class="success-details">
              <div>
                <span>姓名</span>
                <strong>{{ result.real_name }}</strong>
              </div>
              <div>
                <span>学号</span>
                <strong>{{ result.student_no }}</strong>
              </div>
              <div>
                <span>签到时间</span>
                <strong>{{ formatDateTime(result.checked_in_at) }}</strong>
              </div>
              <div>
                <span>签到方式</span>
                <strong>{{ result.checkin_method_text }}</strong>
              </div>
              <div>
                <span>当前已签到</span>
                <strong>{{ result.checked_in_count }} 人</strong>
              </div>
            </div>

            <div class="success-actions">
              <el-button type="primary" round @click="viewActivity">查看活动</el-button>
              <el-button plain round :icon="Refresh" @click="resetResult">继续签到</el-button>
            </div>
          </div>

          <div v-else class="manual-card surface">
            <div class="card-head">
              <div>
                <h2>手动输入</h2>
                <p>摄像头不可用时，可输入活动 ID 与签到码</p>
              </div>
            </div>

            <el-form label-position="top" size="large" @submit.prevent="submitManual">
              <el-form-item label="活动 ID">
                <el-input-number
                  v-model="manualForm.activityId"
                  :min="1"
                  :controls="false"
                  placeholder="请输入数字活动 ID"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item label="签到码">
                <el-input
                  v-model="manualForm.code"
                  maxlength="8"
                  placeholder="请输入 8 位签到码"
                  class="code-input"
                  @keyup.enter="submitManual"
                />
              </el-form-item>
              <el-button
                type="primary"
                size="large"
                class="manual-submit ch-button-gradient"
                :loading="processing"
                @click="submitManual"
              >
                提交签到
              </el-button>
            </el-form>

            <div class="manual-tip">
              <el-icon><Iphone /></el-icon>
              签到码区分字母与数字，请输入主办方屏幕或纸质凭证上的完整 8 位字符。
            </div>
          </div>

          <div v-if="errorMessage" class="error-card">
            <span class="error-icon"><el-icon><WarningFilled /></el-icon></span>
            <div>
              <strong>签到未完成</strong>
              <p>{{ errorMessage }}</p>
              <RouterLink to="/my/signups">查看我的报名</RouterLink>
            </div>
          </div>

          <div class="help-card surface">
            <h3>签到遇到问题？</h3>
            <ul>
              <li><span>01</span>确认已成功报名该活动，候补状态无法签到。</li>
              <li><span>02</span>确认当前处于签到时段（活动开始前 30 分钟至结束）。</li>
              <li><span>03</span>动态码过期时，请让主办方刷新二维码后再扫描。</li>
              <li><span>04</span>仍无法签到，请联系现场工作人员手动补签。</li>
            </ul>
            <RouterLink to="/my/signups" class="help-link">
              <el-icon><Tickets /></el-icon>
              查看我的报名与签到状态
            </RouterLink>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.checkin-hero {
  padding-bottom: 44px;
}

.context-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  margin-bottom: 22px;
  padding: 20px 24px;
}

.context-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.context-badge span {
  flex: 0 0 auto;
  padding: 4px 10px;
  border-radius: 6px;
  color: #fff;
  font-size: 10.5px;
  font-weight: 600;
}

.context-badge strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 16px;
}

.context-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 8px 18px;
  color: var(--ch-muted);
  font-size: 11.5px;
}

.checkin-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.85fr);
  gap: 22px;
  align-items: start;
}

.scanner-card {
  padding: 26px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.card-head h2 {
  font-size: 20px;
  letter-spacing: -0.02em;
}

.card-head p {
  margin-top: 3px;
  color: var(--ch-muted);
  font-size: 12px;
}

.scan-state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
  padding: 5px 10px;
  border-radius: 999px;
  background: #f4f6fb;
  color: var(--ch-muted);
  font-size: 10.5px;
  font-weight: 600;
}

.scan-state__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ch-muted-light);
}

.scan-state.is-live {
  background: #effaf6;
  color: #0b8a5f;
}

.scan-state.is-live .scan-state__dot {
  background: #0f9f6e;
  box-shadow: 0 0 0 3px rgba(15, 159, 110, 0.15);
}

.video-shell {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  border-radius: 16px;
  background:
    radial-gradient(400px 280px at 50% 20%, rgba(74, 104, 242, 0.14), transparent 65%),
    #0b1226;
}

.scanner-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 30px;
  color: #fff;
  text-align: center;
}

.placeholder-icon {
  display: grid;
  place-items: center;
  width: 62px;
  height: 62px;
  margin-bottom: 4px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.06);
  color: #a9baff;
  font-size: 28px;
  backdrop-filter: blur(8px);
}

.video-placeholder strong {
  font-size: 15px;
}

.video-placeholder p {
  max-width: 330px;
  color: rgba(255, 255, 255, 0.44);
  font-size: 11.5px;
  line-height: 1.65;
}

.video-placeholder .el-button {
  margin-top: 8px;
}

.scan-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.scan-overlay::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 58%;
  aspect-ratio: 1;
  max-width: 280px;
  border-radius: 16px;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 0 999px rgba(4, 8, 20, 0.42);
}

.scan-corner {
  position: absolute;
  z-index: 2;
  width: 32px;
  height: 32px;
  border: 3px solid #8ea5ff;
}

.scan-corner--tl {
  left: 21%;
  top: 21%;
  border-right: none;
  border-bottom: none;
  border-radius: 10px 0 0 0;
}

.scan-corner--tr {
  right: 21%;
  top: 21%;
  border-left: none;
  border-bottom: none;
  border-radius: 0 10px 0 0;
}

.scan-corner--bl {
  left: 21%;
  bottom: 21%;
  border-right: none;
  border-top: none;
  border-radius: 0 0 0 10px;
}

.scan-corner--br {
  right: 21%;
  bottom: 21%;
  border-left: none;
  border-top: none;
  border-radius: 0 0 10px 0;
}

.scan-line {
  position: absolute;
  left: 23%;
  right: 23%;
  top: 22%;
  z-index: 2;
  height: 2px;
  background: linear-gradient(90deg, transparent, #9fb2ff, transparent);
  box-shadow: 0 0 16px rgba(142, 165, 255, 0.8);
  animation: scan-sweep 2.6s ease-in-out infinite;
}

@keyframes scan-sweep {
  0%,
  100% {
    top: 23%;
    opacity: 0.4;
  }
  50% {
    top: 75%;
    opacity: 1;
  }
}

.processing-overlay {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(7, 12, 26, 0.72);
  color: #fff;
  font-size: 12px;
  backdrop-filter: blur(3px);
}

.processing-overlay .el-icon {
  font-size: 28px;
  color: #a9baff;
}

.scanner-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
}

.scanner-hint {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ch-muted-light);
  font-size: 11px;
}

.checkin-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.manual-card {
  padding: 26px;
}

.manual-card :deep(.el-form-item) {
  margin-bottom: 16px;
}

.code-input :deep(.el-input__inner) {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  font-variant-numeric: tabular-nums;
}

.manual-submit {
  width: 100%;
  height: 46px;
  margin-top: 4px;
  border-radius: 11px;
}

.manual-tip {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin-top: 16px;
  padding: 11px 12px;
  border-radius: 9px;
  background: #f7f9fe;
  color: var(--ch-muted);
  font-size: 11px;
  line-height: 1.65;
}

.manual-tip .el-icon {
  flex: 0 0 auto;
  margin-top: 2px;
  color: var(--ch-primary);
}

.success-card {
  position: relative;
  overflow: hidden;
  padding: 30px;
  border-radius: var(--ch-radius);
  background:
    radial-gradient(320px 240px at 100% 0%, rgba(74, 230, 180, 0.2), transparent 60%),
    linear-gradient(150deg, #0d3d31, #0b2c25 60%, #071f1a);
  color: rgba(255, 255, 255, 0.7);
  box-shadow: 0 20px 50px rgba(7, 50, 38, 0.24);
}

.success-icon {
  display: grid;
  place-items: center;
  width: 54px;
  height: 54px;
  margin-bottom: 18px;
  border-radius: 16px;
  background: rgba(72, 226, 178, 0.14);
  color: #4ee2b2;
  font-size: 28px;
}

.success-eyebrow {
  color: #4ee2b2;
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.22em;
}

.success-card h2 {
  margin-top: 6px;
  color: #fff;
  font-size: 27px;
  letter-spacing: -0.02em;
}

.success-card > p {
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

.success-details {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.success-details div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.success-details span {
  color: rgba(255, 255, 255, 0.4);
  font-size: 10px;
}

.success-details strong {
  color: #fff;
  font-size: 12.5px;
  font-weight: 600;
}

.success-actions {
  display: flex;
  gap: 10px;
  margin-top: 26px;
}

.success-actions .el-button--primary {
  background: #4ee2b2;
  border-color: #4ee2b2;
  color: #073b2d;
}

.success-actions .el-button--primary:hover {
  background: #6deac1;
  border-color: #6deac1;
}

.success-actions .el-button.is-plain {
  border-color: rgba(255, 255, 255, 0.22);
  background: transparent;
  color: rgba(255, 255, 255, 0.76);
}

.success-actions .el-button.is-plain:hover {
  border-color: rgba(255, 255, 255, 0.4);
  color: #fff;
}

.error-card {
  display: flex;
  gap: 12px;
  padding: 18px;
  border: 1px solid rgba(224, 72, 75, 0.2);
  border-radius: var(--ch-radius-sm);
  background: #fdf3f3;
}

.error-icon {
  flex: 0 0 auto;
  color: var(--ch-danger);
  font-size: 20px;
}

.error-card strong {
  color: #a83034;
  font-size: 13px;
}

.error-card p {
  margin-top: 3px;
  color: #b85054;
  font-size: 11.5px;
  line-height: 1.65;
}

.error-card a {
  display: inline-block;
  margin-top: 6px;
  color: #a83034;
  font-size: 11px;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.help-card {
  padding: 22px;
}

.help-card h3 {
  font-size: 14px;
}

.help-card ul {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin-top: 14px;
}

.help-card li {
  display: flex;
  gap: 9px;
  color: var(--ch-muted);
  font-size: 11.5px;
  line-height: 1.6;
}

.help-card li span {
  flex: 0 0 auto;
  color: var(--ch-primary);
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.help-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #f0f3fa;
  color: var(--ch-primary);
  font-size: 11.5px;
  font-weight: 600;
}

@media (max-width: 980px) {
  .checkin-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .context-banner {
    flex-direction: column;
    align-items: flex-start;
  }

  .context-meta {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .scanner-card,
  .manual-card,
  .success-card {
    padding: 20px;
  }

  .scanner-footer {
    flex-direction: column;
    align-items: flex-start;
  }

  .success-details {
    grid-template-columns: minmax(0, 1fr);
  }

  .success-actions {
    flex-direction: column;
  }
}
</style>
