<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Lock } from '@element-plus/icons-vue'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const from = computed(() => (typeof route.query.from === 'string' ? route.query.from : ''))
</script>

<template>
  <div class="page-block">
    <div class="page-container">
      <div class="forbidden-card">
        <div class="forbidden-card__icon">
          <el-icon><Lock /></el-icon>
        </div>
        <span class="eyebrow">Access denied</span>
        <h1>这个区域需要更高的权限</h1>
        <p>
          当前账号可以正常浏览活动与个人中心。如果你认为这是配置问题，请联系平台管理员为你的账号分配对应角色。
        </p>
        <div v-if="from" class="forbidden-card__path">请求路径：{{ from }}</div>
        <div class="forbidden-card__actions">
          <el-button type="primary" size="large" round @click="router.push('/activities')">
            去活动广场
          </el-button>
          <el-button v-if="auth.canUseConsole" size="large" round @click="router.push('/console')">
            返回工作台
          </el-button>
          <el-button v-else size="large" round @click="router.push('/')">回到首页</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forbidden-card {
  max-width: 640px;
  margin: 32px auto;
  padding: 56px 48px;
  text-align: center;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: 28px;
  box-shadow: var(--ch-shadow);
}

.forbidden-card__icon {
  display: grid;
  place-items: center;
  width: 78px;
  height: 78px;
  margin: 0 auto 22px;
  border-radius: 24px;
  background: var(--ch-accent-soft);
  color: var(--ch-accent);
  font-size: 34px;
}

.forbidden-card .eyebrow {
  color: var(--ch-accent);
  letter-spacing: 0.2em;
}

.forbidden-card .eyebrow::before {
  display: none;
}

.forbidden-card h1 {
  margin-top: 12px;
  font-size: clamp(26px, 4vw, 34px);
  letter-spacing: -0.02em;
}

.forbidden-card p {
  margin: 14px auto 0;
  max-width: 460px;
  color: var(--ch-muted);
  font-size: 15px;
}

.forbidden-card__path {
  display: inline-flex;
  margin-top: 18px;
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--ch-bg);
  color: var(--ch-muted-light);
  font-size: 12px;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}

.forbidden-card__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin-top: 30px;
}

@media (max-width: 640px) {
  .forbidden-card {
    padding: 40px 22px;
  }
}
</style>
