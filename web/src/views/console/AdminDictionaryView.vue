<script setup lang="ts">
import { computed, onMounted, reactive, ref, type Component } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Basketball,
  Brush,
  Calendar,
  Camera,
  Check,
  Coffee,
  Compass,
  EditPen,
  Film,
  Flag,
  Microphone,
  Plus,
  Present,
  Promotion,
  Reading,
  Star,
  Trophy,
} from '@element-plus/icons-vue'

import {
  createCategory,
  createTag,
  listAdminCategories,
  listAdminTags,
  updateCategory,
  updateTag,
} from '@/api/admin'
import EmptyState from '@/components/EmptyState.vue'
import type { Category, Tag } from '@/types'

type DictTab = 'category' | 'tag'

const iconMap: Record<string, Component> = {
  Calendar,
  Reading,
  Microphone,
  Trophy,
  Star,
  Flag,
  Promotion,
  Basketball,
  Brush,
  Camera,
  Compass,
  Film,
  Coffee,
  Present,
}

const iconOptions = Object.keys(iconMap)
const colorPresets = ['#3757e8', '#7a5af8', '#f97316', '#0f9f6e', '#ec4899', '#0ea5e9', '#d98a00', '#64748b']

const activeTab = ref<DictTab>('category')
const loading = ref(true)
const saving = ref(false)
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance | null>(null)

const form = reactive({
  name: '',
  slug: '',
  icon: 'Calendar',
  color: '#3757e8',
  sort_order: 0,
  is_active: true,
})

const dialogTitle = computed(() => {
  const label = activeTab.value === 'category' ? '活动分类' : '活动标签'
  return editingId.value ? `编辑${label}` : `新增${label}`
})

const rules = computed<FormRules>(() => {
  if (activeTab.value === 'category') {
    return {
      name: [
        { required: true, message: '请填写分类名称', trigger: 'blur' },
        { max: 50, message: '名称不能超过 50 个字符', trigger: 'blur' },
      ],
      slug: [
        { required: true, message: '请填写分类标识', trigger: 'blur' },
        {
          pattern: /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
          message: '标识仅支持小写字母、数字和连字符，如 lecture-2',
          trigger: 'blur',
        },
      ],
      color: [{ pattern: /^#([\da-f]{3}|[\da-f]{6})$/i, message: '请输入合法的颜色值', trigger: 'blur' }],
    }
  }
  return {
    name: [
      { required: true, message: '请填写标签名称', trigger: 'blur' },
      { max: 32, message: '名称不能超过 32 个字符', trigger: 'blur' },
    ],
    color: [{ pattern: /^#([\da-f]{3}|[\da-f]{6})$/i, message: '请输入合法的颜色值', trigger: 'blur' }],
  }
})

const activeCategoryCount = computed(() => categories.value.filter((item) => item.is_active).length)
const activeTagCount = computed(() => tags.value.filter((item) => item.is_active).length)

function suggestSlug() {
  if (form.slug || activeTab.value !== 'category') return
  const pinyinSafe = form.name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  if (pinyinSafe) form.slug = pinyinSafe
}

async function load() {
  loading.value = true
  try {
    const [categoryData, tagData] = await Promise.all([listAdminCategories(), listAdminTags()])
    categories.value = categoryData
    tags.value = tagData
  } catch {
    // 接口错误由拦截器提示
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.name = ''
  form.slug = ''
  form.icon = 'Calendar'
  form.color = '#3757e8'
  form.sort_order = 0
  form.is_active = true
}

function openCreate() {
  editingId.value = null
  resetForm()
  const maxOrder = Math.max(0, ...categories.value.map((item) => item.sort_order || 0))
  form.sort_order = maxOrder + 10
  dialogVisible.value = true
}

function openCategoryEdit(row: Category) {
  editingId.value = row.id
  form.name = row.name
  form.slug = row.slug
  form.icon = row.icon || 'Calendar'
  form.color = row.color || '#3757e8'
  form.sort_order = row.sort_order ?? 0
  form.is_active = row.is_active !== false
  dialogVisible.value = true
}

function openTagEdit(row: Tag) {
  editingId.value = row.id
  form.name = row.name
  form.slug = ''
  form.icon = 'Calendar'
  form.color = row.color || '#3757e8'
  form.sort_order = 0
  form.is_active = row.is_active !== false
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (activeTab.value === 'category') {
      const payload = {
        name: form.name.trim(),
        slug: form.slug.trim(),
        icon: form.icon,
        color: form.color,
        sort_order: Number(form.sort_order) || 0,
        is_active: form.is_active,
      }
      if (editingId.value) {
        await updateCategory(editingId.value, payload)
      } else {
        await createCategory(payload)
      }
    } else {
      const payload = {
        name: form.name.trim(),
        color: form.color,
        is_active: form.is_active,
      }
      if (editingId.value) {
        await updateTag(editingId.value, payload)
      } else {
        await createTag(payload)
      }
    }
    ElMessage.success(editingId.value ? '已保存修改' : '新增成功')
    dialogVisible.value = false
    editingId.value = null
    await load()
  } catch {
    // 接口错误由拦截器提示
  } finally {
    saving.value = false
  }
}

async function toggleCategory(row: Category, value: boolean) {
  try {
    await updateCategory(row.id, { is_active: value })
    row.is_active = value
    ElMessage.success(value ? `已启用「${row.name}」` : `已停用「${row.name}」`)
  } catch {
    // 失败时保持原状态，接口错误由拦截器提示
  }
}

async function toggleTag(row: Tag, value: boolean) {
  try {
    await updateTag(row.id, { is_active: value })
    row.is_active = value
    ElMessage.success(value ? `已启用「${row.name}」` : `已停用「${row.name}」`)
  } catch {
    // 失败时保持原状态
  }
}

onMounted(load)
</script>

<template>
  <div class="dict-page" v-loading="loading">
    <div class="page-head">
      <div>
        <span class="eyebrow">Platform dictionary</span>
        <h1>字典管理</h1>
        <p>维护活动分类与公共标签，控制它们在发布表单与筛选区的可用性。</p>
      </div>
      <el-button type="primary" round :icon="Plus" @click="openCreate">
        {{ activeTab === 'category' ? '新增分类' : '新增标签' }}
      </el-button>
    </div>

    <div class="dict-summary">
      <div class="dict-summary__item">
        <span>活动分类</span>
        <strong>{{ categories.length }}</strong>
        <small>{{ activeCategoryCount }} 个启用中</small>
      </div>
      <div class="dict-summary__item">
        <span>活动标签</span>
        <strong>{{ tags.length }}</strong>
        <small>{{ activeTagCount }} 个启用中</small>
      </div>
    </div>

    <div class="dict-tabs">
      <button
        type="button"
        class="dict-tab"
        :class="{ 'is-active': activeTab === 'category' }"
        @click="activeTab = 'category'"
      >
        活动分类
        <span>{{ categories.length }}</span>
      </button>
      <button
        type="button"
        class="dict-tab"
        :class="{ 'is-active': activeTab === 'tag' }"
        @click="activeTab = 'tag'"
      >
        活动标签
        <span>{{ tags.length }}</span>
      </button>
    </div>

    <div v-show="activeTab === 'category'" class="table-card">
      <el-table v-if="categories.length" :data="categories" style="width: 100%">
        <el-table-column label="分类" min-width="220">
          <template #default="{ row }">
            <div class="cat-cell">
              <span class="cat-cell__icon" :style="{ background: row.color || '#3757e8' }">
                <el-icon><component :is="iconMap[row.icon] ?? Calendar" /></el-icon>
              </span>
              <div>
                <strong>{{ row.name }}</strong>
                <span>{{ row.slug }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="排序" prop="sort_order" width="90" align="center" />
        <el-table-column label="更新时间" min-width="150">
          <template #default="{ row }">
            <span class="table-muted">{{ row.updated_at ? new Date(row.updated_at).toLocaleString('zh-CN') : '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active !== false"
              size="small"
              @change="(value: boolean | string | number) => toggleCategory(row, Boolean(value))"
            />
            <span class="switch-label">{{ row.is_active !== false ? '启用' : '停用' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" round :icon="EditPen" @click="openCategoryEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else-if="!loading" title="还没有活动分类" description="新增分类后，主办方即可创建活动。">
        <el-button type="primary" round :icon="Plus" @click="openCreate">新增分类</el-button>
      </EmptyState>
    </div>

    <div v-show="activeTab === 'tag'" class="table-card">
      <el-table v-if="tags.length" :data="tags" style="width: 100%">
        <el-table-column label="标签" min-width="220">
          <template #default="{ row }">
            <span class="tag-preview" :style="{ color: row.color, borderColor: row.color }">
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="颜色值" prop="color" min-width="120" />
        <el-table-column label="创建时间" min-width="150">
          <template #default="{ row }">
            <span class="table-muted">{{ row.created_at ? new Date(row.created_at).toLocaleString('zh-CN') : '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active !== false"
              size="small"
              @change="(value: boolean | string | number) => toggleTag(row, Boolean(value))"
            />
            <span class="switch-label">{{ row.is_active !== false ? '启用' : '停用' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" round :icon="EditPen" @click="openTagEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else-if="!loading" title="还没有活动标签" description="标签用于表达「志愿时长」「限量名额」等活动属性。">
        <el-button type="primary" round :icon="Plus" @click="openCreate">新增标签</el-button>
      </EmptyState>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="min(540px, 94vw)"
      :close-on-click-modal="false"
      @closed="editingId = null"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
        <el-form-item :label="activeTab === 'category' ? '分类名称' : '标签名称'" prop="name">
          <el-input v-model="form.name" maxlength="50" placeholder="例如：讲座学术" @blur="suggestSlug" />
        </el-form-item>
        <el-form-item v-if="activeTab === 'category'" label="分类标识（slug）" prop="slug">
          <el-input v-model="form.slug" maxlength="50" placeholder="英文小写，用于筛选参数，如 lecture" />
        </el-form-item>
        <el-form-item v-if="activeTab === 'category'" label="展示图标">
          <div class="icon-picker">
            <button
              v-for="icon in iconOptions"
              :key="icon"
              type="button"
              class="icon-choice"
              :class="{ 'is-active': form.icon === icon }"
              :title="icon"
              @click="form.icon = icon"
            >
              <el-icon><component :is="iconMap[icon]" /></el-icon>
            </button>
          </div>
        </el-form-item>
        <el-form-item label="主题色" prop="color">
          <div class="color-row">
            <el-color-picker v-model="form.color" :predefine="colorPresets" />
            <el-input v-model="form.color" maxlength="20" class="color-input" />
            <span class="color-preview" :style="{ background: form.color }"></span>
          </div>
        </el-form-item>
        <el-form-item v-if="activeTab === 'category'" label="排序值">
          <el-input-number v-model="form.sort_order" :min="0" :max="9999" controls-position="right" />
          <span class="form-hint">数值越小，在分类栏中越靠前</span>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="停用" />
          <span class="form-hint">停用后不再出现在活动筛选与发布表单中</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" :icon="Check" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.dict-page {
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

.dict-summary {
  display: flex;
  gap: 16px;
}

.dict-summary__item {
  display: flex;
  flex-direction: column;
  min-width: 180px;
  padding: 16px 20px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.dict-summary__item span {
  color: var(--ch-muted);
  font-size: 12px;
}

.dict-summary__item strong {
  margin-top: 2px;
  font-size: 24px;
  letter-spacing: -0.02em;
}

.dict-summary__item small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.dict-tabs {
  display: inline-flex;
  gap: 4px;
  align-self: flex-start;
  padding: 4px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--ch-border);
}

.dict-tab {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 16px;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: var(--ch-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
}

.dict-tab span {
  padding: 1px 7px;
  border-radius: 999px;
  background: rgba(16, 26, 51, 0.06);
  font-size: 11px;
}

.dict-tab.is-active {
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
}

.dict-tab.is-active span {
  background: #fff;
  color: var(--ch-primary);
}

.cat-cell {
  display: flex;
  align-items: center;
  gap: 11px;
}

.cat-cell__icon {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 11px;
  color: #fff;
  font-size: 17px;
}

.cat-cell div {
  display: flex;
  flex-direction: column;
}

.cat-cell strong {
  font-size: 13px;
  font-weight: 650;
}

.cat-cell span {
  color: var(--ch-muted-light);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 11px;
}

.tag-preview {
  display: inline-flex;
  align-items: center;
  padding: 3px 11px;
  border: 1px solid;
  border-radius: 999px;
  background: #fff;
  font-size: 12px;
  font-weight: 600;
}

.table-muted {
  color: var(--ch-muted);
  font-size: 12px;
}

.switch-label {
  margin-left: 8px;
  color: var(--ch-muted-light);
  font-size: 11px;
}

.icon-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.icon-choice {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--ch-border);
  border-radius: 11px;
  background: #fff;
  color: var(--ch-muted);
  font-size: 17px;
  cursor: pointer;
  transition: all 0.16s ease;
}

.icon-choice:hover {
  border-color: var(--ch-primary-light, #6b83f0);
  color: var(--ch-primary);
}

.icon-choice.is-active {
  border-color: var(--ch-primary);
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  box-shadow: 0 0 0 3px rgba(55, 87, 232, 0.12);
}

.color-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.color-input {
  max-width: 160px;
}

.color-preview {
  flex: 1;
  height: 26px;
  border-radius: 8px;
  border: 1px solid var(--ch-border);
}

.form-hint {
  margin-left: 12px;
  color: var(--ch-muted-light);
  font-size: 11px;
}

@media (max-width: 760px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .dict-summary {
    flex-wrap: wrap;
  }

  .dict-summary__item {
    flex: 1 1 45%;
    min-width: 0;
  }
}
</style>
