<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { EChartsOption } from 'echarts'
import {
  ArrowLeft,
  DataLine,
  Refresh,
  Tickets,
  TrendCharts,
  User,
  View,
} from '@element-plus/icons-vue'

import { getActivityStatistics } from '@/api/analytics'
import EChart from '@/components/EChart.vue'
import EmptyState from '@/components/EmptyState.vue'
import StatCard from '@/components/StatCard.vue'
import type { ActivityStatistics } from '@/types'
import {
  activityStatusMeta,
  formatNumber,
  formatPercent,
} from '@/utils/format'

const route = useRoute()
const router = useRouter()
const activityId = Number(route.params.id)

const loading = ref(true)
const stats = ref<ActivityStatistics | null>(null)

const signupTotal = computed(() => stats.value?.counts.total ?? 0)
const checkedIn = computed(() => stats.value?.counts.checked_in ?? 0)

const trendOption = computed<EChartsOption>(() => {
  const rows = stats.value?.signup_trend ?? []
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(16, 26, 51, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#fff', fontSize: 12 },
      valueFormatter: (value) => `${value} 人`,
    },
    grid: { left: 8, right: 18, top: 24, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: rows.map((row) => row.date.slice(5)),
      axisLine: { lineStyle: { color: '#dfe4f0' } },
      axisTick: { show: false },
      axisLabel: { color: '#8f99b0', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#8f99b0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#eef1f8', type: 'dashed' } },
    },
    series: [
      {
        name: '新增报名',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        data: rows.map((row) => row.value),
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
              { offset: 0, color: 'rgba(55, 87, 232, 0.28)' },
              { offset: 1, color: 'rgba(55, 87, 232, 0.01)' },
            ],
          },
        },
      },
    ],
  }
})

const collegeOption = computed<EChartsOption>(() => {
  const rows = [...(stats.value?.college_distribution ?? [])].reverse()
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(16, 26, 51, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#fff', fontSize: 12 },
      valueFormatter: (value) => `${value} 人`,
    },
    grid: { left: 8, right: 30, top: 12, bottom: 8, containLabel: true },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#8f99b0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#eef1f8', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: rows.map((row) => row.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#5a6680', fontSize: 12, width: 110, overflow: 'truncate' },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((row) => row.value),
        barWidth: 14,
        itemStyle: {
          borderRadius: [0, 7, 7, 0],
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: '#6b83f0' },
              { offset: 1, color: '#3757e8' },
            ],
          },
        },
        label: { show: true, position: 'right', color: '#8f99b0', fontSize: 11 },
      },
    ],
  }
})

const gradeOption = computed<EChartsOption>(() => {
  const rows = stats.value?.grade_distribution ?? []
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(16, 26, 51, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: '{b}<br/>{c} 人（{d}%）',
    },
    legend: {
      bottom: 0,
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: '#66708a', fontSize: 11 },
    },
    color: ['#3757e8', '#7a5af8', '#0f9f6e', '#f4a340', '#ff7a59', '#38bdf8'],
    series: [
      {
        type: 'pie',
        radius: ['46%', '70%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: '#fff', borderWidth: 3 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 700 } },
        data: rows,
      },
    ],
  }
})

const methodOption = computed<EChartsOption>(() => {
  const rows = stats.value?.checkin_method_distribution ?? []
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(16, 26, 51, 0.92)',
      borderWidth: 0,
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: '{b}<br/>{c} 人（{d}%）',
    },
    legend: {
      bottom: 0,
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: '#66708a', fontSize: 11 },
    },
    color: ['#3757e8', '#0f9f6e'],
    series: [
      {
        type: 'pie',
        radius: ['48%', '72%'],
        center: ['50%', '44%'],
        itemStyle: { borderColor: '#fff', borderWidth: 3 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 700 } },
        data: rows,
      },
    ],
  }
})

async function load() {
  loading.value = true
  try {
    stats.value = await getActivityStatistics(activityId)
  } catch {
    stats.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="stats-page" v-loading="loading">
    <div class="page-head">
      <div>
        <button type="button" class="back-link" @click="router.push('/console/activities')">
          <el-icon><ArrowLeft /></el-icon>
          返回我的活动
        </button>
        <div class="page-head__title">
          <h1>{{ stats?.activity.title || '活动数据' }}</h1>
          <span
            v-if="stats"
            class="status-pill"
            :class="activityStatusMeta(stats.activity.status).className"
          >
            {{ stats.activity.status_text }}
          </span>
        </div>
        <p>报名、到场与人群画像，帮助你复盘活动效果。</p>
      </div>
      <div class="page-head__actions">
        <el-button :icon="Refresh" round :loading="loading" @click="load">刷新数据</el-button>
        <el-button round @click="router.push(`/console/activities/${activityId}/roster`)">
          查看名单
        </el-button>
      </div>
    </div>

    <template v-if="stats">
      <div class="rate-grid">
        <div class="rate-card">
          <span>名额使用率</span>
          <strong>{{ formatPercent(stats.rates.fill_rate) }}</strong>
          <div class="rate-track">
            <span :style="{ width: `${Math.min(stats.rates.fill_rate * 100, 100)}%` }"></span>
          </div>
          <small>{{ stats.counts.success }} / {{ stats.activity.capacity }} 人</small>
        </div>
        <div class="rate-card">
          <span>签到率</span>
          <strong>{{ formatPercent(stats.rates.checkin_rate) }}</strong>
          <div class="rate-track rate-track--green">
            <span :style="{ width: `${Math.min(stats.rates.checkin_rate * 100, 100)}%` }"></span>
          </div>
          <small>{{ stats.counts.checked_in }} / {{ stats.counts.success }} 人</small>
        </div>
        <div class="rate-card">
          <span>候补转正率</span>
          <strong>{{ formatPercent(stats.rates.waitlist_promotion_rate) }}</strong>
          <div class="rate-track rate-track--orange">
            <span :style="{ width: `${Math.min(stats.rates.waitlist_promotion_rate * 100, 100)}%` }"></span>
          </div>
          <small>{{ stats.counts.promoted }} / {{ stats.counts.waitlisted_ever }} 人</small>
        </div>
        <div class="rate-card">
          <span>浏览转化率</span>
          <strong>{{ formatPercent(stats.rates.view_conversion_rate) }}</strong>
          <div class="rate-track rate-track--violet">
            <span :style="{ width: `${Math.min(stats.rates.view_conversion_rate * 100, 100)}%` }"></span>
          </div>
          <small>{{ stats.counts.success }} / {{ formatNumber(stats.activity.view_count) }} 次浏览</small>
        </div>
      </div>

      <div class="stat-grid">
        <StatCard label="报名总量" :value="signupTotal" icon="Tickets" tone="primary" hint="含候补与取消记录" />
        <StatCard label="报名成功" :value="stats.counts.success" icon="CircleCheck" tone="success" hint="含已签到与未签到" />
        <StatCard label="已签到" :value="checkedIn" icon="Select" tone="teal" hint="现场实际到场人数" />
        <StatCard label="候补队列" :value="stats.counts.waitlist" icon="Clock" tone="warning" :hint="`累计候补 ${stats.counts.waitlisted_ever} 人`" />
        <StatCard label="未到场" :value="stats.counts.no_show" icon="Warning" tone="rose" hint="报名成功但未签到" />
        <StatCard label="已取消" :value="stats.counts.cancelled" icon="Close" tone="violet" hint="主动取消的报名" />
      </div>

      <section class="chart-card chart-card--wide">
        <div class="chart-card__head">
          <div>
            <h2>近 7 天报名趋势</h2>
            <p>观察报名高峰，把握下一次活动的宣发节奏。</p>
          </div>
          <span class="soft-chip"><el-icon><TrendCharts /></el-icon>按天统计</span>
        </div>
        <EChart :option="trendOption" height="300px" />
      </section>

      <div class="chart-grid">
        <section class="chart-card">
          <div class="chart-card__head">
            <div>
              <h2>学院分布</h2>
              <p>成功报名学生的学院构成。</p>
            </div>
            <el-icon class="chart-card__icon"><User /></el-icon>
          </div>
          <EChart v-if="stats.college_distribution.length" :option="collegeOption" height="300px" />
          <EmptyState v-else title="暂无学院数据" description="有成功报名后即可查看学院分布。" />
        </section>

        <section class="chart-card">
          <div class="chart-card__head">
            <div>
              <h2>年级分布</h2>
              <p>参与学生的年级构成。</p>
            </div>
            <el-icon class="chart-card__icon"><DataLine /></el-icon>
          </div>
          <EChart v-if="stats.grade_distribution.length" :option="gradeOption" height="300px" />
          <EmptyState v-else title="暂无年级数据" description="学生完善年级信息后即可统计。" />
        </section>

        <section class="chart-card">
          <div class="chart-card__head">
            <div>
              <h2>签到方式</h2>
              <p>扫码签到与手动补签的比例。</p>
            </div>
            <el-icon class="chart-card__icon"><View /></el-icon>
          </div>
          <EChart v-if="stats.checkin_method_distribution.length" :option="methodOption" height="300px" />
          <EmptyState v-else title="暂无签到记录" description="活动开始后，签到数据会实时汇总到这里。" />
        </section>

        <section class="chart-card overview-card">
          <div class="chart-card__head">
            <div>
              <h2>数据解读</h2>
              <p>基于当前活动数据自动生成。</p>
            </div>
            <el-icon class="chart-card__icon"><Tickets /></el-icon>
          </div>
          <ul class="insights">
            <li>
              <span>名额使用</span>
              <strong>{{ formatPercent(stats.rates.fill_rate) }}</strong>
              <p>
                {{ stats.rates.fill_rate >= 0.9 ? '活动名额接近满员，可考虑增加场次。' : '还有余量，可通过推送与社群继续招募。' }}
              </p>
            </li>
            <li>
              <span>现场到场</span>
              <strong>{{ formatPercent(stats.rates.checkin_rate) }}</strong>
              <p>
                {{ stats.rates.checkin_rate >= 0.8 ? '到场情况良好，签到流程运转顺畅。' : '签到率有提升空间，建议提前提醒并优化签到入口。' }}
              </p>
            </li>
            <li>
              <span>候补转化</span>
              <strong>{{ formatPercent(stats.rates.waitlist_promotion_rate) }}</strong>
              <p>
                {{ stats.counts.waitlisted_ever ? `共有 ${stats.counts.waitlisted_ever} 人进入候补，${stats.counts.promoted} 人成功转正。` : '本次活动没有产生候补记录。' }}
              </p>
            </li>
          </ul>
        </section>
      </div>
    </template>

    <EmptyState
      v-else-if="!loading"
      title="暂时无法获取活动数据"
      description="请确认活动存在且你有权限查看，或稍后重试。"
    >
      <el-button round @click="load">重新加载</el-button>
    </EmptyState>
  </div>
</template>

<style scoped>
.stats-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
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
  font-size: 28px;
  letter-spacing: -0.03em;
}

.page-head p {
  margin-top: 6px;
  color: var(--ch-muted);
  font-size: 14px;
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

.rate-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.rate-card {
  padding: 20px 22px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.rate-card > span {
  color: var(--ch-muted);
  font-size: 12px;
}

.rate-card > strong {
  display: block;
  margin-top: 2px;
  font-size: 28px;
  letter-spacing: -0.03em;
}

.rate-track {
  height: 6px;
  margin: 12px 0 8px;
  border-radius: 999px;
  background: #edf0f7;
  overflow: hidden;
}

.rate-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6b83f0, #3757e8);
  transition: width 0.5s ease;
}

.rate-track--green span {
  background: linear-gradient(90deg, #34c38f, #0f9f6e);
}

.rate-track--orange span {
  background: linear-gradient(90deg, #f7bd5c, #d98a00);
}

.rate-track--violet span {
  background: linear-gradient(90deg, #a78bfa, #7a5af8);
}

.rate-card small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.stat-grid :deep(.stat-card) {
  padding: 18px;
  gap: 12px;
}

.stat-grid :deep(.stat-card__icon) {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  font-size: 18px;
}

.stat-grid :deep(.stat-card__value) {
  font-size: 22px;
}

.stat-grid :deep(.stat-card__hint) {
  display: none;
}

.chart-card {
  padding: 24px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
}

.chart-card--wide {
  width: 100%;
}

.chart-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 10px;
}

.chart-card__head h2 {
  font-size: 16px;
}

.chart-card__head p {
  margin-top: 4px;
  color: var(--ch-muted);
  font-size: 12px;
}

.chart-card__icon {
  color: var(--ch-muted-light);
  font-size: 20px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.chart-grid .empty-state {
  padding: 40px 20px;
}

.overview-card {
  display: flex;
  flex-direction: column;
}

.insights {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 6px;
}

.insights li {
  padding: 14px 16px;
  border-radius: 12px;
  background: #fafbfe;
  border: 1px solid #eff2f9;
}

.insights span {
  color: var(--ch-muted);
  font-size: 11px;
}

.insights strong {
  float: right;
  font-size: 15px;
}

.insights p {
  margin-top: 4px;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1000px) {
  .rate-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 700px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .rate-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
