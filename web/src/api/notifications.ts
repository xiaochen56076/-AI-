import { api, unwrap } from './http'
import type { Notification, NotificationQuery, Paginated } from '@/types'

export function listNotifications(params: NotificationQuery = {}) {
  return unwrap<Paginated<Notification>>(api.get('/notifications', { params }))
}

export function getUnreadCount() {
  return unwrap<{ unread: number }>(api.get('/notifications/unread-count'))
}

export function markNotificationRead(id: number) {
  return unwrap<{ id: number; is_read: boolean; unread: number }>(
    api.post(`/notifications/${id}/read`),
  )
}

export function markAllNotificationsRead() {
  return unwrap<{ updated: number; unread: number }>(api.post('/notifications/read-all'))
}
