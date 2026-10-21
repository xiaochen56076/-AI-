<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Back,
  Calendar,
  Camera,
  Clock,
  EditPen,
  Location,
  Share,
  Star,
  StarFilled,
  Tickets,
  TrendCharts,
  User,
  View,
} from '@element-plus/icons-vue'

import EmptyState from '@/components/EmptyState.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import {
  cancelActivity,
  favoriteActivity,
  getActivity,
  submitActivity,
  unfavoriteActivity,
} from '@/api/activities'
import { cancelSignup, signupForActivity } from '@/api/signups'
import { useAuthStore } from '@/stores/auth'
import type { ActivityDetail } from '@/types'
import {
  activityStatusMeta,
  categoryGradient,
  checkinModeLabel,
  countdownText,
  formatDateTime,
  formatTimeRange,
} from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activity = ref<ActivityDetail | null>(null)
const loading = ref(true)
const notFound = ref(false)
const coverError = ref(false)
const signupVisible = ref(false)
const remark = ref('')
const submitting = ref(false)
const now = ref(Date.now())
let clock: number | null = null

const activityId = computed(() => Number(route.params.id))
const status = computed(() => activityStatusMeta(activity.value?.status ?? 0))
const hasCover = computed(() => Boolean(activity.value?.cover_url) && !coverError.value)
const bannerStyle = computed(() => ({
  background: categoryGradient(activity.value?.category?.color),
}))

const signupStart = computed(() => (activity.value ? Date.parse(activity.value.signup_start) : 0))
const signupEnd = computed(() => (activity.value ? Date.parse(activity.value.signup_end) : 0))
const endTime = computed(() => (activity.value ? Date.parse(activity.value.end_time) : 0))

const signupWindowActive = computed(
  () =>
    Boolean(activity.value) &&
    activity.value?.status === 2 &&
    now.value >= signupStart.value &&
    now.value <= signupEnd.value,
)

const mySignup = computed(() => activity.value?.my_signup ?? null)
const hasActiveSignup = computed(() =>
  mySignup.value ? [0, 1, 3].includes(mySignup.value.status) : false,
)

const waitlistAvailable = computed(() => {
  const item = activity.value
  if (!item || item.status !== 2 || !signupWindowActive.value) return false
  if (item.remaining > 0) return false
  if (!item.waitlist_enabled) return false
  return item.waitlist_limit === 0 || item.waitlist_count < item.waitlist_limit
})

const canApply = computed(
  () =>
    Boolean(activity.value) &&
    activity.value?.status === 2 &&
    signupWindowActive.value &&
    !hasActiveSignup.value &&
    (activity.value.remaining > 0 || waitlistAvailable.value),
)

const canCancelSignup = computed(() => {
  const item = activity.value
  if (!item || !mySignup.value) return false
  return (
    [0, 1].includes(mySignup.value.status) &&
    item.status === 2 &&
    now.value <= signupEnd.value
  )
})

const canCheckin = computed(
  () =>
    Boolean(activity.value?.checkin_open) &&
    mySignup.value?.status === 1 &&
    !mySignup.value?.checked_in,
)

const progress = computed(() => {
  const item = activity.value
  if (!item?.capacity) return 0
  return Math.min(100, Math.round((item.signup_count / item.capacity) * 100))
})

const countdown = computed(() => {
  const item = activity.value
  if (!item) return { label: '', value: '' }
  if (now.value < signupStart.value) {
    return { label: '报名开启倒计时', value: countdownText(item.signup_start, now.value) }
  }
  if (now.value <= signupEnd.value && item.status === 2) {
    return { label: '报名截止倒计时', value: countdownText(item.signup_end, now.value) }
  }
  if (now.value < endTime.value) {
    return { label: '活动开始倒计时', value: countdownText(item.start_time, now.value) }
  }
  return { label: '活动状态', value: item.status === 3 ? '已结束' : '已开始' }
})

const signupButtonText = computed(() => {
  const item = activity.value
  if (!item) return '报名'
  if (hasActiveSignup.value) {
    return mySignup.value?.status === 3 ? '已签到' : '已报名'
  }
  if (item.status !== 2) return item.status_text
  if (now.value < signupStart.value) return '报名未开始'
  if (now.value > signupEnd.value) return '报名已截止'
  if (item.remaining > 0) return '立即报名'
  if (waitlistAvailable.value) return '加入候补'
  return '名额已满'
})

const signupButtonDisabled = computed(() => {
  const item = activity.value
  if (!item || hasActiveSignup.value) return true
  return !canApply.value
})

const showWaitlistHint = computed(
  () =>
    Boolean(activity.value) &&
    activity.value?.status === 2 &&
    activity.value.remaining <= 0 &&
    activity.value.waitlist_enabled &&
    now.value >= signupStart.value &&
    now.value <= signupEnd.value &&
    !hasActiveSignup.value,
)

const canManage = computed(() => Boolean(activity.value?.can_manage))
const canCancelActivity = computed(
  () => canManage.value && [0, 1, 2, 5].includes(activity.value?.status ?? -1),
)
const auditVisible = computed(
  () => Boolean(activity.value) && (activity.value?.audit_records.length ?? 0) > 0,
)

async function load() {
  loading.value = true
  notFound.value = false
  coverError.value = false
  try {
    activity.value = await getActivity(activityId.value)
    document.title = `${activity.value.title} · CampusHub`
  } catch {
    notFound.value = true
    activity.value = null
  } finally {
    loading.value = false
  }
}

function requireLogin() {
  router.push({ name: 'login', query: { redirect: route.fullPath } })
}

function openSignup() {
  if (!auth.isAuthenticated) {
    requireLogin()
    return
  }
  if (!canApply.value) return
  remark.value = ''
  signupVisible.value = true
}

async function confirmSignup() {
  if (!activity.value) return
  submitting.value = true
  try {
    const result = await signupForActivity(activity.value.id, remark.value.trim())
    signupVisible.value = false
    ElMessage.success(
      result.status === 0
        ? `名额已满，你已进入候补队列，当前排在第 ${result.position ?? '-'} 位`
        : '报名成功，请留意活动提醒',
    )
    await load()
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    submitting.value = false
  }
}

async function handleCancelSignup() {
  if (!activity.value) return
  try {
    await ElMessageBox.confirm(
      '取消后名额将释放给候补同学，如需再次参加需要重新报名。',
      '确认取消报名？',
      {
        confirmButtonText: '取消报名',
        cancelButtonText: '再想想',
        type: 'warning',
      },
    )
  } catch {
    return
  }
  try {
    await cancelSignup(activity.value.id)
    ElMessage.success('已取消报名')
    await load()
  } catch {
    // 错误提示由请求拦截器统一处理
  }
}

async function toggleFavorite() {
  if (!auth.isAuthenticated) {
    requireLogin()
    return
  }
  const item = activity.value
  if (!item) return
  try {
    if (item.is_favorited) {
      await unfavoriteActivity(item.id)
      item.is_favorited = false
      ElMessage.success('已取消收藏')
    } else {
      await favoriteActivity(item.id)
      item.is_favorited = true
      ElMessage.success('已加入收藏')
    }
  } catch {
    // 错误提示由请求拦截器统一处理
  }
}

function goCheckin() {
  if (!activity.value) return
  router.push({ name: 'checkin', query: { activity: String(activity.value.id) } })
}

async function share() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    ElMessage.success('活动链接已复制，去分享给同学吧')
  } catch {
    ElMessage.info('请手动复制浏览器地址栏中的链接')
  }
}

function goConsole(suffix: string) {
  if (!activity.value) return
  router.push(`/console/activities/${activity.value.id}/${suffix}`)
}

async function submitForReview() {
  if (!activity.value) return
  try {
    await ElMessageBox.confirm(
      '提交后将进入审核队列，审核通过后活动会自动发布。',
      '提交审核？',
      { confirmButtonText: '提交审核', cancelButtonText: '取消', type: 'info' },
    )
  } catch {
    return
  }
  try {
    await submitActivity(activity.value.id)
    ElMessage.success('已提交审核，请等待审核结果')
    await load()
  } catch {
    // 错误提示由请求拦截器统一处理
  }
}

async function handleCancelActivity() {
  if (!activity.value) return
  let reason = ''
  try {
    const result = await ElMessageBox.prompt(
      '下架后所有已报名同学会收到通知，名额将全部释放。请填写取消原因。',
      '取消活动',
      {
        confirmButtonText: '确认取消活动',
        cancelButtonText: '返回',
        inputPlaceholder: '例如：场地临时调整，活动延期举行',
        inputValidator: (value) => (value && value.trim().length >= 2 ? true : '请填写至少 2 个字的原因'),
        type: 'warning',
      },
    )
    reason = result.value
  } catch {
    return
  }
  try {
    await cancelActivity(activity.value.id, reason.trim())
    ElMessage.success('活动已取消，相关通知已发送')
    await load()
  } catch {
    // 错误提示由请求拦截器统一处理
  }
}

watch(
  () => route.params.id,
  () => {
    if (route.name === 'activity-detail') void load()
  },
  { immediate: true },
)

onMounted(() => {
  clock = window.setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onBeforeUnmount(() => {
  if (clock !== null) window.clearInterval(clock)
})
</script>

<template>
  <div class="detail-page">
    <div v-if="loading" class="page-container detail-loading">
      <div class="skeleton-banner skeleton-block"></div>
      <div class="detail-loading__grid">
        <div class="skeleton-body skeleton-block"></div>
        <div class="skeleton-side skeleton-block"></div>
      </div>
    </div>

    <div v-else-if="notFound || !activity" class="page-container page-block">
      <EmptyState
        title="活动不存在或尚未公开"
        description="活动可能已下架，或者你访问的链接有误。"
      >
        <RouterLink to="/activities">
          <el-button type="primary" round>返回活动广场</el-button>
        </RouterLink>
      </EmptyState>
    </div>

    <template v-else>
      <section class="detail-banner" :style="bannerStyle">
        <img
          v-if="hasCover"
          :src="activity.cover_url"
          :alt="activity.title"
          class="banner-image"
          @error="coverError = true"
        />
        <div class="banner-overlay"></div>
        <div class="banner-pattern"></div>

        <div class="page-container banner-inner">
          <div class="banner-topline">
            <RouterLink to="/activities" class="banner-back">
              <el-icon><Back /></el-icon>
              返回活动广场
            </RouterLink>
            <div class="banner-actions">
              <button type="button" class="glass-button" @click="share">
                <el-icon><Share /></el-icon>
                分享
              </button>
              <button
                type="button"
                class="glass-button"
                :class="{ 'is-active': activity.is_favorited }"
                @click="toggleFavorite"
              >
                <el-icon>
                  <StarFilled v-if="activity.is_favorited" />
                  <Star v-else />
                </el-icon>
                {{ activity.is_favorited ? '已收藏' : '收藏' }}
              </button>
            </div>
          </div>

          <div class="banner-content">
            <div class="banner-tags">
              <span class="banner-category">{{ activity.category?.name }}</span>
              <span class="banner-status">{{ status.label }}</span>
              <span v-if="activity.club?.name" class="banner-club">{{ activity.club.name }}</span>
            </div>
            <h1>{{ activity.title }}</h1>
            <p v-if="activity.summary">{{ activity.summary }}</p>

            <div class="banner-meta">
              <span>
                <el-icon><Calendar /></el-icon>
                {{ formatTimeRange(activity.start_time, activity.end_time) }}
              </span>
              <span>
                <el-icon><Location /></el-icon>
                {{ activity.location }}
              </span>
              <span>
                <el-icon><User /></el-icon>
                {{ activity.organizer?.display_name }}
              </span>
              <span>
                <el-icon><View /></el-icon>
                {{ activity.view_count }} 次浏览
              </span>
            </div>

            <div v-if="activity.tags.length" class="banner-tag-row">
              <span v-for="tag in activity.tags" :key="tag.id" class="banner-tag">
                {{ tag.name }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <div class="page-container detail-body">
        <div class="detail-main">
          <section v-if="activity.description" class="surface pad detail-section">
            <div class="section-title">
              <span class="section-index">01</span>
              <h2>活动详情</h2>
            </div>
            <div class="description-text">{{ activity.description }}</div>
          </section>

          <section class="surface pad detail-section">
            <div class="section-title">
              <span class="section-index">02</span>
              <h2>活动信息</h2>
            </div>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-icon"><el-icon><Calendar /></el-icon></span>
                <div>
                  <span>活动时间</span>
                  <strong>{{ formatTimeRange(activity.start_time, activity.end_time) }}</strong>
                </div>
              </div>
              <div class="info-item">
                <span class="info-icon"><el-icon><Clock /></el-icon></span>
                <div>
                  <span>报名时间</span>
                  <strong>{{ formatDateTime(activity.signup_start) }} 至 {{ formatDateTime(activity.signup_end) }}</strong>
                </div>
              </div>
              <div class="info-item">
                <span class="info-icon"><el-icon><Location /></el-icon></span>
                <div>
                  <span>活动地点</span>
                  <strong>{{ activity.location }}</strong>
                </div>
              </div>
              <div class="info-item">
                <span class="info-icon"><el-icon><User /></el-icon></span>
                <div>
                  <span>主办方</span>
                  <strong>{{ activity.organizer?.display_name }}</strong>
                </div>
              </div>
              <div class="info-item">
                <span class="info-icon"><el-icon><Tickets /></el-icon></span>
                <div>
                  <span>签到方式</span>
                  <strong>{{ checkinModeLabel(activity.checkin_mode) }}</strong>
                </div>
              </div>
              <div class="info-item">
                <span class="info-icon"><el-icon><View /></el-icon></span>
                <div>
                  <span>报名情况</span>
                  <strong>{{ activity.signup_count }} / {{ activity.capacity }} 人</strong>
                </div>
              </div>
            </div>

            <div v-if="activity.cancel_reason" class="cancel-reason">
              <el-icon><Warning /></el-icon>
              活动取消原因：{{ activity.cancel_reason }}
            </div>
          </section>

          <section v-if="auditVisible" class="surface pad detail-section">
            <div class="section-title">
              <span class="section-index">03</span>
              <h2>审核记录</h2>
            </div>
            <div class="audit-timeline">
              <div
                v-for="record in activity.audit_records"
                :key="record.id"
                class="audit-timeline__item"
                :class="{ 'is-reject': record.action === 2 }"
              >
                <div class="audit-head">
                  <strong>{{ record.action_text }}</strong>
                  <span>{{ formatDateTime(record.created_at) }}</span>
                </div>
                <p v-if="record.comment">{{ record.comment }}</p>
                <span class="audit-by">审核人：{{ record.auditor_name }}</span>
              </div>
            </div>
          </section>

          <section v-if="canManage" class="surface pad detail-section manage-section">
            <div class="section-title">
              <span class="section-index">管理</span>
              <h2>主办方工作区</h2>
            </div>
            <p class="manage-hint">
              已发布活动仅支持修改简介、详情、封面与标签。如需调整时间、容量等关键信息，请取消后重新发布。
            </p>
            <div class="manage-actions">
              <el-button :icon="EditPen" @click="goConsole('edit')">编辑活动</el-button>
              <el-button :icon="Tickets" @click="goConsole('roster')">报名名单</el-button>
              <el-button
                v-if="activity.checkin_mode !== 0"
                :icon="Camera"
                @click="goConsole('checkin')"
              >
                签到管理
              </el-button>
              <el-button :icon="TrendCharts" @click="goConsole('stats')">活动数据</el-button>
              <el-button
                v-if="activity.can_submit"
                type="primary"
                @click="submitForReview"
              >
                提交审核
              </el-button>
              <el-button
                v-if="canCancelActivity"
                type="danger"
                plain
                @click="handleCancelActivity"
              >
                取消活动
              </el-button>
            </div>
          </section>

          <section v-if="activity.can_audit" class="audit-callout">
            <div>
              <strong>该活动正在等待审核</strong>
              <span>前往审核工作台查看完整信息并通过或驳回。</span>
            </div>
            <RouterLink to="/console/audit">
              <el-button type="primary" round>去审核</el-button>
            </RouterLink>
          </section>
        </div>

        <aside class="detail-side">
          <div class="signup-card surface">
            <div class="signup-card__head">
              <span class="status-pill" :class="status.className">{{ status.label }}</span>
              <span class="view-count"><el-icon><View /></el-icon>{{ activity.view_count }}</span>
            </div>

            <div class="signup-progress">
              <div class="signup-progress__labels">
                <span>报名进度</span>
                <strong>{{ activity.signup_count }}<small> / {{ activity.capacity }}</small></strong>
              </div>
              <div class="signup-progress__bar">
                <span
                  :style="{
                    width: `${progress}%`,
                    background: activity.category?.color || '#3757e8',
                  }"
                ></span>
              </div>
              <div class="signup-progress__foot">
                <span v-if="activity.remaining > 0">剩余 {{ activity.remaining }} 个名额</span>
                <span v-else>名额已满</span>
                <span v-if="activity.waitlist_count">候补 {{ activity.waitlist_count }} 人</span>
              </div>
            </div>

            <div class="countdown-box">
              <span>{{ countdown.label }}</span>
              <strong>{{ countdown.value }}</strong>
            </div>

            <div v-if="mySignup" class="my-signup">
              <div class="my-signup__row">
                <span>我的报名状态</span>
                <span class="status-pill" :class="mySignup.status === 3 ? 'is-checked' : mySignup.status === 0 ? 'is-waitlist' : 'is-success'">
                  {{ mySignup.status_text }}
                </span>
              </div>
              <div v-if="mySignup.status === 0" class="my-signup__row">
                <span>候补序号</span>
                <strong>第 {{ mySignup.queue_no ?? '—' }} 位</strong>
              </div>
              <div v-if="mySignup.checked_in" class="my-signup__row">
                <span>签到状态</span>
                <strong class="text-success">已完成签到</strong>
              </div>
            </div>

            <el-button
              v-if="hasActiveSignup && mySignup?.status === 3"
              class="signup-button"
              size="large"
              type="success"
              plain
              disabled
            >
              已完成签到
            </el-button>
            <el-button
              v-else-if="canCheckin"
              class="signup-button"
              size="large"
              type="success"
              @click="goCheckin"
            >
              <el-icon style="margin-right: 6px"><Camera /></el-icon>
              立即扫码签到
            </el-button>
            <el-button
              v-else
              class="signup-button"
              size="large"
              type="primary"
              :disabled="signupButtonDisabled"
              :class="{ 'ch-button-gradient': !signupButtonDisabled }"
              @click="openSignup"
            >
              {{ signupButtonText }}
            </el-button>

            <div v-if="showWaitlistHint" class="waitlist-hint">
              名额已满，报名将自动进入候补队列。有人取消时，系统会按顺序自动转正并通知你。
            </div>

            <div v-if="!auth.isAuthenticated" class="login-hint">
              <RouterLink :to="{ name: 'login', query: { redirect: route.fullPath } }">
                登录
              </RouterLink>
              后即可报名、收藏与签到
            </div>

            <div v-else-if="canCancelSignup" class="signup-footer">
              <button type="button" class="cancel-signup-button" @click="handleCancelSignup">
                取消我的报名
              </button>
            </div>

            <div class="signup-card__divider"></div>

            <div class="organizer-mini">
              <UserAvatar
                :name="activity.organizer?.display_name"
                :src="activity.organizer?.avatar_url"
                :size="42"
              />
              <div>
                <span>主办方</span>
                <strong>{{ activity.organizer?.display_name }}</strong>
                <small>{{ activity.organizer?.college || activity.club?.name }}</small>
              </div>
            </div>
          </div>

          <div class="side-tip">
            <span class="side-tip__icon"><el-icon><InfoFilled /></el-icon></span>
            <div>
              <strong>参与须知</strong>
              <p>
                请按活动时间提前到场。需要签到的活动，现场扫描主办方展示的动态二维码即可完成签到。
              </p>
            </div>
          </div>

          <div v-if="activity.checkin_open" class="checkin-open-badge">
            <span class="live-dot"></span>
            签到通道已开启 · {{ formatDateTime(activity.checkin_window_end) }} 关闭
          </div>
        </aside>
      </div>
    </template>

    <el-dialog
      v-model="signupVisible"
      :title="activity && activity.remaining > 0 ? '确认报名' : '加入候补队列'"
      width="440px"
      align-center
    >
      <div v-if="activity" class="signup-dialog">
        <div class="signup-dialog__activity">
          <span :style="{ background: activity.category?.color }">{{ activity.category?.name }}</span>
          <strong>{{ activity.title }}</strong>
          <small>{{ formatTimeRange(activity.start_time, activity.end_time) }} · {{ activity.location }}</small>
        </div>
        <div v-if="activity.remaining > 0" class="signup-dialog__note is-success">
          <el-icon><CircleCheck /></el-icon>
          当前还有 {{ activity.remaining }} 个名额，提交后立即锁定。
        </div>
        <div v-else class="signup-dialog__note is-warning">
          <el-icon><Warning /></el-icon>
          当前名额已满，提交后将进入候补队列，有人取消时按顺序自动转正。
        </div>
        <el-form label-position="top">
          <el-form-item label="备注（可选）">
            <el-input
              v-model="remark"
              type="textarea"
              :rows="3"
              maxlength="200"
              show-word-limit
              placeholder="填写特殊需求或想对主办方说的话"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="signupVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          class="ch-button-gradient"
          @click="confirmSignup"
        >
          {{ activity && activity.remaining > 0 ? '确认报名' : '加入候补' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.detail-page {
  min-height: 60vh;
}

.detail-loading {
  padding-top: 32px;
}

.skeleton-banner {
  height: 320px;
}

.detail-loading__grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  margin-top: 24px;
}

.skeleton-body {
  height: 500px;
}

.skeleton-side {
  height: 420px;
}

.detail-banner {
  position: relative;
  padding: 28px 0 104px;
  overflow: hidden;
  color: #fff;
}

.banner-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.banner-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(7, 12, 26, 0.82) 0%, rgba(7, 12, 26, 0.46) 58%, rgba(7, 12, 26, 0.35)),
    linear-gradient(180deg, rgba(7, 12, 26, 0.15), rgba(7, 12, 26, 0.55));
}

.banner-pattern {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.14) 1px, transparent 1px);
  background-size: 26px 26px;
  opacity: 0.3;
  mask-image: linear-gradient(90deg, #000, transparent 75%);
  pointer-events: none;
}

.banner-inner {
  position: relative;
  z-index: 1;
}

.banner-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.banner-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 12.5px;
  font-weight: 500;
  transition: color 0.2s ease;
}

.banner-back:hover {
  color: #fff;
}

.banner-actions {
  display: flex;
  gap: 8px;
}

.glass-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 13px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.86);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
}

.glass-button:hover {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.34);
}

.glass-button.is-active {
  color: #ffd48a;
}

.banner-content {
  max-width: 760px;
  margin-top: 42px;
}

.banner-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.banner-category {
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--ch-ink);
  font-size: 11.5px;
  font-weight: 700;
}

.banner-status {
  padding: 5px 11px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.86);
  font-size: 11.5px;
  font-weight: 600;
  backdrop-filter: blur(8px);
}

.banner-club {
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

.banner-content h1 {
  margin-top: 16px;
  font-size: clamp(32px, 4.4vw, 46px);
  line-height: 1.18;
  letter-spacing: -0.03em;
  text-shadow: 0 6px 30px rgba(0, 0, 0, 0.18);
}

.banner-content > p {
  max-width: 660px;
  margin-top: 13px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14.5px;
  line-height: 1.7;
}

.banner-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin-top: 22px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 12.5px;
}

.banner-meta span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.banner-meta .el-icon {
  color: rgba(255, 255, 255, 0.46);
}

.banner-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 16px;
}

.banner-tag {
  padding: 3px 9px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.64);
  font-size: 11px;
}

.detail-body {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 24px;
  margin-top: -64px;
  padding-bottom: 24px;
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.detail-section {
  padding: 30px 32px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 22px;
}

.section-index {
  display: grid;
  place-items: center;
  min-width: 30px;
  height: 24px;
  padding: 0 7px;
  border-radius: 7px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.section-title h2 {
  font-size: 20px;
  letter-spacing: -0.02em;
}

.description-text {
  color: var(--ch-ink-soft);
  font-size: 14.5px;
  line-height: 1.95;
  white-space: pre-line;
  word-break: break-word;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px 24px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.info-icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #f5f7fd;
  color: var(--ch-primary);
  font-size: 16px;
}

.info-item div {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.5;
}

.info-item span {
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.info-item strong {
  margin-top: 2px;
  color: var(--ch-ink-soft);
  font-size: 13px;
  font-weight: 600;
  word-break: break-word;
}

.cancel-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 22px;
  padding: 13px 15px;
  border-radius: 10px;
  background: #fdecec;
  color: #b83a3e;
  font-size: 12.5px;
  line-height: 1.6;
}

.audit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.audit-head strong {
  font-size: 13px;
}

.audit-head span {
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.audit-timeline p {
  margin-top: 6px;
  color: var(--ch-muted);
  font-size: 13px;
  line-height: 1.7;
}

.audit-by {
  display: inline-block;
  margin-top: 6px;
  color: var(--ch-muted-light);
  font-size: 11px;
}

.manage-section .manage-hint {
  margin-top: -10px;
  margin-bottom: 18px;
  color: var(--ch-muted);
  font-size: 12.5px;
  line-height: 1.7;
}

.manage-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.manage-actions .el-button {
  margin-left: 0;
}

.audit-callout {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 20px 24px;
  border: 1px solid rgba(217, 138, 0, 0.24);
  border-radius: var(--ch-radius);
  background: #fff9ee;
}

.audit-callout div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.audit-callout strong {
  font-size: 14px;
}

.audit-callout span {
  color: #9b701f;
  font-size: 12.5px;
}

.detail-side {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.signup-card {
  position: sticky;
  top: 90px;
  padding: 24px;
}

.signup-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.view-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.signup-progress {
  margin-top: 22px;
}

.signup-progress__labels {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  color: var(--ch-muted);
  font-size: 12px;
}

.signup-progress__labels strong {
  color: var(--ch-ink);
  font-size: 22px;
  font-weight: 750;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.signup-progress__labels small {
  color: var(--ch-muted-light);
  font-size: 12px;
  font-weight: 500;
}

.signup-progress__bar {
  height: 8px;
  margin-top: 8px;
  border-radius: 999px;
  background: #edf0f8;
  overflow: hidden;
}

.signup-progress__bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.4s ease;
}

.signup-progress__foot {
  display: flex;
  justify-content: space-between;
  margin-top: 7px;
  color: var(--ch-muted-light);
  font-size: 11px;
}

.countdown-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
  padding: 12px 14px;
  border: 1px solid #edf0f8;
  border-radius: 11px;
  background: #fafbff;
}

.countdown-box span {
  color: var(--ch-muted);
  font-size: 11.5px;
}

.countdown-box strong {
  color: var(--ch-primary);
  font-size: 13px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.my-signup {
  margin-top: 14px;
  padding: 13px 14px;
  border-radius: 11px;
  background: var(--ch-primary-soft);
}

.my-signup__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  color: var(--ch-muted);
}

.my-signup__row + .my-signup__row {
  margin-top: 8px;
}

.my-signup__row strong {
  color: var(--ch-ink-soft);
  font-size: 12px;
}

.text-success {
  color: var(--ch-success) !important;
}

.signup-button {
  width: 100%;
  height: 48px;
  margin-top: 18px;
  border-radius: 12px;
  font-size: 14.5px;
}

.waitlist-hint {
  margin-top: 12px;
  padding: 11px 12px;
  border-radius: 9px;
  background: #fff8ea;
  color: #9b701f;
  font-size: 11.5px;
  line-height: 1.65;
}

.login-hint {
  margin-top: 12px;
  text-align: center;
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.login-hint a {
  color: var(--ch-primary);
  font-weight: 700;
}

.signup-footer {
  margin-top: 14px;
  text-align: center;
}

.cancel-signup-button {
  padding: 4px;
  border: none;
  background: transparent;
  color: var(--ch-muted-light);
  font-size: 11.5px;
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}

.cancel-signup-button:hover {
  color: var(--ch-danger);
}

.signup-card__divider {
  height: 1px;
  margin: 20px 0;
  background: #f0f3fa;
}

.organizer-mini {
  display: flex;
  align-items: center;
  gap: 11px;
}

.organizer-mini > div {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}

.organizer-mini span {
  color: var(--ch-muted-light);
  font-size: 10px;
  letter-spacing: 0.06em;
}

.organizer-mini strong {
  font-size: 12.5px;
}

.organizer-mini small {
  color: var(--ch-muted);
  font-size: 11px;
}

.side-tip {
  display: flex;
  gap: 11px;
  padding: 18px;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius-sm);
  background: #fff;
}

.side-tip__icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  font-size: 15px;
}

.side-tip div {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.side-tip strong {
  font-size: 12px;
}

.side-tip p {
  color: var(--ch-muted);
  font-size: 11.5px;
  line-height: 1.65;
}

.checkin-open-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  border: 1px solid rgba(15, 159, 110, 0.2);
  border-radius: 10px;
  background: #effaf6;
  color: #0b8a5f;
  font-size: 11.5px;
  font-weight: 600;
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #0f9f6e;
  box-shadow: 0 0 0 3px rgba(15, 159, 110, 0.15);
}

.signup-dialog__activity {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 16px;
  border-radius: 12px;
  background: #f7f9fe;
}

.signup-dialog__activity span {
  align-self: flex-start;
  padding: 2px 8px;
  border-radius: 5px;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
}

.signup-dialog__activity strong {
  font-size: 15px;
  line-height: 1.4;
}

.signup-dialog__activity small {
  color: var(--ch-muted);
  font-size: 11.5px;
}

.signup-dialog__note {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 14px;
  padding: 11px 13px;
  border-radius: 9px;
  font-size: 12px;
}

.signup-dialog__note.is-success {
  background: #effaf6;
  color: #0b8a5f;
}

.signup-dialog__note.is-warning {
  background: #fff8ea;
  color: #9b701f;
}

.signup-dialog :deep(.el-form) {
  margin-top: 18px;
}

.signup-dialog :deep(.el-form-item) {
  margin-bottom: 0;
}

@media (max-width: 1060px) {
  .detail-body {
    grid-template-columns: minmax(0, 1fr) 340px;
  }

  .info-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  .detail-body {
    grid-template-columns: minmax(0, 1fr);
    margin-top: -50px;
  }

  .signup-card {
    position: static;
  }

  .detail-side {
    order: -1;
  }
}

@media (max-width: 640px) {
  .detail-banner {
    padding-bottom: 84px;
  }

  .banner-content {
    margin-top: 30px;
  }

  .banner-meta {
    gap: 10px 16px;
  }

  .detail-section {
    padding: 22px;
  }

  .detail-body {
    margin-top: -44px;
  }

  .detail-loading__grid {
    grid-template-columns: 1fr;
  }

  .skeleton-side {
    display: none;
  }
}
</style>
