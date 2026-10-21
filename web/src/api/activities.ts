import { api, unwrap } from './http'
import type {
  ActivityBrief,
  ActivityDetail,
  ActivityPayload,
  ActivityQuery,
  Category,
  Paginated,
  Tag,
} from '@/types'

export function listActivities(params: ActivityQuery = {}) {
  return unwrap<Paginated<ActivityBrief>>(api.get('/activities', { params }))
}

export function getActivity(id: number) {
  return unwrap<ActivityDetail>(api.get(`/activities/${id}`))
}

export function listCategories() {
  return unwrap<Category[]>(api.get('/categories'))
}

export function listTags() {
  return unwrap<Tag[]>(api.get('/tags'))
}

export function createActivity(payload: ActivityPayload) {
  return unwrap<ActivityDetail>(api.post('/activities', payload))
}

export function updateActivity(id: number, payload: Partial<ActivityPayload>) {
  return unwrap<ActivityDetail>(api.patch(`/activities/${id}`, payload))
}

export function submitActivity(id: number) {
  return unwrap<ActivityDetail>(api.post(`/activities/${id}/submit`))
}

export function cancelActivity(id: number, reason: string) {
  return unwrap<ActivityDetail>(api.post(`/activities/${id}/cancel`, { reason }))
}

export function favoriteActivity(id: number) {
  return unwrap<{ is_favorited: boolean }>(api.post(`/activities/${id}/favorite`))
}

export function unfavoriteActivity(id: number) {
  return unwrap<{ is_favorited: boolean }>(api.delete(`/activities/${id}/favorite`))
}

export function myActivities(
  params: { status?: string | number; keyword?: string; page?: number; page_size?: number } = {},
) {
  return unwrap<Paginated<ActivityBrief>>(api.get('/my/activities', { params }))
}

export function myFavorites(params: { page?: number } = {}) {
  return unwrap<Paginated<ActivityBrief>>(api.get('/my/favorites', { params }))
}

export function listAudits(
  params: { status?: string | number; keyword?: string; page?: number; page_size?: number } = {},
) {
  return unwrap<Paginated<ActivityDetail>>(api.get('/admin/audits', { params }))
}

export function reviewActivity(id: number, action: number, comment = '') {
  return unwrap<ActivityDetail>(api.post(`/admin/audits/${id}`, { action, comment }))
}
