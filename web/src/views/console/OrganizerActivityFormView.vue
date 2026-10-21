<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  ArrowLeft,
  Calendar,
  CircleCheck,
  CircleClose,
  Clock,
  Document,
  Location,
  Picture,
  Promotion,
  Tickets,
  Warning,
} from '@element-plus/icons-vue'

import {
  createActivity,
  getActivity,
  listCategories,
  listTags,
  submitActivity,
  updateActivity,
} from '@/api/activities'
import type { ActivityDetail, ActivityPayload, Category, Tag } from '@/types'
import {
  activityStatusMeta,
  formatTimeRange,
  toApiDateTime,
  toDateTimeValue,
} from '@/utils/format'

const route = useRoute()
const router = useRouter()

const activityId = ref<number | null>(
  route.params.id ? Number(route.params.id) : null,
)

const loading = ref(true)
const saving = ref(false)
const saveMode = ref<'draft' | 'submit' | null>(null)
const formRef = ref<FormInstance | null>(null)
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])
const detail = ref<ActivityDetail | null>(null)

function defaultSchedule() {
  const start = dayjs().add(3, 'day').hour(14).minute(0).second(0)
  return {
    start_time: start,
    end_time: start.add(2, 'hour'),
    signup_start: dayjs().hour(9).minute(0).second(0),
    signup_end: start.subtract(2, 'hour'),
  }
}

const schedule = defaultSchedule()

const form = reactive<Required<ActivityPayload>>({
  title: '',
  summary: '',
  description: '',
  cover_url: '',
  location: '',
  start_time: toDateTimeValue(schedule.start_time.toISOString()),
  end_time: toDateTimeValue(schedule.end_time.toISOString()),
  signup_start: toDateTimeValue(schedule.signup_start.toISOString()),
  signup_end: toDateTimeValue(schedule.signup_end.toISOString()),
  capacity: 60,
  waitlist_enabled: true,
  waitlist_limit: 0,
  checkin_mode: 2,
  category_id: 0,
  tag_ids: [],
})

const coverError = ref(false)

const isEdit = computed(() => Boolean(activityId.value))
const isPublished = computed(() => detail.value?.status === 2)
const blocked = computed(
  () => detail.value !== null && ![0, 2, 5].includes(detail.value.status),
)
const canSubmit = computed(
  () => !detail.value || [0, 5].includes(detail.value.status),
)

const selectedCategory = computed(() =>
  categories.value.find((item) => item.id === form.category_id),
)
const selectedTags = computed(() =>
  tags.value.filter((item) => form.tag_ids?.includes(item.id)),
)
const coverPreview = computed(() =>
  form.cover_url && !coverError.value ? form.cover_url : '',
)

const checkinModes = [
  {
    value: 2,
    title: '动态码签到',
    description: '签到码每 30 秒刷新，防代签能力最好，推荐使用。',
  },
  {
    value: 1,
    title: '静态码签到',
    description: '固定二维码，适合人数较少、网络受限的活动。',
  },
  {
    value: 0,
    title: '无需签到',
    description: '只统计报名，不记录到场情况。',
  },
]

const readiness = computed(() => [
  { label: '活动标题与分类', done: Boolean(form.title.trim() && form.category_id) },
  { label: '时间与地点', done: Boolean(form.start_time && form.end_time && form.location.trim()) },
  { label: '报名时间窗口', done: Boolean(form.signup_start && form.signup_end) },
  { label: '活动详情', done: form.description.trim().length >= 20 },
  { label: '报名人数上限', done: form.capacity >= 1 },
])

const readyCount = computed(() => readiness.value.filter((item) => item.done).length)

function validateEndTime(_rule: unknown, value: string, callback: (error?: Error) => void) {
  if (!value || !form.start_time) return callback()
  if (!dayjs(value).isAfter(dayjs(form.start_time))) {
    return callback(new Error('结束时间必须晚于活动开始时间'))
  }
  callback()
}

function validateSignupEnd(_rule: unknown, value: string, callback: (error?: Error) => void) {
  if (!value) return callback()
  if (form.signup_start && !dayjs(value).isAfter(dayjs(form.signup_start))) {
    return callback(new Error('报名截止时间必须晚于报名开始时间'))
  }
  if (form.start_time && dayjs(value).isAfter(dayjs(form.start_time))) {
    return callback(new Error('报名截止时间不能晚于活动开始时间'))
  }
  callback()
}

function validateCover(_rule: unknown, value: string, callback: (error?: Error) => void) {
  if (!value) return callback()
  if (!/^(https?:\/\/|\/)/.test(value)) {
    return callback(new Error('封面地址必须以 http(s):// 或 / 开头'))
  }
  callback()
}

const rules: FormRules = {
  title: [
    { required: true, message: '请填写活动标题', trigger: 'blur' },
    { max: 120, message: '标题不能超过 120 个字符', trigger: 'blur' },
  ],
  category_id: [{ required: true, message: '请选择活动分类', trigger: 'change' }],
  summary: [{ max: 255, message: '简介不能超过 255 个字符', trigger: 'blur' }],
  location: [{ required: true, message: '请填写活动地点', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择活动开始时间', trigger: 'change' }],
  end_time: [
    { required: true, message: '请选择活动结束时间', trigger: 'change' },
    { validator: validateEndTime, trigger: 'change' },
  ],
  signup_start: [{ required: true, message: '请选择报名开始时间', trigger: 'change' }],
  signup_end: [
    { required: true, message: '请选择报名截止时间', trigger: 'change' },
    { validator: validateSignupEnd, trigger: 'change' },
  ],
  capacity: [{ required: true, message: '请填写报名人数上限', trigger: 'blur' }],
  cover_url: [{ validator: validateCover, trigger: 'blur' }],
}

function revalidateTimes() {
  formRef.value?.validateField(['end_time', 'signup_end']).catch(() => undefined)
}

async function load() {
  loading.value = true
  try {
    const [categoryData, tagData] = await Promise.all([listCategories(), listTags()])
    categories.value = categoryData
    tags.value = tagData
    if (categoryData.length && !form.category_id) {
      form.category_id = categoryData[0].id
    }
    if (activityId.value) {
      const data = await getActivity(activityId.value)
      detail.value = data
      form.title = data.title
      form.summary = data.summary
      form.description = data.description
      form.cover_url = data.cover_url
      form.location = data.location
      form.start_time = toDateTimeValue(data.start_time)
      form.end_time = toDateTimeValue(data.end_time)
      form.signup_start = toDateTimeValue(data.signup_start)
      form.signup_end = toDateTimeValue(data.signup_end)
      form.capacity = data.capacity
      form.waitlist_enabled = data.waitlist_enabled
      form.waitlist_limit = data.waitlist_limit
      form.checkin_mode = data.checkin_mode
      form.category_id = data.category.id
      form.tag_ids = data.tags.map((tag) => tag.id)
    }
  } catch {
    // 接口错误由请求拦截器提示
  } finally {
    loading.value = false
  }
}

function buildPayload(): Partial<ActivityPayload> {
  if (isPublished.value) {
    return {
      summary: form.summary,
      description: form.description,
      cover_url: form.cover_url,
      tag_ids: form.tag_ids,
    }
  }
  return {
    title: form.title.trim(),
    summary: form.summary.trim(),
    description: form.description,
    cover_url: form.cover_url.trim(),
    location: form.location.trim(),
    start_time: toApiDateTime(form.start_time),
    end_time: toApiDateTime(form.end_time),
    signup_start: toApiDateTime(form.signup_start),
    signup_end: toApiDateTime(form.signup_end),
    capacity: Number(form.capacity),
    waitlist_enabled: form.waitlist_enabled,
    waitlist_limit: Number(form.waitlist_limit || 0),
    checkin_mode: form.checkin_mode,
    category_id: form.category_id,
    tag_ids: form.tag_ids,
  }
}

async function persist() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return null
  if (!form.category_id) {
    ElMessage.warning('请选择活动分类')
    return null
  }
  const payload = buildPayload()
  if (isEdit.value && activityId.value) {
    const updated = await updateActivity(activityId.value, payload)
    detail.value = updated
    return updated.id
  }
  const created = await createActivity(payload as ActivityPayload)
  detail.value = created
  activityId.value = created.id
  await router.replace(`/console/activities/${created.id}/edit`)
  return created.id
}

async function save(asDraft: boolean) {
  if (saving.value) return
  const wasEdit = isEdit.value
  saveMode.value = asDraft ? 'draft' : 'submit'
  saving.value = true
  try {
    const id = await persist()
    if (!id) return
    if (asDraft) {
      ElMessage.success(wasEdit ? '活动信息已保存' : '活动草稿已创建')
      if (!wasEdit) await load()
      return
    }
    await submitActivity(id)
    ElMessage.success('活动已提交审核，请等待审核结果')
    router.push('/console/activities')
  } catch {
    // 接口错误由请求拦截器提示；创建成功后提交失败时停留在当前编辑页
  } finally {
    saving.value = false
    saveMode.value = null
  }
}

function goBack() {
  router.push('/console/activities')
}

onMounted(load)
</script>

<template>
  <div class="activity-form-page" v-loading="loading">
    <div class="page-head">
      <div>
        <button type="button" class="back-link" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回我的活动
        </button>
        <div class="page-head__title">
          <h1>{{ isEdit ? '编辑活动' : '发布新活动' }}</h1>
          <span
            v-if="detail"
            class="status-pill"
            :class="activityStatusMeta(detail.status).className"
          >
            {{ detail.status_text }}
          </span>
        </div>
        <p>{{ isEdit ? '调整活动信息并重新提交审核。' : '填写活动信息，保存草稿后可随时继续编辑。' }}</p>
      </div>
    </div>

    <div v-if="blocked && detail" class="blocked-card">
      <div class="blocked-card__icon">
        <el-icon><Warning /></el-icon>
      </div>
      <div>
        <h2>当前状态不可编辑</h2>
        <p>
          活动处于「{{ detail.status_text }}」状态。只有草稿、已驳回和已发布活动支持编辑，已发布活动仅可调整简介、详情、封面和标签。
        </p>
        <el-button round @click="goBack">返回活动列表</el-button>
      </div>
    </div>

    <template v-else>
      <el-alert
        v-if="isPublished"
        type="warning"
        :closable="false"
        show-icon
        class="publish-alert"
        title="已发布活动受限编辑"
        description="活动时间、地点、人数等关键信息已锁定，仅支持修改简介、详情、封面和标签。如需调整关键信息，请先取消活动后重新创建。"
      />

      <div class="form-layout">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          class="form-main"
          @submit.prevent
        >
          <section class="form-card">
            <div class="form-card__head">
              <span class="form-card__step">01</span>
              <div>
                <h2>基础信息</h2>
                <p>让同学快速了解活动的主题与分类。</p>
              </div>
            </div>
            <div class="form-grid">
              <el-form-item label="活动标题" prop="title" class="span-2">
                <el-input
                  v-model="form.title"
                  maxlength="120"
                  show-word-limit
                  placeholder="例如：春季校园公益跑"
                  :disabled="isPublished"
                />
              </el-form-item>
              <el-form-item label="活动分类" prop="category_id">
                <el-select
                  v-model="form.category_id"
                  placeholder="请选择分类"
                  style="width: 100%"
                  :disabled="isPublished"
                >
                  <el-option
                    v-for="category in categories"
                    :key="category.id"
                    :label="category.name"
                    :value="category.id"
                  >
                    <span class="option-dot" :style="{ background: category.color }"></span>
                    {{ category.name }}
                  </el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="活动标签">
                <el-select
                  v-model="form.tag_ids"
                  multiple
                  collapse-tags
                  collapse-tags-tooltip
                  placeholder="选择标签（可多选）"
                  style="width: 100%"
                >
                  <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id">
                    <span class="option-dot" :style="{ background: tag.color }"></span>
                    {{ tag.name }}
                  </el-option>
                </el-select>
              </el-form-item>
              <el-form-item label="一句话简介" prop="summary" class="span-2">
                <el-input
                  v-model="form.summary"
                  maxlength="255"
                  show-word-limit
                  placeholder="用一句话概括活动亮点，会展示在活动卡片中"
                />
              </el-form-item>
            </div>
          </section>

          <section class="form-card">
            <div class="form-card__head">
              <span class="form-card__step">02</span>
              <div>
                <h2>时间与地点</h2>
                <p>请确保活动结束时间晚于当前时间，报名截止不能晚于活动开始。</p>
              </div>
            </div>
            <div class="form-grid">
              <el-form-item label="活动开始时间" prop="start_time">
                <el-date-picker
                  v-model="form.start_time"
                  type="datetime"
                  value-format="YYYY-MM-DDTHH:mm:ssZ"
                  placeholder="选择开始时间"
                  style="width: 100%"
                  :disabled="isPublished"
                  @change="revalidateTimes"
                />
              </el-form-item>
              <el-form-item label="活动结束时间" prop="end_time">
                <el-date-picker
                  v-model="form.end_time"
                  type="datetime"
                  value-format="YYYY-MM-DDTHH:mm:ssZ"
                  placeholder="选择结束时间"
                  style="width: 100%"
                  :disabled="isPublished"
                />
              </el-form-item>
              <el-form-item label="报名开始时间" prop="signup_start">
                <el-date-picker
                  v-model="form.signup_start"
                  type="datetime"
                  value-format="YYYY-MM-DDTHH:mm:ssZ"
                  placeholder="选择报名开始时间"
                  style="width: 100%"
                  :disabled="isPublished"
                  @change="revalidateTimes"
                />
              </el-form-item>
              <el-form-item label="报名截止时间" prop="signup_end">
                <el-date-picker
                  v-model="form.signup_end"
                  type="datetime"
                  value-format="YYYY-MM-DDTHH:mm:ssZ"
                  placeholder="选择报名截止时间"
                  style="width: 100%"
                  :disabled="isPublished"
                />
              </el-form-item>
              <el-form-item label="活动地点" prop="location" class="span-2">
                <el-input
                  v-model="form.location"
                  maxlength="200"
                  placeholder="例如：东校区大学生活动中心 301"
                  :disabled="isPublished"
                  :prefix-icon="Location"
                />
              </el-form-item>
            </div>
          </section>

          <section class="form-card">
            <div class="form-card__head">
              <span class="form-card__step">03</span>
              <div>
                <h2>报名与签到</h2>
                <p>设置人数上限、候补规则和现场签到方式。</p>
              </div>
            </div>
            <div class="form-grid">
              <el-form-item label="报名人数上限" prop="capacity">
                <el-input-number
                  v-model="form.capacity"
                  :min="1"
                  :max="100000"
                  :step="10"
                  controls-position="right"
                  style="width: 100%"
                  :disabled="isPublished"
                />
              </el-form-item>
              <el-form-item label="候补设置">
                <div class="switch-row">
                  <el-switch
                    v-model="form.waitlist_enabled"
                    active-text="开启候补"
                    :disabled="isPublished"
                  />
                  <el-input-number
                    v-if="form.waitlist_enabled"
                    v-model="form.waitlist_limit"
                    :min="0"
                    :max="100000"
                    controls-position="right"
                    class="waitlist-input"
                    :disabled="isPublished"
                  />
                  <span class="field-hint">候补上限，0 表示不限</span>
                </div>
              </el-form-item>
              <el-form-item label="签到方式" class="span-2">
                <div class="mode-options">
                  <button
                    v-for="mode in checkinModes"
                    :key="mode.value"
                    type="button"
                    class="mode-option"
                    :class="{ 'is-active': form.checkin_mode === mode.value }"
                    :disabled="isPublished"
                    @click="form.checkin_mode = mode.value"
                  >
                    <span class="mode-option__dot"></span>
                    <strong>{{ mode.title }}</strong>
                    <p>{{ mode.description }}</p>
                  </button>
                </div>
              </el-form-item>
            </div>
          </section>

          <section class="form-card">
            <div class="form-card__head">
              <span class="form-card__step">04</span>
              <div>
                <h2>活动详情</h2>
                <p>补充完整介绍，帮助同学了解流程、注意事项与参与收获。</p>
              </div>
            </div>
            <div class="form-grid">
              <el-form-item label="封面图片地址" prop="cover_url" class="span-2">
                <el-input
                  v-model="form.cover_url"
                  maxlength="500"
                  placeholder="https://example.com/cover.jpg，可留空使用分类默认封面"
                  :prefix-icon="Picture"
                  @input="coverError = false"
                />
              </el-form-item>
              <el-form-item label="活动详情" prop="description" class="span-2">
                <el-input
                  v-model="form.description"
                  type="textarea"
                  :rows="10"
                  maxlength="5000"
                  show-word-limit
                  placeholder="介绍活动背景、流程安排、参与须知、联系人等信息。"
                />
              </el-form-item>
            </div>
          </section>
        </el-form>

        <aside class="form-side">
          <div class="side-card side-card--actions">
            <h3>{{ isEdit ? '保存修改' : '发布活动' }}</h3>
            <p class="side-card__hint">
              {{
                isPublished
                  ? '已发布活动保存后会立即生效。'
                  : '建议先保存草稿，确认信息无误后再提交审核。'
              }}
            </p>
            <el-button
              v-if="canSubmit"
              type="primary"
              size="large"
              round
              class="submit-button"
              :loading="saving && saveMode === 'submit'"
              :disabled="saving"
              :icon="Promotion"
              @click="save(false)"
            >
              保存并提交审核
            </el-button>
            <el-button
              size="large"
              round
              class="draft-button"
              :loading="saving && saveMode === 'draft'"
              :disabled="saving"
              :icon="Document"
              @click="save(true)"
            >
              {{ isPublished ? '保存修改' : '保存草稿' }}
            </el-button>
            <el-button text class="back-button" @click="goBack">暂时离开</el-button>
          </div>

          <div class="side-card">
            <div class="side-card__head">
              <h3>发布检查</h3>
              <span>{{ readyCount }}/{{ readiness.length }}</span>
            </div>
            <ul class="checklist">
              <li v-for="item in readiness" :key="item.label" :class="{ 'is-done': item.done }">
                <el-icon>
                  <CircleCheck v-if="item.done" />
                  <CircleClose v-else />
                </el-icon>
                {{ item.label }}
              </li>
            </ul>
          </div>

          <div class="side-card side-card--preview">
            <h3>活动预览</h3>
            <div
              class="preview-cover"
              :style="{ background: selectedCategory?.color || '#3757e8' }"
            >
              <img v-if="coverPreview" :src="coverPreview" alt="封面预览" @error="coverError = true" />
              <div v-else class="preview-cover__fallback">
                <el-icon><Calendar /></el-icon>
                <span>{{ selectedCategory?.name || '选择活动分类' }}</span>
              </div>
            </div>
            <strong class="preview-title">{{ form.title || '活动标题将在这里展示' }}</strong>
            <p class="preview-summary">{{ form.summary || '一句话简介会出现在活动卡片中。' }}</p>
            <div class="preview-meta">
              <span><el-icon><Clock /></el-icon>{{ formatTimeRange(form.start_time, form.end_time) }}</span>
              <span><el-icon><Location /></el-icon>{{ form.location || '活动地点待定' }}</span>
              <span><el-icon><Tickets /></el-icon>限 {{ form.capacity }} 人</span>
            </div>
            <div v-if="selectedTags.length" class="preview-tags">
              <span v-for="tag in selectedTags" :key="tag.id" class="tag-chip">{{ tag.name }}</span>
            </div>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.activity-form-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-height: 480px;
}

.page-head__title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

.page-head h1 {
  font-size: 30px;
  letter-spacing: -0.03em;
}

.page-head p {
  margin-top: 6px;
  color: var(--ch-muted);
  font-size: 14px;
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

.publish-alert {
  margin-bottom: 2px;
  border-radius: 14px;
}

.blocked-card {
  display: flex;
  gap: 20px;
  padding: 32px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.blocked-card__icon {
  display: grid;
  place-items: center;
  flex: 0 0 54px;
  width: 54px;
  height: 54px;
  border-radius: 16px;
  background: #fff5e3;
  color: #c07c00;
  font-size: 26px;
}

.blocked-card h2 {
  font-size: 20px;
}

.blocked-card p {
  margin: 8px 0 18px;
  max-width: 640px;
  color: var(--ch-muted);
  font-size: 14px;
}

.form-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 22px;
  align-items: start;
}

.form-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-card {
  padding: 26px 28px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.form-card__head {
  display: flex;
  gap: 14px;
  margin-bottom: 22px;
}

.form-card__step {
  display: grid;
  place-items: center;
  flex: 0 0 40px;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  font-size: 13px;
  font-weight: 800;
}

.form-card__head h2 {
  font-size: 17px;
  line-height: 1.4;
}

.form-card__head p {
  margin-top: 3px;
  color: var(--ch-muted);
  font-size: 12px;
}

.option-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 8px;
  border-radius: 50%;
}

.switch-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.waitlist-input {
  width: 120px;
}

.field-hint {
  color: var(--ch-muted-light);
  font-size: 12px;
}

.mode-options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
}

.mode-option {
  position: relative;
  padding: 16px;
  text-align: left;
  background: #fbfcff;
  border: 1px solid var(--ch-border);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.mode-option:hover:not(:disabled) {
  border-color: #b9c5f5;
}

.mode-option.is-active {
  border-color: var(--ch-primary);
  background: var(--ch-primary-soft);
  box-shadow: 0 0 0 3px rgba(55, 87, 232, 0.1);
}

.mode-option:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.mode-option__dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-bottom: 10px;
  border-radius: 50%;
  background: var(--ch-border-strong);
}

.mode-option.is-active .mode-option__dot {
  background: var(--ch-primary);
  box-shadow: 0 0 0 4px rgba(55, 87, 232, 0.16);
}

.mode-option strong {
  display: block;
  font-size: 14px;
}

.mode-option p {
  margin-top: 5px;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.55;
}

.form-side {
  position: sticky;
  top: 90px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.side-card {
  padding: 20px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.side-card h3 {
  font-size: 15px;
}

.side-card--actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background:
    radial-gradient(280px 160px at 100% 0%, rgba(55, 87, 232, 0.08), transparent 70%),
    #fff;
}

.side-card__hint {
  margin-bottom: 6px;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.6;
}

.submit-button,
.draft-button {
  width: 100%;
  margin-left: 0;
}

.back-button {
  align-self: center;
  color: var(--ch-muted);
}

.side-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.side-card__head span {
  color: var(--ch-muted-light);
  font-size: 12px;
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
}

.checklist li {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ch-muted-light);
  font-size: 13px;
}

.checklist li .el-icon {
  font-size: 16px;
}

.checklist li.is-done {
  color: var(--ch-ink-soft);
}

.checklist li.is-done .el-icon {
  color: var(--ch-success);
}

.preview-cover {
  position: relative;
  height: 128px;
  margin: 14px 0;
  border-radius: 12px;
  overflow: hidden;
}

.preview-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-cover__fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 100%;
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
}

.preview-cover__fallback .el-icon {
  font-size: 28px;
}

.preview-title {
  display: block;
  font-size: 14px;
  line-height: 1.4;
}

.preview-summary {
  margin-top: 6px;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.6;
}

.preview-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--ch-border);
  color: var(--ch-muted);
  font-size: 12px;
}

.preview-meta span {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.preview-meta .el-icon {
  margin-top: 2px;
  color: var(--ch-muted-light);
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

@media (max-width: 1080px) {
  .form-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .form-side {
    position: static;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .side-card--actions {
    grid-row: span 2;
  }
}

@media (max-width: 720px) {
  .form-card {
    padding: 20px 18px;
  }

  .form-side {
    grid-template-columns: minmax(0, 1fr);
  }

  .mode-options {
    grid-template-columns: minmax(0, 1fr);
  }

  .side-card--actions {
    grid-row: auto;
  }
}
</style>
