import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

import type { ApiEnvelope, RefreshPayload } from '@/types'

const TOKEN_KEY = 'campushub.tokens'

export interface TokenPair {
  access: string
  refresh: string
}

export class ApiError extends Error {
  code: number
  status: number
  data: unknown

  constructor(message: string, code = 0, status = 0, data: unknown = null) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.data = data
  }
}

export function loadTokens(): TokenPair | null {
  const raw = localStorage.getItem(TOKEN_KEY)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as TokenPair
    return parsed.access && parsed.refresh ? parsed : null
  } catch {
    return null
  }
}

export function saveTokens(tokens: TokenPair) {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens))
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
}

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 20000,
})

let refreshPromise: Promise<string> | null = null

async function requestNewAccessToken(): Promise<string> {
  const tokens = loadTokens()
  if (!tokens?.refresh) {
    throw new ApiError('登录状态已失效', 20001, 401)
  }
  const response = await axios.post<ApiEnvelope<RefreshPayload>>('/api/v1/auth/refresh', {
    refresh: tokens.refresh,
  })
  if (response.data.code !== 0) {
    throw new ApiError(response.data.message, response.data.code, 401)
  }
  const next: TokenPair = {
    access: response.data.data.access,
    refresh: response.data.data.refresh || tokens.refresh,
  }
  saveTokens(next)
  return next.access
}

function redirectToLogin() {
  clearTokens()
  if (!window.location.pathname.startsWith('/login')) {
    const redirect = encodeURIComponent(window.location.pathname + window.location.search)
    window.location.assign(`/login?expired=1&redirect=${redirect}`)
  }
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const tokens = loadTokens()
  if (tokens?.access) {
    config.headers.set('Authorization', `Bearer ${tokens.access}`)
  }
  return config
})

api.interceptors.response.use(
  (response: AxiosResponse) => {
    if (response.config.responseType === 'blob') return response
    const envelope = response.data as ApiEnvelope<unknown>
    if (envelope && typeof envelope.code === 'number' && envelope.code !== 0) {
      ElMessage.error(envelope.message || '操作失败')
      return Promise.reject(new ApiError(envelope.message, envelope.code, response.status, envelope.data))
    }
    return response
  },
  async (error: AxiosError<ApiEnvelope<unknown>>) => {
    const config = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    const status = error.response?.status ?? 0
    const message = error.response?.data?.message

    if (status === 401 && config && !config._retry) {
      const requestUrl = config.url || ''
      const isAuthRequest = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/refresh')
      if (!isAuthRequest) {
        config._retry = true
        try {
          refreshPromise = refreshPromise || requestNewAccessToken()
          const access = await refreshPromise
          config.headers.set('Authorization', `Bearer ${access}`)
          return api(config)
        } catch {
          redirectToLogin()
          ElMessage.error('登录已过期，请重新登录')
          return Promise.reject(new ApiError('登录已过期', 20001, 401))
        } finally {
          refreshPromise = null
        }
      }
    }

    if (status === 403) {
      ElMessage.error(message || '没有权限执行此操作')
    } else if (status === 401) {
      ElMessage.error(message || '学号或密码不正确')
    } else if (!error.response) {
      ElMessage.error('网络连接失败，请确认后端服务已启动')
    } else {
      ElMessage.error(message || '操作失败，请稍后重试')
    }

    return Promise.reject(
      new ApiError(message || error.message, error.response?.data?.code ?? 0, status, error.response?.data?.data)
    )
  },
)

export async function unwrap<T>(request: Promise<AxiosResponse<ApiEnvelope<T>>>): Promise<T> {
  const response = await request
  return response.data.data
}
