<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="not-found">
    <div class="not-found__inner">
      <div class="not-found__code">
        <span>4</span>
        <span class="not-found__orb">0</span>
        <span>4</span>
      </div>
      <h1>这条路口没有活动</h1>
      <p>页面可能已被移动或删除。回到活动广场，继续发现校园里的新鲜事。</p>
      <div class="not-found__actions">
        <el-button type="primary" size="large" round @click="router.push('/')">回到首页</el-button>
        <el-button size="large" round @click="router.push('/activities')">逛逛活动</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: grid;
  place-items: center;
  min-height: calc(100vh - 220px);
  padding: 60px 24px;
  background:
    radial-gradient(600px 300px at 50% 0%, rgba(55, 87, 232, 0.12), transparent 65%),
    var(--ch-bg);
}

.not-found__inner {
  text-align: center;
}

.not-found__code {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: clamp(88px, 16vw, 150px);
  font-weight: 850;
  line-height: 1;
  letter-spacing: -0.06em;
  color: var(--ch-ink);
}

.not-found__orb {
  display: inline-grid;
  place-items: center;
  width: 0.92em;
  height: 0.92em;
  border-radius: 50%;
  background: linear-gradient(135deg, #5874f5, #3757e8 60%, #2439a8);
  color: #fff;
  font-size: 0.72em;
  box-shadow: 0 24px 50px rgba(55, 87, 232, 0.32);
  animation: float 4s ease-in-out infinite;
}

.not-found h1 {
  margin-top: 18px;
  font-size: clamp(22px, 3vw, 30px);
  letter-spacing: -0.02em;
}

.not-found p {
  margin: 12px auto 0;
  max-width: 420px;
  color: var(--ch-muted);
}

.not-found__actions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}
</style>
