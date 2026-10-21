import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as authApi from '@/api/auth'
import type { RegisterPayload } from '@/api/auth'
import { clearTokens, loadTokens, saveTokens } from '@/api/http'
import type { AuthPayload, User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const initialized = ref(false)
  const loading = ref(false)

  const isAuthenticated = computed(() => Boolean(user.value))
  const permissions = computed(() => user.value?.permissions ?? [])
  const roles = computed(() => user.value?.roles ?? [])
  const displayName = computed(() => user.value?.display_name || user.value?.real_name || '')

  function hasPermission(permission: string | string[]) {
    const required = Array.isArray(permission) ? permission : [permission]
    if (!required.length) return true
    return required.some((item) => permissions.value.includes(item))
  }

  function hasRole(role: string) {
    return roles.value.some((item) => item.code === role)
  }

  const consoleEntry = computed(() => {
    if (hasPermission('analytics:global')) return '/console/dashboard'
    if (hasPermission('activity:audit')) return '/console/audit'
    if (hasPermission('activity:create')) return '/console/activities'
    if (hasPermission('user:manage')) return '/console/users'
    if (hasPermission('dict:manage')) return '/console/dictionaries'
    return null
  })

  const canUseConsole = computed(() => Boolean(consoleEntry.value))

  function applyAuth(payload: AuthPayload) {
    saveTokens({ access: payload.access, refresh: payload.refresh })
    user.value = payload.user
    initialized.value = true
  }

  async function bootstrap() {
    if (initialized.value) return
    const tokens = loadTokens()
    if (!tokens) {
      initialized.value = true
      return
    }
    try {
      user.value = await authApi.fetchMe()
    } catch {
      clearTokens()
      user.value = null
    } finally {
      initialized.value = true
    }
  }

  async function login(studentNo: string, password: string) {
    loading.value = true
    try {
      const payload = await authApi.login(studentNo.trim(), password)
      applyAuth(payload)
      return payload
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterPayload) {
    loading.value = true
    try {
      const result = await authApi.register(payload)
      applyAuth(result)
      return result
    } finally {
      loading.value = false
    }
  }

  async function refreshUser() {
    if (!loadTokens()) return null
    user.value = await authApi.fetchMe()
    return user.value
  }

  async function updateProfile(payload: Partial<User>) {
    const updated = await authApi.updateProfile(payload)
    user.value = updated
    return updated
  }

  async function logout() {
    const tokens = loadTokens()
    try {
      if (tokens) await authApi.logout(tokens.refresh)
    } catch {
      // 即使服务端注销失败，也清理本地会话
    } finally {
      clearTokens()
      user.value = null
      initialized.value = true
    }
  }

  return {
    user,
    initialized,
    loading,
    isAuthenticated,
    permissions,
    roles,
    displayName,
    hasPermission,
    hasRole,
    consoleEntry,
    canUseConsole,
    bootstrap,
    login,
    register,
    refreshUser,
    updateProfile,
    logout,
  }
})
