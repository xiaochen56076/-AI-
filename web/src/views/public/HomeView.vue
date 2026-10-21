<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'

import ActivityCard from '@/components/ActivityCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { listActivities, listCategories } from '@/api/activities'
import type { ActivityBrief, Category } from '@/types'
import {
  categoryGradient,
  countdownText,
  formatMonthDay,
  formatNumber,
  formatTimeRange,
  formatWeekday,
} from '@/utils/format'

const router = useRouter()

const categories = ref<Category[]>([])
const upcoming = ref<ActivityBrief[]>([])
const hot = ref<ActivityBrief[]>([])
const upcomingTotal = ref(0)
const loading = ref(true)
const keyword = ref('')

const featured = computed(() => upcoming.value[0] ?? null)
const featuredPercent = computed(() => {
  if (!featured.value?.capacity) return 0
  return Math.min(100, Math.round((featured.value.signup_count / featured.value.capacity) * 100))
})

async function load() {
  loading.value = true
  try {
    const [categoryList, upcomingPage, hotPage] = await Promise.all([
      listCategories(),
      listActivities({ scope: 'upcoming', sort: 'start_time', page_size: 6 }),
      listActivities({ scope: 'upcoming', sort: 'hot', page_size: 4 }),
    ])
    categories.value = categoryList
    upcoming.value = upcomingPage.results
    upcomingTotal.value = upcomingPage.total
    hot.value = hotPage.results
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    loading.value = false
  }
}

function search() {
  router.push({
    name: 'activities',
    query: keyword.value.trim() ? { keyword: keyword.value.trim() } : {},
  })
}

function openCategory(category: Category) {
  router.push({ name: 'activities', query: { category: category.slug } })
}

onMounted(load)
</script>

<template>
  <div class="home">
    <section class="home-hero">
      <div class="hero-orb hero-orb--one"></div>
      <div class="hero-orb hero-orb--two"></div>
      <div class="page-container hero-grid">
        <div class="hero-copy rise-in">
          <span class="hero-eyebrow">
            <span class="hero-eyebrow__dot"></span>
            CAMPUS ACTIVITY HUB · 2026
          </span>
          <h1>
            发现校园里，<br />
            <span class="gradient-text">正在发生</span>的精彩
          </h1>
          <p class="hero-description">
            讲座、演出、比赛、志愿……一站式发现并参与校园活动。在线报名、满员候补、现场扫码签到，让每一次参与都轻松顺畅。
          </p>

          <div class="hero-search">
            <el-input
              v-model="keyword"
              size="large"
              placeholder="搜索活动名称、地点或主办社团"
              :prefix-icon="Search"
              clearable
              @keyup.enter="search"
            />
            <el-button type="primary" size="large" class="ch-button-gradient" @click="search">
              搜索活动
            </el-button>
          </div>

          <div class="quick-categories">
            <button
              v-for="category in categories.slice(0, 6)"
              :key="category.id"
              type="button"
              class="quick-chip"
              @click="openCategory(category)"
            >
              <span class="quick-chip__dot" :style="{ background: category.color }"></span>
              {{ category.name }}
            </button>
          </div>

          <div class="hero-stats">
            <div>
              <strong>{{ formatNumber(upcomingTotal) }}</strong>
              <span>场近期活动</span>
            </div>
            <div class="hero-stats__divider"></div>
            <div>
              <strong>{{ categories.length || 6 }}</strong>
              <span>个活动分类</span>
            </div>
            <div class="hero-stats__divider"></div>
            <div>
              <strong>30s</strong>
              <span>动态签到码刷新</span>
            </div>
          </div>
        </div>

        <div class="hero-visual rise-in">
          <div v-if="featured" class="featured-card">
            <div class="featured-card__top">
              <span class="featured-label">
                <span class="pulse-dot"></span>
                下一场活动
              </span>
              <span class="status-pill" :class="featured.status === 2 ? 'is-published' : 'is-ended'">
                {{ featured.status_text }}
              </span>
            </div>

            <div class="featured-date">
              <strong>{{ formatMonthDay(featured.start_time).split('月')[1]?.replace('日', '') }}</strong>
              <div>
                <span>{{ formatMonthDay(featured.start_time).split('月')[0] }}月</span>
                <small>{{ formatWeekday(featured.start_time) }} · {{ formatTimeRange(featured.start_time, featured.end_time).split(' - ')[1] }}</small>
              </div>
            </div>

            <h3>{{ featured.title }}</h3>
            <p>{{ featured.summary || '一场不容错过的校园活动，期待你的参与。' }}</p>

            <div class="featured-meta">
              <span>
                <el-icon><Location /></el-icon>
                {{ featured.location }}
              </span>
              <span>
                <el-icon><User /></el-icon>
                {{ featured.organizer?.display_name }}
              </span>
            </div>

            <div class="featured-capacity">
              <div class="featured-capacity__row">
                <span>报名进度</span>
                <strong>{{ featured.signup_count }} / {{ featured.capacity }}</strong>
              </div>
              <div class="featured-capacity__bar">
                <span :style="{ width: `${featuredPercent}%`, background: featured.category?.color || '#3757e8' }"></span>
              </div>
            </div>

            <div class="featured-footer">
              <span class="featured-countdown">
                <el-icon><Timer /></el-icon>
                距开始 {{ countdownText(featured.start_time) }}
              </span>
              <RouterLink :to="`/activities/${featured.id}`" class="featured-link">
                查看详情
                <el-icon><ArrowRight /></el-icon>
              </RouterLink>
            </div>

            <div class="featured-decoration" :style="{ background: categoryGradient(featured.category?.color) }"></div>
          </div>

          <div v-else class="featured-empty skeleton-block"></div>

          <div class="floating-note">
            <span class="floating-note__icon"><el-icon><CircleCheckFilled /></el-icon></span>
            <div>
              <strong>候补自动转正</strong>
              <small>有人取消名额，系统自动通知下一位</small>
            </div>
          </div>
        </div>
      </div>

      <div class="hero-marquee">
        <div class="page-container hero-marquee__inner">
          <span>{{ categories.length || 6 }} 大活动分类</span>
          <span class="dot-separator"></span>
          <span>实时候补队列</span>
          <span class="dot-separator"></span>
          <span>动态二维码签到</span>
          <span class="dot-separator"></span>
          <span>活动数据洞察</span>
          <span class="dot-separator"></span>
          <span>全流程消息通知</span>
        </div>
      </div>
    </section>

    <section class="home-section page-container">
      <div class="section-heading">
        <div>
          <span class="eyebrow">Explore by interest</span>
          <h2>按兴趣，找到你的主场</h2>
          <p>从学术讲座到体育竞技，每一种热爱都值得被看见。</p>
        </div>
      </div>

      <div class="category-grid">
        <button
          v-for="(category, index) in categories"
          :key="category.id"
          type="button"
          class="category-card"
          :style="{ '--cat-color': category.color, '--delay': `${index * 40}ms` }"
          @click="openCategory(category)"
        >
          <span class="category-card__icon">
            <el-icon><component :is="category.icon || 'Calendar'" /></el-icon>
          </span>
          <div class="category-card__text">
            <strong>{{ category.name }}</strong>
            <span>查看相关活动</span>
          </div>
          <span class="category-card__arrow"><el-icon><ArrowRight /></el-icon></span>
          <span class="category-card__glow"></span>
        </button>
      </div>
    </section>

    <section class="home-section page-container">
      <div class="section-heading">
        <div>
          <span class="eyebrow">Upcoming</span>
          <h2>近期活动</h2>
          <p>挑一场感兴趣的活动，把日程填满。</p>
        </div>
        <RouterLink to="/activities" class="text-link">
          查看全部活动
          <el-icon><ArrowRight /></el-icon>
        </RouterLink>
      </div>

      <div v-if="loading" class="card-grid">
        <div v-for="item in 3" :key="item" class="skeleton-card skeleton-block"></div>
      </div>
      <div v-else-if="upcoming.length" class="card-grid">
        <ActivityCard v-for="activity in upcoming" :key="activity.id" :activity="activity" />
      </div>
      <EmptyState
        v-else
        title="暂无近期活动"
        description="新的活动正在筹备中，先去活动广场看看往期内容吧。"
      >
        <RouterLink to="/activities?scope=all">
          <el-button round>浏览全部活动</el-button>
        </RouterLink>
      </EmptyState>
    </section>

    <section class="home-section page-container">
      <div class="home-split">
        <div class="hot-panel surface">
          <div class="hot-panel__head">
            <div>
              <span class="eyebrow">Trending</span>
              <h2>本周热门</h2>
            </div>
            <span class="hot-panel__hint">按浏览量排序</span>
          </div>

          <div v-if="hot.length" class="hot-list">
            <RouterLink
              v-for="(activity, index) in hot"
              :key="activity.id"
              :to="`/activities/${activity.id}`"
              class="hot-item"
            >
              <span class="hot-rank" :class="{ 'is-top': index < 3 }">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="hot-item__body">
                <div class="hot-item__meta">
                  <span :style="{ color: activity.category?.color }">{{ activity.category?.name }}</span>
                  <span class="dot-separator"></span>
                  <span>{{ formatMonthDay(activity.start_time) }}</span>
                </div>
                <strong>{{ activity.title }}</strong>
                <span class="hot-item__sub">{{ activity.location }} · {{ activity.signup_count }} 人已报名</span>
              </div>
              <el-icon class="hot-item__arrow"><ArrowRight /></el-icon>
            </RouterLink>
          </div>
          <EmptyState v-else title="暂无热门活动" description="活动热度正在积累，稍后再来看看。" />
        </div>

        <div class="organizer-cta">
          <span class="organizer-cta__eyebrow">FOR ORGANIZERS</span>
          <h2>让你的活动，<br />被更多人看见。</h2>
          <p>
            从发布、审核、报名管理到现场签到与数据复盘，CampusHub 为主办方准备了完整的活动运营工具。
          </p>
          <ul class="organizer-cta__list">
            <li><el-icon><Select /></el-icon> 灵活配置报名时间与候补规则</li>
            <li><el-icon><Select /></el-icon> 实时查看名单并导出 CSV</li>
            <li><el-icon><Select /></el-icon> 动态二维码签到，防代签更安心</li>
            <li><el-icon><Select /></el-icon> 报名、签到与学院分布一目了然</li>
          </ul>
          <div class="organizer-cta__actions">
            <RouterLink to="/register">
              <el-button type="primary" size="large" round>成为主办方</el-button>
            </RouterLink>
            <RouterLink to="/login">
              <el-button size="large" round plain class="organizer-cta__ghost">进入工作台</el-button>
            </RouterLink>
          </div>
          <span class="organizer-cta__orb"></span>
          <span class="organizer-cta__grid"></span>
        </div>
      </div>
    </section>

    <section class="home-section page-container">
      <div class="step-strip">
        <div class="step-item">
          <span class="step-index">01</span>
          <div>
            <strong>发现</strong>
            <p>按分类、时间与热度筛选，快速找到心仪活动。</p>
          </div>
        </div>
        <div class="step-line"></div>
        <div class="step-item">
          <span class="step-index">02</span>
          <div>
            <strong>报名</strong>
            <p>在线锁定名额，满员时自动进入候补队列。</p>
          </div>
        </div>
        <div class="step-line"></div>
        <div class="step-item">
          <span class="step-index">03</span>
          <div>
            <strong>参与</strong>
            <p>现场扫码签到，活动结束后查看个人参与记录。</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  overflow: hidden;
}

.home-hero {
  position: relative;
  padding: 72px 0 0;
  background:
    radial-gradient(1000px 520px at 8% -8%, rgba(55, 87, 232, 0.16), transparent 62%),
    radial-gradient(760px 420px at 96% 12%, rgba(255, 122, 89, 0.13), transparent 60%),
    linear-gradient(180deg, #f8faff 0%, #f3f6fd 100%);
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(380px, 0.92fr);
  gap: 54px;
  align-items: center;
  padding-bottom: 64px;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 7px 13px;
  border: 1px solid rgba(55, 87, 232, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: var(--ch-primary);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.hero-eyebrow__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ch-primary);
  box-shadow: 0 0 0 4px rgba(55, 87, 232, 0.12);
}

.hero-copy h1 {
  margin-top: 22px;
  font-size: clamp(42px, 5.4vw, 66px);
  line-height: 1.08;
  letter-spacing: -0.045em;
  font-weight: 800;
}

.gradient-text {
  background: linear-gradient(100deg, #3757e8, #7a5af8 52%, #ff7a59);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-description {
  max-width: 560px;
  margin-top: 20px;
  color: var(--ch-muted);
  font-size: 15.5px;
  line-height: 1.8;
}

.hero-search {
  display: flex;
  gap: 10px;
  max-width: 560px;
  margin-top: 28px;
  padding: 7px;
  border: 1px solid var(--ch-border);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 16px 40px rgba(20, 34, 79, 0.08);
}

.hero-search :deep(.el-input__wrapper) {
  box-shadow: none;
  background: transparent;
  font-size: 14px;
}

.hero-search :deep(.el-input__inner) {
  height: 42px;
}

.hero-search .el-button {
  flex: 0 0 auto;
  border-radius: 11px;
}

.quick-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}

.quick-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 12px;
  border: 1px solid var(--ch-border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: var(--ch-ink-soft);
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-chip:hover {
  border-color: rgba(55, 87, 232, 0.3);
  background: #fff;
  color: var(--ch-primary);
  transform: translateY(-1px);
}

.quick-chip__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 26px;
  margin-top: 38px;
}

.hero-stats div:not(.hero-stats__divider) {
  display: flex;
  flex-direction: column;
}

.hero-stats strong {
  font-size: 25px;
  font-weight: 760;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}

.hero-stats span {
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.hero-stats__divider {
  width: 1px;
  height: 30px;
  background: var(--ch-border);
}

.hero-visual {
  position: relative;
}

.featured-card {
  position: relative;
  padding: 26px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 30px 70px rgba(20, 34, 79, 0.14);
  backdrop-filter: blur(20px);
}

.featured-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.featured-label {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--ch-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.pulse-dot {
  position: relative;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #0f9f6e;
}

.pulse-dot::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 1px solid rgba(15, 159, 110, 0.4);
  animation: pulse 1.8s ease-out infinite;
}

@keyframes pulse {
  from {
    transform: scale(0.7);
    opacity: 1;
  }
  to {
    transform: scale(1.6);
    opacity: 0;
  }
}

.featured-date {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 22px;
}

.featured-date strong {
  font-size: 54px;
  line-height: 0.9;
  letter-spacing: -0.06em;
  font-weight: 800;
  color: var(--ch-ink);
}

.featured-date > div {
  display: flex;
  flex-direction: column;
  padding-left: 12px;
  border-left: 1px solid var(--ch-border);
  line-height: 1.45;
}

.featured-date span {
  color: var(--ch-ink-soft);
  font-size: 13px;
  font-weight: 700;
}

.featured-date small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.featured-card h3 {
  margin-top: 16px;
  font-size: 21px;
  line-height: 1.4;
  letter-spacing: -0.02em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.featured-card > p {
  margin-top: 8px;
  color: var(--ch-muted);
  font-size: 13px;
  line-height: 1.65;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.featured-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 18px;
  color: var(--ch-muted);
  font-size: 12px;
}

.featured-meta span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.featured-meta .el-icon {
  color: var(--ch-muted-light);
}

.featured-capacity {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px dashed var(--ch-border);
}

.featured-capacity__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--ch-muted);
  font-size: 11.5px;
}

.featured-capacity__row strong {
  color: var(--ch-ink-soft);
  font-variant-numeric: tabular-nums;
}

.featured-capacity__bar {
  height: 6px;
  margin-top: 8px;
  border-radius: 999px;
  background: #edf0f8;
  overflow: hidden;
}

.featured-capacity__bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.featured-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 20px;
}

.featured-countdown {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.featured-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ch-primary);
  font-size: 13px;
  font-weight: 700;
}

.featured-decoration {
  position: absolute;
  right: -60px;
  bottom: -70px;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  opacity: 0.12;
  filter: blur(10px);
  pointer-events: none;
}

.featured-empty {
  height: 430px;
}

.floating-note {
  position: absolute;
  left: -26px;
  bottom: -22px;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 13px 16px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 40px rgba(20, 34, 79, 0.12);
  backdrop-filter: blur(12px);
  animation: float-soft 6s ease-in-out infinite;
}

.floating-note__icon {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #e8f8f2;
  color: #0f9f6e;
  font-size: 18px;
}

.floating-note div {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.floating-note strong {
  font-size: 12px;
}

.floating-note small {
  color: var(--ch-muted-light);
  font-size: 10.5px;
}

.hero-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.hero-orb--one {
  width: 540px;
  height: 540px;
  top: -210px;
  right: -140px;
  background: radial-gradient(circle at 40% 40%, rgba(122, 144, 255, 0.16), transparent 70%);
}

.hero-orb--two {
  width: 380px;
  height: 380px;
  bottom: -160px;
  left: -130px;
  background: radial-gradient(circle at 40% 40%, rgba(255, 146, 120, 0.12), transparent 70%);
}

.hero-marquee {
  border-top: 1px solid rgba(55, 87, 232, 0.08);
  background: rgba(255, 255, 255, 0.4);
}

.hero-marquee__inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  height: 56px;
  color: var(--ch-muted-light);
  font-size: 12px;
  letter-spacing: 0.04em;
}

.home-section {
  padding-top: 78px;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.category-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  overflow: hidden;
  border: 1px solid var(--ch-border);
  border-radius: 16px;
  background: #fff;
  text-align: left;
  cursor: pointer;
  transition: all 0.25s ease;
  animation: rise-in 0.5s ease both;
  animation-delay: var(--delay);
}

.category-card:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--cat-color) 35%, white);
  box-shadow: 0 16px 36px rgba(20, 34, 79, 0.09);
}

.category-card__icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--cat-color) 12%, white);
  color: var(--cat-color);
  font-size: 23px;
}

.category-card__text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.4;
}

.category-card__text strong {
  font-size: 14.5px;
  font-weight: 700;
}

.category-card__text span {
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.category-card__arrow {
  margin-left: auto;
  color: var(--cat-color);
  font-size: 15px;
  opacity: 0;
  transform: translateX(-5px);
  transition: all 0.2s ease;
}

.category-card:hover .category-card__arrow {
  opacity: 1;
  transform: translateX(0);
}

.category-card__glow {
  position: absolute;
  right: -40px;
  top: -40px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--cat-color);
  opacity: 0.05;
}

.skeleton-card {
  height: 380px;
}

.home-split {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.85fr);
  gap: 24px;
  align-items: stretch;
}

.hot-panel {
  padding: 28px;
}

.hot-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.hot-panel__head h2 {
  margin-top: 8px;
  font-size: 26px;
  letter-spacing: -0.02em;
}

.hot-panel__hint {
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.hot-list {
  display: flex;
  flex-direction: column;
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 8px;
  border-top: 1px solid #f0f2f9;
  border-radius: 10px;
  transition: background 0.2s ease, padding 0.2s ease;
}

.hot-item:hover {
  background: #fafbff;
  padding-left: 14px;
  padding-right: 14px;
}

.hot-rank {
  flex: 0 0 auto;
  width: 32px;
  color: var(--ch-muted-light);
  font-size: 15px;
  font-weight: 750;
  font-variant-numeric: tabular-nums;
}

.hot-rank.is-top {
  color: var(--ch-primary);
}

.hot-item__body {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.45;
}

.hot-item__meta {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--ch-muted-light);
  font-size: 11px;
}

.hot-item__meta span:first-child {
  font-weight: 700;
}

.hot-item__body strong {
  margin-top: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 650;
}

.hot-item__sub {
  margin-top: 2px;
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.hot-item__arrow {
  margin-left: auto;
  color: var(--ch-border-strong);
  font-size: 14px;
}

.hot-item:hover .hot-item__arrow {
  color: var(--ch-primary);
}

.organizer-cta {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 34px;
  overflow: hidden;
  border-radius: var(--ch-radius);
  background:
    radial-gradient(500px 320px at 100% 0%, rgba(74, 104, 242, 0.32), transparent 60%),
    radial-gradient(300px 260px at 0% 100%, rgba(255, 122, 89, 0.16), transparent 60%),
    #0c142b;
  color: rgba(255, 255, 255, 0.72);
}

.organizer-cta__eyebrow {
  position: relative;
  z-index: 1;
  color: #93a7ff;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.22em;
}

.organizer-cta h2 {
  position: relative;
  z-index: 1;
  margin-top: 16px;
  color: #fff;
  font-size: clamp(26px, 3vw, 34px);
  line-height: 1.25;
  letter-spacing: -0.03em;
}

.organizer-cta > p {
  position: relative;
  z-index: 1;
  margin-top: 14px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  line-height: 1.75;
}

.organizer-cta__list {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 24px;
}

.organizer-cta__list li {
  display: flex;
  align-items: center;
  gap: 9px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12.5px;
}

.organizer-cta__list .el-icon {
  color: #7f98ff;
  font-size: 14px;
}

.organizer-cta__actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: auto;
  padding-top: 28px;
}

.organizer-cta__actions .el-button--primary {
  background: #fff;
  border-color: #fff;
  color: #2439a8;
}

.organizer-cta__actions .el-button--primary:hover {
  background: #eef2ff;
  border-color: #eef2ff;
}

.organizer-cta__ghost {
  border-color: rgba(255, 255, 255, 0.22);
  background: transparent;
  color: rgba(255, 255, 255, 0.82);
}

.organizer-cta__ghost:hover {
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.organizer-cta__orb {
  position: absolute;
  right: -70px;
  bottom: -80px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  pointer-events: none;
}

.organizer-cta__orb::after {
  content: '';
  position: absolute;
  inset: 28px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.organizer-cta__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(180deg, transparent, #000);
  pointer-events: none;
}

.step-strip {
  display: flex;
  align-items: center;
  gap: 26px;
  padding: 34px 38px;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  background: #fff;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  flex: 1;
}

.step-index {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  font-size: 12px;
  font-weight: 750;
}

.step-item strong {
  font-size: 14px;
}

.step-item p {
  margin-top: 3px;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.6;
}

.step-line {
  width: 34px;
  height: 1px;
  background: var(--ch-border);
  flex: 0 0 auto;
}

@media (max-width: 1080px) {
  .hero-grid {
    grid-template-columns: 1fr;
    gap: 44px;
  }

  .hero-visual {
    max-width: 560px;
  }

  .home-split {
    grid-template-columns: 1fr;
  }

  .organizer-cta {
    min-height: 380px;
  }

  .category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .home-hero {
    padding-top: 44px;
  }

  .hero-grid {
    padding-bottom: 46px;
  }

  .hero-copy h1 {
    font-size: clamp(36px, 11vw, 48px);
  }

  .hero-stats {
    gap: 18px;
  }

  .hero-largebr {
    display: none;
  }

  .hero-search {
    flex-direction: column;
    padding: 10px;
  }

  .floating-note {
    display: none;
  }

  .home-section {
    padding-top: 54px;
  }

  .category-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .hero-marquee__inner {
    gap: 10px;
    overflow-x: auto;
    white-space: nowrap;
    justify-content: flex-start;
  }

  .step-strip {
    flex-direction: column;
    align-items: flex-start;
    gap: 18px;
    padding: 24px;
  }

  .step-line {
    display: none;
  }
}
</style>
