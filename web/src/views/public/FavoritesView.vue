<script setup lang="ts">
import { onMounted, ref } from 'vue'

import ActivityCard from '@/components/ActivityCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { myFavorites } from '@/api/activities'
import type { ActivityBrief, Paginated } from '@/types'

const pageData = ref<Paginated<ActivityBrief>>({
  total: 0,
  page: 1,
  page_size: 9,
  results: [],
})
const loading = ref(true)

async function load(page = 1) {
  loading.value = true
  try {
    pageData.value = await myFavorites({ page })
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    loading.value = false
  }
}

onMounted(() => load(1))
</script>

<template>
  <div class="favorites-page">
    <section class="page-hero">
      <div class="page-container">
        <span class="eyebrow">Saved activities</span>
        <h1>我的收藏</h1>
        <p>把心动的活动收进这里，报名截止前记得回来看看。</p>
      </div>
    </section>

    <section class="page-container page-block">
      <div v-if="loading" class="card-grid">
        <div v-for="item in 3" :key="item" class="skeleton-card skeleton-block"></div>
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
        title="收藏夹还是空的"
        description="在活动详情页点击收藏，之后就能在这里快速找到它。"
      >
        <RouterLink to="/activities">
          <el-button type="primary" round>去发现活动</el-button>
        </RouterLink>
      </EmptyState>

      <div v-if="pageData.total > pageData.page_size" class="pager-row">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="pageData.total"
          :page-size="pageData.page_size"
          :current-page="pageData.page"
          @current-change="load"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
.skeleton-card {
  height: 390px;
}
</style>
