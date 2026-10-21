import { api, unwrap } from './http'
import type { AuthPayload, User } from '@/types'

export interface RegisterPayload {
  student_no: string
  password: string
  confirm_password: string
  real_name: string
  nickname?: string
  email?: string
  phone?: string
  college?: string
  major?: string
  grade?: number | null
}

export function login(studentNo: string, password: string) {
  return unwrap<AuthPayload>(api.post('/auth/login', { student_no: studentNo, password }))
}

export function register(payload: RegisterPayload) {
  return unwrap<AuthPayload>(api.post('/auth/register', payload))
}

export function fetchMe() {
  return unwrap<User>(api.get('/users/me'))
}

export function updateProfile(payload: Partial<User>) {
  return unwrap<User>(api.patch('/users/me', payload))
}

export function changePassword(payload: {
  old_password: string
  new_password: string
  confirm_password: string
}) {
  return unwrap<null>(api.post('/users/me/password', payload))
}

export function logout(refresh: string) {
  return unwrap<null>(api.post('/auth/logout', { refresh }))
}
