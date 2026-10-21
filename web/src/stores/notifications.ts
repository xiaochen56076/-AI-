import { ref } from 'vue'
import { defineStore } from 'pinia'

import * as notificationApi from '@/api/notifications'
import { useAuthStore } from '@/stores/auth'

export const useNotificationsStore = defineStore('notifications', () => {
  const unread = ref(0)
  const loading = ref(false)
  let pollTimer: number | null = null

  async function refreshUnread() {
    const auth = useAuthStore()
    if (!auth.isAuthenticated) {
      unread.value = 0
      return
    }
    loading.value = true
    try {
      const result = await notificationApi.getUnreadCount()
      unread.value = result.unread
    } catch {
      // 静默失败，避免轮询打扰用户
    } finally {
      loading.value = false
    }
  }

  async function markRead(id: number) {
    const result = await notificationApi.markNotificationRead(id)
    unread.value = result.unread
    return result
  }

  async function markAllRead() {
    const result = await notificationApi.markAllNotificationsRead()
    unread.value = result.unread
    return result
  }

  function setUnread(value: number) {
    unread.value = Math.max(0, value)
  }

  function startPolling(interval = 60000) {
    stopPolling()
    void refreshUnread()
    pollTimer = window.setInterval(() => {
      void refreshUnread()
    }, interval)
  }

  function stopPolling() {
    if (pollTimer !== null) {
      window.clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    unread,
    loading,
    refreshUnread,
    markRead,
    markAllRead,
    setUnread,
    startPolling,
    stopPolling,
  }
})
