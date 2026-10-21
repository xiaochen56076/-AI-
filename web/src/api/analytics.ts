import { api, unwrap } from './http'
import type { ActivityStatistics, Dashboard } from '@/types'

export function getActivityStatistics(activityId: number) {
  return unwrap<ActivityStatistics>(api.get(`/activities/${activityId}/statistics`))
}

export function getDashboard() {
  return unwrap<Dashboard>(api.get('/admin/dashboard'))
}
