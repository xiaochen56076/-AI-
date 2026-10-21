<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'
import { RouterView } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'

const auth = useAuthStore()
const notifications = useNotificationsStore()

watch(
  () => auth.isAuthenticated,
  (authenticated) => {
    if (authenticated) {
      notifications.startPolling()
    } else {
      notifications.stopPolling()
      notifications.setUnread(0)
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => notifications.stopPolling())
</script>

<template>
  <RouterView v-slot="{ Component }">
    <Transition name="page-fade" mode="out-in">
      <component :is="Component" />
    </Transition>
  </RouterView>
</template>
