<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    value: string | number
    icon?: string
    hint?: string
    tone?: 'primary' | 'success' | 'warning' | 'violet' | 'rose' | 'teal'
  }>(),
  {
    icon: 'DataLine',
    hint: '',
    tone: 'primary',
  },
)
</script>

<template>
  <div class="stat-card" :class="`tone-${tone}`">
    <div class="stat-card__icon">
      <el-icon><component :is="icon" /></el-icon>
    </div>
    <div class="stat-card__content">
      <span class="stat-card__label">{{ label }}</span>
      <strong class="stat-card__value">{{ value }}</strong>
      <span v-if="hint" class="stat-card__hint">{{ hint }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  display: flex;
  gap: 16px;
  padding: 22px;
  background: #fff;
  border: 1px solid var(--ch-border);
  border-radius: var(--ch-radius);
  box-shadow: 0 1px 2px rgba(16, 26, 51, 0.03);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--ch-shadow);
}

.stat-card__icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 46px;
  height: 46px;
  border-radius: 14px;
  font-size: 22px;
}

.stat-card__content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.stat-card__label {
  color: var(--ch-muted);
  font-size: 13px;
  font-weight: 500;
}

.stat-card__value {
  margin-top: 2px;
  font-size: 26px;
  line-height: 1.2;
  letter-spacing: -0.02em;
  font-weight: 750;
}

.stat-card__hint {
  margin-top: 4px;
  color: var(--ch-muted-light);
  font-size: 12px;
}

.tone-primary .stat-card__icon {
  color: #3757e8;
  background: #eef2ff;
}

.tone-success .stat-card__icon {
  color: #0f9f6e;
  background: #e8f8f2;
}

.tone-warning .stat-card__icon {
  color: #c07c00;
  background: #fff5e3;
}

.tone-violet .stat-card__icon {
  color: #7a5af8;
  background: #f1edff;
}

.tone-rose .stat-card__icon {
  color: #df5077;
  background: #fff0f4;
}

.tone-teal .stat-card__icon {
  color: #0d9488;
  background: #e6faf7;
}
</style>
