<script setup lang="ts">
defineProps<{
  eyebrow?: string
  title: string
  description?: string
}>()
</script>

<template>
  <div class="auth-layout">
    <aside class="auth-aside">
      <RouterLink to="/" class="auth-brand">
        <span class="auth-brand__mark">C</span>
        <span class="auth-brand__text">
          <strong>CampusHub</strong>
          <small>校园活动平台</small>
        </span>
      </RouterLink>

      <div class="auth-aside__content">
        <span class="auth-aside__eyebrow">CAMPUS LIFE, CONNECTED</span>
        <h1>让校园生活，<br /><em>在这里发生。</em></h1>
        <p>
          从一场讲座、一次比赛，到一群志同道合的人。CampusHub 把活动发现、报名候补、扫码签到和数据分析放在同一个地方。
        </p>

        <div class="auth-feature-list">
          <div class="auth-feature">
            <span class="auth-feature__icon"><el-icon><Compass /></el-icon></span>
            <div>
              <strong>发现精彩活动</strong>
              <small>六大分类，按兴趣与时间轻松筛选</small>
            </div>
          </div>
          <div class="auth-feature">
            <span class="auth-feature__icon"><el-icon><Tickets /></el-icon></span>
            <div>
              <strong>报名与候补一步到位</strong>
              <small>满员自动候补，名额释放即刻转正</small>
            </div>
          </div>
          <div class="auth-feature">
            <span class="auth-feature__icon"><el-icon><Camera /></el-icon></span>
            <div>
              <strong>现场扫码签到</strong>
              <small>动态二维码防代签，签到记录实时可查</small>
            </div>
          </div>
        </div>

        <div class="auth-metrics">
          <div>
            <strong>6</strong>
            <span>活动分类</span>
          </div>
          <div>
            <strong>30s</strong>
            <span>动态码刷新</span>
          </div>
          <div>
            <strong>24h</strong>
            <span>在线服务</span>
          </div>
        </div>
      </div>

      <span class="auth-aside__copyright">© 2026 CampusHub · 校园活动平台</span>

      <span class="orb orb--one"></span>
      <span class="orb orb--two"></span>
      <span class="orb orb--three"></span>
      <span class="grid-lines"></span>
    </aside>

    <section class="auth-main">
      <div class="auth-main__top">
        <RouterLink to="/" class="auth-back">
          <el-icon><ArrowLeft /></el-icon>
          返回首页
        </RouterLink>
        <span class="auth-main__hint">安全登录 · 仅限校内师生</span>
      </div>

      <div class="auth-card">
        <span v-if="eyebrow" class="eyebrow">{{ eyebrow }}</span>
        <h2>{{ title }}</h2>
        <p v-if="description" class="auth-card__description">{{ description }}</p>
        <slot />
      </div>

      <div class="auth-main__footer">
        <span>CampusHub · 让每一次参与都简单</span>
      </div>
    </section>
  </div>
</template>

<style scoped>
.auth-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(480px, 0.95fr);
  min-height: 100vh;
  background: #fff;
}

.auth-aside {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 40px 54px;
  overflow: hidden;
  background:
    radial-gradient(900px 600px at 10% 0%, rgba(76, 106, 245, 0.4), transparent 60%),
    radial-gradient(600px 500px at 95% 100%, rgba(122, 90, 248, 0.24), transparent 60%),
    #0a1226;
  color: rgba(255, 255, 255, 0.72);
}

.auth-brand {
  position: relative;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 11px;
  align-self: flex-start;
}

.auth-brand__mark {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 13px;
  background: linear-gradient(135deg, #6d86ff, #3757e8 60%, #2439a8);
  color: #fff;
  font-size: 22px;
  font-weight: 800;
  box-shadow: 0 10px 28px rgba(55, 87, 232, 0.4);
}

.auth-brand__text {
  display: flex;
  flex-direction: column;
  line-height: 1.12;
}

.auth-brand__text strong {
  color: #fff;
  font-size: 17px;
  font-weight: 800;
}

.auth-brand__text small {
  color: rgba(255, 255, 255, 0.4);
  font-size: 9.5px;
  letter-spacing: 0.18em;
}

.auth-aside__content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex: 1;
  max-width: 540px;
  padding: 54px 0;
}

.auth-aside__eyebrow {
  color: #8fa4ff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.28em;
}

.auth-aside__content h1 {
  margin-top: 18px;
  color: #fff;
  font-size: clamp(36px, 4.2vw, 54px);
  line-height: 1.16;
  letter-spacing: -0.035em;
  font-weight: 800;
}

.auth-aside__content h1 em {
  font-style: normal;
  background: linear-gradient(100deg, #9fb2ff, #ffffff 42%, #ffc4b5);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.auth-aside__content > p {
  max-width: 460px;
  margin-top: 22px;
  color: rgba(255, 255, 255, 0.52);
  font-size: 14.5px;
  line-height: 1.85;
}

.auth-feature-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 34px;
}

.auth-feature {
  display: flex;
  align-items: center;
  gap: 14px;
}

.auth-feature__icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: #b3c1ff;
  font-size: 19px;
  backdrop-filter: blur(8px);
}

.auth-feature div {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}

.auth-feature strong {
  color: rgba(255, 255, 255, 0.92);
  font-size: 13.5px;
  font-weight: 650;
}

.auth-feature small {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}

.auth-metrics {
  display: flex;
  gap: 40px;
  margin-top: 40px;
  padding-top: 28px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.auth-metrics div {
  display: flex;
  flex-direction: column;
}

.auth-metrics strong {
  color: #fff;
  font-size: 26px;
  font-weight: 760;
  letter-spacing: -0.02em;
}

.auth-metrics span {
  color: rgba(255, 255, 255, 0.36);
  font-size: 11.5px;
}

.auth-aside__copyright {
  position: relative;
  z-index: 2;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.28);
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(1px);
  pointer-events: none;
}

.orb--one {
  width: 320px;
  height: 320px;
  right: -110px;
  top: 8%;
  background: radial-gradient(circle at 35% 35%, rgba(112, 137, 255, 0.34), transparent 68%);
  animation: float-soft 9s ease-in-out infinite;
}

.orb--two {
  width: 220px;
  height: 220px;
  left: -80px;
  bottom: 12%;
  background: radial-gradient(circle at 40% 40%, rgba(255, 138, 110, 0.2), transparent 68%);
  animation: float-soft 12s ease-in-out infinite reverse;
}

.orb--three {
  width: 90px;
  height: 90px;
  right: 22%;
  bottom: 20%;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.grid-lines {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: radial-gradient(circle at 40% 40%, #000, transparent 78%);
  pointer-events: none;
}

.auth-main {
  display: flex;
  flex-direction: column;
  padding: 34px 48px 26px;
  background:
    radial-gradient(700px 360px at 100% 0%, rgba(55, 87, 232, 0.05), transparent 60%),
    #fff;
}

.auth-main__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.auth-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--ch-muted);
  font-size: 13px;
  font-weight: 600;
  transition: color 0.2s ease;
}

.auth-back:hover {
  color: var(--ch-primary);
}

.auth-main__hint {
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

.auth-card {
  width: min(440px, 100%);
  margin: auto;
  padding: 28px 0;
}

.auth-card:has(.register-form) {
  width: min(620px, 100%);
}

.auth-card h2 {
  margin-top: 10px;
  font-size: clamp(27px, 3vw, 34px);
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.auth-card__description {
  margin-top: 10px;
  color: var(--ch-muted);
  font-size: 14px;
}

.auth-card :deep(.el-form) {
  margin-top: 28px;
}

.auth-card :deep(.el-form-item) {
  margin-bottom: 20px;
}

.auth-card :deep(.el-input__wrapper) {
  min-height: 46px;
  border-radius: 11px;
  background: #fbfcff;
}

.auth-main__footer {
  text-align: center;
  color: var(--ch-muted-light);
  font-size: 11.5px;
}

@media (max-width: 1080px) {
  .auth-layout {
    grid-template-columns: minmax(0, 1fr) minmax(420px, 0.95fr);
  }

  .auth-aside {
    padding: 32px;
  }

  .auth-feature-list {
    display: none;
  }

  .auth-main {
    padding: 28px 32px 20px;
  }
}

@media (max-width: 800px) {
  .auth-layout {
    display: block;
  }

  .auth-aside {
    min-height: 180px;
    padding: 26px 24px;
  }

  .auth-aside__content {
    padding: 32px 0 12px;
  }

  .auth-aside__content h1 {
    font-size: 30px;
  }

  .auth-aside__content > p,
  .auth-metrics,
  .auth-aside__copyright {
    display: none;
  }

  .auth-main {
    min-height: calc(100vh - 180px);
    padding: 22px 24px 18px;
  }

  .auth-main__top {
    margin-bottom: 18px;
  }

  .auth-card {
    margin: 0 auto auto;
    padding: 10px 0 30px;
  }
}
</style>
