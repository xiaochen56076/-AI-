<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string
    description?: string
  }>(),
  {
    title: '这里还没有内容',
    description: '换个条件试试，或稍后再来看看。',
  },
)
</script>

<template>
  <div class="empty-state">
    <div class="empty-state__icon">
      <el-icon><Box /></el-icon>
    </div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <div v-if="$slots.default" class="empty-state__actions">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 64px 24px;
  border: 1px dashed var(--ch-border-strong);
  border-radius: var(--ch-radius);
  background: linear-gradient(180deg, #fff, #fafbff);
}

.empty-state__icon {
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  margin-bottom: 18px;
  border-radius: 20px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  font-size: 28px;
}

.empty-state h3 {
  font-size: 17px;
  font-weight: 700;
}

.empty-state p {
  max-width: 360px;
  margin-top: 8px;
  color: var(--ch-muted);
  font-size: 14px;
}

.empty-state__actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}
</style>
