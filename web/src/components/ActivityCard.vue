<script setup lang="ts">
import { computed, ref, type Component } from 'vue'
import {
  ArrowRight,
  Basketball,
  Brush,
  Calendar,
  Camera,
  Coffee,
  Compass,
  Film,
  Flag,
  Microphone,
  Present,
  Promotion,
  Reading,
  Star,
  Trophy,
} from '@element-plus/icons-vue'

import type { ActivityBrief } from '@/types'
import {
  activityStatusMeta,
  categoryGradient,
  formatMonthDay,
  formatTimeRange,
  formatWeekday,
} from '@/utils/format'

const props = defineProps<{
  activity: ActivityBrief
}>()

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

const coverError = ref(false)
const categoryIcon = computed(() => iconMap[props.activity.category?.icon] ?? Calendar)
const status = computed(() => activityStatusMeta(props.activity.status))
const catColor = computed(() => props.activity.category?.color || '#3757e8')
const coverStyle = computed(() => ({ background: categoryGradient(catColor.value) }))
const percent = computed(() => {
  if (!props.activity.capacity) return 0
  return Math.min(100, Math.round((props.activity.signup_count / props.activity.capacity) * 100))
})
const hasCover = computed(() => Boolean(props.activity.cover_url) && !coverError.value)
const isEnded = computed(() => props.activity.status === 3)
</script>

<template>
  <RouterLink
    :to="`/activities/${activity.id}`"
    class="activity-card"
    :style="{ '--cat-color': catColor }"
  >
    <div class="activity-card__cover" :style="coverStyle">
      <img
        v-if="hasCover"
        :src="activity.cover_url"
        :alt="activity.title"
        loading="lazy"
        @error="coverError = true"
      />
      <div v-else class="cover-pattern">
        <el-icon><component :is="categoryIcon" /></el-icon>
        <span>{{ activity.category?.name }}</span>
      </div>
      <div class="cover-shade"></div>
      <span class="status-pill cover-status" :class="status.className">{{ status.label }}</span>
      <div class="cover-date">
        <span>{{ formatMonthDay(activity.start_time).replace('月', ' / ').replace('日', '') }}</span>
        <small>{{ formatWeekday(activity.start_time) }}</small>
      </div>
    </div>

    <div class="activity-card__body">
      <div class="card-eyebrow">
        <span class="category-name">{{ activity.category?.name || '校园活动' }}</span>
        <span class="dot-separator"></span>
        <span>{{ activity.club?.name || activity.organizer?.display_name }}</span>
      </div>

      <h3>{{ activity.title }}</h3>
      <p class="summary">{{ activity.summary || '精彩校园活动，等你来参与。' }}</p>

      <div class="facts">
        <span>
          <el-icon><Clock /></el-icon>
          {{ formatTimeRange(activity.start_time, activity.end_time) }}
        </span>
        <span>
          <el-icon><Location /></el-icon>
          {{ activity.location }}
        </span>
      </div>

      <div class="card-footer">
        <div class="capacity">
          <div class="capacity-bar">
            <span :style="{ width: `${percent}%` }"></span>
          </div>
          <span class="capacity-text">
            {{ activity.signup_count }} / {{ activity.capacity }}
          </span>
        </div>
        <span class="card-cta">
          {{ isEnded ? '回顾活动' : '查看详情' }}
          <el-icon><ArrowRight /></el-icon>
        </span>
      </div>
    </div>
  </RouterLink>
</template>

<style scoped>
.activity-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  box-shadow: 0 1px 2px rgba(16, 26, 51, 0.03);
  transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}

.activity-card:hover {
  transform: translateY(-5px);
  border-color: rgba(55, 87, 232, 0.22);
  box-shadow: var(--ch-shadow-hover);
}

.activity-card__cover {
  position: relative;
  height: 168px;
  overflow: hidden;
}

.activity-card__cover::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255, 255, 255, 0.16) 1px, transparent 1px);
  background-size: 18px 18px;
  pointer-events: none;
}

.activity-card__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.activity-card:hover .activity-card__cover img {
  transform: scale(1.05);
}

.cover-pattern {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.94);
}

.cover-pattern .el-icon {
  font-size: 42px;
  opacity: 0.9;
}

.cover-pattern span {
  font-size: 12px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  opacity: 0.75;
}

.cover-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(8, 14, 30, 0.02) 30%, rgba(8, 14, 30, 0.42));
}

.cover-status {
  position: absolute;
  top: 14px;
  right: 14px;
  z-index: 1;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
}

.cover-date {
  position: absolute;
  left: 16px;
  bottom: 14px;
  z-index: 1;
  display: flex;
  flex-direction: column;
  padding: 7px 11px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--ch-ink);
  line-height: 1.25;
  backdrop-filter: blur(8px);
}

.cover-date span {
  font-size: 15px;
  font-weight: 750;
  letter-spacing: -0.01em;
}

.cover-date small {
  font-size: 11px;
  color: var(--ch-muted);
}

.activity-card__body {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 18px 20px 18px;
}

.card-eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ch-muted-light);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.category-name {
  color: var(--cat-color);
  font-weight: 700;
}

.activity-card h3 {
  margin-top: 9px;
  font-size: 17px;
  line-height: 1.45;
  font-weight: 700;
  letter-spacing: -0.01em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 49px;
}

.summary {
  margin-top: 7px;
  color: var(--ch-muted);
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 42px;
}

.facts {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 12px;
  color: var(--ch-muted);
  font-size: 12.5px;
}

.facts span {
  display: flex;
  align-items: center;
  gap: 7px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.facts .el-icon {
  flex: 0 0 auto;
  color: var(--ch-muted-light);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: auto;
  padding-top: 16px;
}

.capacity {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
}

.capacity-bar {
  width: 64px;
  height: 5px;
  border-radius: 999px;
  background: #edf0f8;
  overflow: hidden;
}

.capacity-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--cat-color);
  transition: width 0.4s ease;
}

.capacity-text {
  color: var(--ch-muted-light);
  font-size: 11.5px;
  font-variant-numeric: tabular-nums;
}

.card-cta {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ch-primary);
  font-size: 12.5px;
  font-weight: 700;
}

@media (max-width: 480px) {
  .activity-card__cover {
    height: 150px;
  }
}
</style>
