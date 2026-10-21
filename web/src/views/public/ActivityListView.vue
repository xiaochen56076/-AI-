<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'

import ActivityCard from '@/components/ActivityCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { listActivities, listCategories, listTags } from '@/api/activities'
import type { ActivityBrief, ActivityQuery, Category, Paginated, Tag } from '@/types'

type Scope = 'upcoming' | 'past' | 'all'
type Sort = 'start_time' | 'deadline' | 'hot' | 'latest'

const route = useRoute()
const router = useRouter()

const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])
const pageData = ref<Paginated<ActivityBrief>>({
  total: 0,
  page: 1,
  page_size: 9,
  results: [],
})
const loading = ref(true)
const keyword = ref('')
const dateRange = ref<[string, string] | null>(null)

const scope = ref<Scope>('upcoming')
const sort = ref<Sort>('start_time')
const category = ref('')
const tag = ref('')

const scopes: { value: Scope; label: string }[] = [
  { value: 'upcoming', label: '即将开始' },
  { value: 'all', label: '全部活动' },
  { value: 'past', label: '往期回顾' },
]

const sortOptions: { value: Sort; label: string }[] = [
  { value: 'start_time', label: '最近开始' },
  { value: 'deadline', label: '即将截止' },
  { value: 'hot', label: '最受欢迎' },
  { value: 'latest', label: '最新发布' },
]

const currentCategory = computed(() =>
  categories.value.find((item) => item.slug === category.value),
)
const currentTag = computed(() => tags.value.find((item) => String(item.id) === tag.value))
const hasFilters = computed(
  () =>
    Boolean(keyword.value.trim()) ||
    Boolean(category.value) ||
    Boolean(tag.value) ||
    Boolean(dateRange.value),
)

function queryString(key: string) {
  const value = route.query[key]
  return typeof value === 'string' ? value : ''
}

function syncFromRoute() {
  keyword.value = queryString('keyword')
  const scopeValue = queryString('scope')
  scope.value = scopeValue === 'past' || scopeValue === 'all' ? scopeValue : 'upcoming'
  const sortValue = queryString('sort')
  sort.value = sortOptions.some((item) => item.value === sortValue)
    ? (sortValue as Sort)
    : 'start_time'
  category.value = queryString('category')
  tag.value = queryString('tag')
  const from = queryString('date_from')
  const to = queryString('date_to')
  dateRange.value = from && to ? [from, to] : null
}

async function fetchActivities() {
  loading.value = true
  const params: ActivityQuery = {
    scope: scope.value,
    sort: sort.value,
    page_size: 9,
  }
  if (keyword.value.trim()) params.keyword = keyword.value.trim()
  if (category.value) params.category = category.value
  if (tag.value) params.tag = tag.value
  if (dateRange.value) {
    params.date_from = dateRange.value[0]
    params.date_to = dateRange.value[1]
  }
  const page = Number(queryString('page'))
  params.page = Number.isInteger(page) && page > 0 ? page : 1

  try {
    pageData.value = await listActivities(params)
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    loading.value = false
  }
}

function patchQuery(patch: Record<string, string | number | undefined>, keepPage = false) {
  const query: Record<string, string> = {}
  for (const [key, value] of Object.entries(route.query)) {
    if (typeof value === 'string') query[key] = value
  }
  for (const [key, value] of Object.entries(patch)) {
    if (value === undefined || value === '') delete query[key]
    else query[key] = String(value)
  }
  if (!keepPage) delete query.page
  router.push({ name: 'activities', query })
}

function submitSearch() {
  patchQuery({ keyword: keyword.value.trim() || undefined })
}

function changeScope(value: Scope) {
  patchQuery({ scope: value === 'upcoming' ? undefined : value })
}

function changeSort(value: Sort) {
  patchQuery({ sort: value === 'start_time' ? undefined : value })
}

function changeCategory(slug: string) {
  patchQuery({ category: slug || undefined })
}

function changeTag(value: string) {
  patchQuery({ tag: value || undefined })
}

function changeDate(value: [string, string] | null) {
  patchQuery({
    date_from: value?.[0],
    date_to: value?.[1],
  })
}

function clearFilters() {
  keyword.value = ''
  router.push({ name: 'activities', query: scope.value === 'upcoming' ? {} : { scope: scope.value } })
}

function changePage(page: number) {
  patchQuery({ page }, true)
}

watch(
  () => route.query,
  async () => {
    syncFromRoute()
    await fetchActivities()
  },
  { immediate: true, deep: true },
)

onMounted(async () => {
  try {
    const [categoryList, tagList] = await Promise.all([listCategories(), listTags()])
    categories.value = categoryList
    tags.value = tagList
  } catch {
    // 分类加载失败时仍可浏览活动
  }
})
</script>

<template>
  <div class="activities-page">
    <section class="page-hero activities-hero">
      <div class="page-container">
        <span class="eyebrow">Activity discovery</span>
        <h1>活动广场</h1>
        <p>按兴趣、分类与时间探索校园活动，找到属于你的下一场精彩。</p>

        <div class="hero-search-bar">
          <el-input
            v-model="keyword"
            size="large"
            placeholder="搜索活动名称、地点或主办社团"
            :prefix-icon="Search"
            clearable
            @keyup.enter="submitSearch"
            @clear="submitSearch"
          />
          <el-button type="primary" size="large" class="ch-button-gradient" @click="submitSearch">
            搜索
          </el-button>
        </div>
      </div>
    </section>

    <section class="page-container page-block">
      <div class="filter-panel surface">
        <div class="scope-row">
          <div class="scope-tabs">
            <button
              v-for="item in scopes"
              :key="item.value"
              type="button"
              class="scope-tab"
              :class="{ 'is-active': scope === item.value }"
              @click="changeScope(item.value)"
            >
              {{ item.label }}
            </button>
          </div>
          <div class="scope-tools">
            <el-select
              :model-value="sort"
              class="sort-select"
              @update:model-value="changeSort"
            >
              <el-option
                v-for="item in sortOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              value-format="YYYY-MM-DD"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              class="date-range"
              @change="changeDate"
            />
          </div>
        </div>

        <div class="category-row">
          <button
            type="button"
            class="category-chip"
            :class="{ 'is-active': !category }"
            @click="changeCategory('')"
          >
            全部分类
          </button>
          <button
            v-for="item in categories"
            :key="item.id"
            type="button"
            class="category-chip"
            :class="{ 'is-active': category === item.slug }"
            :style="{ '--chip-color': item.color }"
            @click="changeCategory(item.slug)"
          >
            <span class="category-chip__dot"></span>
            {{ item.name }}
          </button>

          <el-select
            v-if="tags.length"
            :model-value="tag"
            placeholder="活动标签"
            clearable
            class="tag-select"
            @update:model-value="changeTag"
          >
            <el-option
              v-for="item in tags"
              :key="item.id"
              :label="item.name"
              :value="String(item.id)"
            />
          </el-select>
        </div>
      </div>

      <div class="result-head">
        <div>
          <strong>{{ pageData.total }}</strong>
          <span>场活动找到</span>
          <template v-if="currentCategory">
            <span class="result-sep">·</span>
            <span>{{ currentCategory.name }}</span>
          </template>
          <template v-if="currentTag">
            <span class="result-sep">·</span>
            <span>{{ currentTag.name }}</span>
          </template>
          <template v-if="dateRange">
            <span class="result-sep">·</span>
            <span>{{ dateRange[0] }} 至 {{ dateRange[1] }}</span>
          </template>
        </div>
        <button v-if="hasFilters" type="button" class="clear-button" @click="clearFilters">
          <el-icon><Close /></el-icon>
          清除筛选
        </button>
      </div>

      <div v-if="loading" class="card-grid">
        <div v-for="item in 6" :key="item" class="skeleton-card skeleton-block"></div>
      </div>

      <div v-else-if="pageData.results.length" class="card-grid">
        <ActivityCard
          v-for="activity in pageData.results"
          :key="activity.id"
          :activity="activity"
        />
      </div>

      <EmptyState
        v-else
        title="没有找到匹配的活动"
        description="试试更换关键词或放宽筛选条件，更多活动正在持续上新。"
      >
        <el-button v-if="hasFilters" round @click="clearFilters">清除筛选条件</el-button>
        <RouterLink to="/">
          <el-button type="primary" round>返回首页</el-button>
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
.activities-hero {
  padding-bottom: 48px;
}

.hero-search-bar {
  display: flex;
  gap: 10px;
  max-width: 640px;
  margin-top: 26px;
  padding: 7px;
  border: 1px solid var(--ch-border);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 16px 40px rgba(20, 34, 79, 0.08);
}

.hero-search-bar :deep(.el-input__wrapper) {
  box-shadow: none;
  background: transparent;
}

.hero-search-bar :deep(.el-input__inner) {
  height: 40px;
}

.hero-search-bar .el-button {
  border-radius: 11px;
}

.filter-panel {
  padding: 18px 20px;
}

.scope-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f3fa;
}

.scope-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: 11px;
  background: #f4f6fb;
}

.scope-tab {
  padding: 7px 16px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--ch-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.scope-tab:hover {
  color: var(--ch-ink);
}

.scope-tab.is-active {
  background: #fff;
  color: var(--ch-primary);
  box-shadow: 0 2px 8px rgba(16, 26, 51, 0.08);
}

.scope-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sort-select {
  width: 130px;
}

.date-range {
  width: 250px;
}

.category-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding-top: 16px;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 13px;
  border: 1px solid var(--ch-border);
  border-radius: 999px;
  background: #fff;
  color: var(--ch-muted);
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.category-chip:hover {
  border-color: var(--ch-border-strong);
  color: var(--ch-ink);
}

.category-chip.is-active {
  border-color: transparent;
  background: var(--ch-ink);
  color: #fff;
}

.category-chip__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--chip-color, currentColor);
}

.category-chip.is-active .category-chip__dot {
  background: #fff;
}

.tag-select {
  width: 130px;
  margin-left: auto;
}

.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 26px 2px 18px;
  color: var(--ch-muted);
  font-size: 13px;
}

.result-head strong {
  margin-right: 5px;
  color: var(--ch-ink);
  font-size: 20px;
  font-weight: 750;
  letter-spacing: -0.02em;
}

.result-sep {
  margin: 0 7px;
  color: var(--ch-border-strong);
}

.clear-button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--ch-muted);
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-button:hover {
  background: #fff;
  color: var(--ch-danger);
}

.skeleton-card {
  height: 390px;
}

@media (max-width: 820px) {
  .scope-row {
    flex-direction: column;
    align-items: stretch;
  }

  .scope-tools {
    flex-wrap: wrap;
  }

  .sort-select {
    flex: 1;
    width: auto;
  }

  .date-range {
    flex: 2;
    width: auto;
  }

  .tag-select {
    width: 120px;
  }
}

@media (max-width: 560px) {
  .hero-search-bar {
    flex-direction: column;
    padding: 10px;
  }

  .scope-tabs {
    width: 100%;
  }

  .scope-tab {
    flex: 1;
    padding: 7px 8px;
  }

  .date-range {
    flex-basis: 100%;
  }

  .tag-select {
    margin-left: 0;
  }

  .result-head {
    flex-wrap: wrap;
  }
}
</style>
