<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import type { EChartsOption } from 'echarts'
import {
  ArrowRight,
  Calendar,
  DataAnalysis,
  Refresh,
  Tickets,
  TrendCharts,
  User,
} from '@element-plus/icons-vue'

import { getDashboard } from '@/api/analytics'
import EChart from '@/components/EChart.vue'
import EmptyState from '@/components/EmptyState.vue'
import StatCard from '@/components/StatCard.vue'
import type { Dashboard } from '@/types'
import { formatDateTime, formatNumber, formatPercent } from '@/utils/format'

const loading = ref(true)
const dashboard = ref<Dashboard | null>(null)

const totalSignup = computed(() => dashboard.value?.signup_status.total ?? 0)

const weeklyOption = computed<EChartsOption>(() => {
  const rows = dashboard.value?.weekly_trend ?? []
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(16, 26, 51, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#fff', fontSize: 12 },
    },
    legend: {
      top: 0,
      right: 0,
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: '#66708a', fontSize: 11 },
    },
    grid: { left: 8, right: 14, top: 40, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      data: rows.map((row) => row.week.slice(5)),
      axisLine: { lineStyle: { color: '#dfe4f0' } },
      axisTick: { show: false },
      axisLabel: { color: '#8f99b0', fontSize: 11 },
    },
    yAxis: [
      {
        type: 'value',
        name: '活动',
        nameTextStyle: { color: '#8f99b0', fontSize: 10 },
        minInterval: 1,
        axisLabel: { color: '#8f99b0', fontSize: 11 },
        splitLine: { lineStyle: { color: '#eef1f8', type: 'dashed' } },
      },
      {
        type: 'value',
        name: '报名',
        nameTextStyle: { color: '#8f99b0', fontSize: 10 },
        minInterval: 1,
        axisLabel: { color: '#8f99b0', fontSize: 11 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '新增活动',
        type: 'bar',
        data: rows.map((row) => row.activities),
        barWidth: 14,
        itemStyle: { borderRadius: [5, 5, 0, 0], color: '#9aaaf5' },
      },
      {
        name: '新增报名',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        data: rows.map((row) => row.signups),
        itemStyle: { color: '#3757e8' },
        lineStyle: { width: 3, color: '#3757e8' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(55, 87, 232, 0.2)' },
              { offset: 1, color: 'rgba(55, 87, 232, 0.01)' },
            ],
          },
        },
      },
    ],
  }
})

const statusOption = computed<EChartsOption>(() => {
  const rows = dashboard.value?.status_distribution ?? []
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(16, 26, 51, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: '{b}<br/>{c} 个（{d}%）',
    },
    legend: {
      bottom: 0,
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: '#66708a', fontSize: 11 },
    },
    color: ['#8f99b0', '#f4a340', '#0f9f6e', '#64748b', '#e0484b', '#b42318'],
    series: [
      {
        type: 'pie',
        radius: ['48%', '72%'],
        center: ['50%', '44%'],
        itemStyle: { borderColor: '#fff', borderWidth: 3 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 13, fontWeight: 700 } },
        data: rows.map((row) => ({ name: row.name, value: row.value })),
      },
    ],
  }
})

const maxCategory = computed(() => {
  const rows = dashboard.value?.popular_categories ?? []
  return Math.max(...rows.map((row) => row.participant_count), 1)
})

function funnelPercent(value: number) {
  if (!totalSignup.value) return '0%'
  return `${Math.round((value / totalSignup.value) * 100)}%`
}

const signupBars = computed(() => {
  const data = dashboard.value?.signup_status
  if (!data) return []
  return [
    { label: '报名成功', value: data.success, color: '#3757e8' },
    { label: '完成签到', value: data.checked_in, color: '#0f9f6e' },
    { label: '未签到', value: data.no_show, color: '#e0484b' },
    { label: '候补中', value: data.waitlist, color: '#f4a340' },
  ]
})

async function load() {
  loading.value = true
  try {
    dashboard.value = await getDashboard()
  } catch {
    dashboard.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="dashboard-page" v-loading="loading">
    <div class="page-head">
      <div>
        <span class="eyebrow">Platform analytics</span>
        <h1>全站数据看板</h1>
        <p>掌握平台活动供给、报名转化与到场的整体运行情况。</p>
      </div>
      <div class="page-head__actions">
        <span v-if="dashboard" class="generated-time">
          <el-icon><Refresh /></el-icon>
          更新于 {{ formatDateTime(dashboard.generated_at) }}
        </span>
        <el-button :icon="Refresh" round :loading="loading" @click="load">刷新</el-button>
      </div>
    </div>

    <template v-if="dashboard">
      <div class="stat-grid">
        <StatCard
          label="平台用户"
          :value="formatNumber(dashboard.totals.users)"
          icon="User"
          tone="primary"
          hint="已注册账号"
        />
        <StatCard
          label="活动总数"
          :value="formatNumber(dashboard.totals.activities)"
          icon="Calendar"
          tone="violet"
          :hint="`${dashboard.activity_status.published} 个正在展示`"
        />
        <StatCard
          label="报名总量"
          :value="formatNumber(dashboard.totals.signups)"
          icon="Tickets"
          tone="warning"
          :hint="`候补 ${dashboard.totals.waitlist} 人`"
        />
        <StatCard
          label="已签到"
          :value="formatNumber(dashboard.totals.checked_in)"
          icon="CircleCheck"
          tone="success"
          :hint="`未到场 ${dashboard.totals.no_show} 人`"
        />
        <div class="rate-card">
          <span class="rate-card__label">整体签到率</span>
          <strong>{{ formatPercent(dashboard.rates.checkin_rate) }}</strong>
          <div class="rate-track">
            <span :style="{ width: `${Math.min(dashboard.rates.checkin_rate * 100, 100)}%` }"></span>
          </div>
          <small>已签到 / 报名成功</small>
        </div>
      </div>

      <div class="dashboard-grid">
        <section class="panel panel--trend">
          <div class="panel__head">
            <div>
              <h2>近 8 周运营趋势</h2>
              <p>活动供给与报名需求的周度变化。</p>
            </div>
            <span class="soft-chip"><el-icon><TrendCharts /></el-icon>周维度</span>
          </div>
          <EChart :option="weeklyOption" height="320px" />
        </section>

        <section class="panel">
          <div class="panel__head">
            <div>
              <h2>活动状态分布</h2>
              <p>平台活动所处生命周期的构成。</p>
            </div>
            <el-icon class="panel__icon"><DataAnalysis /></el-icon>
          </div>
          <EChart :option="statusOption" height="320px" />
        </section>

        <section class="panel">
          <div class="panel__head">
            <div>
              <h2>热门活动分类</h2>
              <p>按成功报名人数排序的分类表现。</p>
            </div>
            <RouterLink to="/activities" class="text-link">
              活动广场
              <el-icon><ArrowRight /></el-icon>
            </RouterLink>
          </div>
          <div v-if="dashboard.popular_categories.length" class="category-list">
            <div
              v-for="category in dashboard.popular_categories"
              :key="category.id"
              class="category-row"
            >
              <div class="category-row__head">
                <span class="category-dot" :style="{ background: category.color }"></span>
                <strong>{{ category.name }}</strong>
                <span class="category-count">{{ category.activity_count }} 个活动</span>
                <span class="category-participants">{{ category.participant_count }} 人</span>
              </div>
              <div class="category-track">
                <span
                  :style="{
                    width: `${Math.max((category.participant_count / maxCategory) * 100, 2)}%`,
                    background: category.color,
                  }"
                ></span>
              </div>
            </div>
          </div>
          <EmptyState v-else title="暂无分类数据" description="活动发布并产生报名后，这里会展示分类热度。" />
        </section>

        <section class="panel">
          <div class="panel__head">
            <div>
              <h2>报名转化漏斗</h2>
              <p>从报名成功到实际到场的整体流转。</p>
            </div>
            <el-icon class="panel__icon"><Tickets /></el-icon>
          </div>
          <div class="funnel">
            <div v-for="bar in signupBars" :key="bar.label" class="funnel-row">
              <div class="funnel-row__head">
                <span>{{ bar.label }}</span>
                <strong>{{ formatNumber(bar.value) }}</strong>
              </div>
              <div class="funnel-track">
                <span
                  :style="{
                    width: funnelPercent(bar.value),
                    background: bar.color,
                  }"
                ></span>
              </div>
              <small>{{ funnelPercent(bar.value) }}</small>
            </div>
          </div>
          <div class="activity-status-strip">
            <div>
              <span>待审核</span>
              <strong>{{ dashboard.activity_status.pending }}</strong>
            </div>
            <div>
              <span>草稿</span>
              <strong>{{ dashboard.activity_status.draft }}</strong>
            </div>
            <div>
              <span>已结束</span>
              <strong>{{ dashboard.activity_status.ended }}</strong>
            </div>
            <div>
              <span>已取消</span>
              <strong>{{ dashboard.activity_status.cancelled }}</strong>
            </div>
          </div>
        </section>
      </div>

      <div class="quick-strip">
        <div class="quick-strip__text">
          <el-icon><User /></el-icon>
          <div>
            <strong>平台治理入口</strong>
            <span>审核待发布活动、管理用户角色与维护分类标签。</span>
          </div>
        </div>
        <div class="quick-strip__actions">
          <RouterLink to="/console/audit" class="quick-link">
            <el-icon><Calendar /></el-icon>
            审核工作台
          </RouterLink>
          <RouterLink to="/console/users" class="quick-link">
            <el-icon><User /></el-icon>
            用户管理
          </RouterLink>
          <RouterLink to="/console/dictionaries" class="quick-link">
            <el-icon><Tickets /></el-icon>
            字典管理
          </RouterLink>
        </div>
      </div>
    </template>

    <EmptyState
      v-else-if="!loading"
      title="暂时无法获取看板数据"
      description="请确认后端服务已启动，或稍后重试。"
    >
      <el-button round :icon="Refresh" @click="load">重新加载</el-button>
    </EmptyState>
  </div>
</template>

<style scoped>
.dashboard-page {
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

.page-head__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
}

.generated-time {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ch-muted-light);
  font-size: 11px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) 1.2fr;
  gap: 16px;
}

.rate-card {
  padding: 22px;
  background:
    radial-gradient(260px 140px at 100% 0%, rgba(55, 87, 232, 0.08), transparent 70%),
    #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.rate-card__label {
  color: var(--ch-muted);
  font-size: 13px;
}

.rate-card strong {
  display: block;
  margin-top: 2px;
  font-size: 26px;
  letter-spacing: -0.03em;
}

.rate-track {
  height: 7px;
  margin: 14px 0 8px;
  border-radius: 999px;
  background: #edf0f7;
  overflow: hidden;
}

.rate-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #34c38f, #0f9f6e);
}

.rate-card small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(320px, 1fr);
  gap: 20px;
}

.panel {
  padding: 24px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  min-width: 0;
}

.panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
}

.panel__head h2 {
  font-size: 16px;
}

.panel__head p {
  margin-top: 4px;
  color: var(--ch-muted);
  font-size: 12px;
}

.panel__icon {
  color: var(--ch-muted-light);
  font-size: 20px;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 18px;
}

.category-row__head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.category-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.category-row__head strong {
  font-size: 13px;
}

.category-count {
  margin-left: auto;
  color: var(--ch-muted-light);
  font-size: 11px;
}

.category-participants {
  min-width: 56px;
  text-align: right;
  color: var(--ch-ink-soft);
  font-size: 12px;
  font-weight: 700;
}

.category-track {
  height: 6px;
  margin-top: 7px;
  border-radius: 999px;
  background: #f1f4fa;
  overflow: hidden;
}

.category-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  opacity: 0.85;
}

.funnel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 20px;
}

.funnel-row {
  position: relative;
}

.funnel-row__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  font-size: 12px;
  color: var(--ch-muted);
}

.funnel-row__head strong {
  color: var(--ch-ink);
  font-size: 14px;
}

.funnel-track {
  height: 8px;
  margin-top: 6px;
  border-radius: 999px;
  background: #f1f4fa;
  overflow: hidden;
}

.funnel-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.5s ease;
}

.funnel-row small {
  position: absolute;
  right: 0;
  bottom: 14px;
  color: var(--ch-muted-light);
  font-size: 10px;
}

.activity-status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px dashed var(--ch-border);
}

.activity-status-strip div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.activity-status-strip span {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.activity-status-strip strong {
  font-size: 18px;
}

.quick-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px 24px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.quick-strip__text {
  display: flex;
  align-items: center;
  gap: 14px;
}

.quick-strip__text > .el-icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 13px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  font-size: 20px;
}

.quick-strip__text div {
  display: flex;
  flex-direction: column;
}

.quick-strip__text strong {
  font-size: 14px;
}

.quick-strip__text span {
  color: var(--ch-muted);
  font-size: 12px;
}

.quick-strip__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--ch-border);
  border-radius: 999px;
  color: var(--ch-ink-soft);
  font-size: 12px;
  font-weight: 600;
  transition: all 0.18s ease;
}

.quick-link:hover {
  border-color: var(--ch-primary);
  color: var(--ch-primary);
  background: var(--ch-primary-soft);
}

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .dashboard-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 760px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .quick-strip {
    flex-direction: column;
    align-items: flex-start;
  }

  .activity-status-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
