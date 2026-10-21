<script setup lang="ts">
import { computed } from 'vue'

import { initialOf } from '@/utils/format'

const props = withDefaults(
  defineProps<{
    name?: string
    src?: string
    size?: number
  }>(),
  {
    name: 'CampusHub',
    src: '',
    size: 36,
  },
)

const palette = [
  ['#3757e8', '#7a5af8'],
  ['#0f9f6e', '#22c7a0'],
  ['#f97316', '#fbbf24'],
  ['#e0484b', '#f47b8e'],
  ['#0ea5e9', '#22d3ee'],
]

const gradient = computed(() => {
  const seed = Array.from(props.name).reduce((sum, char) => sum + char.charCodeAt(0), 0)
  const pair = palette[seed % palette.length]
  return `linear-gradient(135deg, ${pair[0]}, ${pair[1]})`
})
</script>

<template>
  <el-avatar
    v-if="src"
    :size="size"
    :src="src"
    class="user-avatar"
    :alt="name"
  />
  <span
    v-else
    class="user-avatar user-avatar__fallback"
    :style="{ width: `${size}px`, height: `${size}px`, background: gradient, fontSize: `${Math.max(12, size * 0.38)}px` }"
  >
    {{ initialOf(name) }}
  </span>
</template>

<style scoped>
.user-avatar {
  flex: 0 0 auto;
}

.user-avatar__fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #fff;
  font-weight: 700;
  letter-spacing: 0.02em;
  user-select: none;
}
</style>
