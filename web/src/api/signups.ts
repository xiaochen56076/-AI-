import { api, unwrap } from './http'
import type {
  CheckinCode,
  CheckinResult,
  MySignup,
  MySignupQuery,
  Paginated,
  RosterQuery,
  Signup,
  SignupResult,
} from '@/types'

export function signupForActivity(activityId: number, remark = '') {
  return unwrap<SignupResult>(api.post(`/activities/${activityId}/signup`, { remark }))
}

export function cancelSignup(activityId: number) {
  return unwrap<{
    signup_id: number
    status: number
    status_text: string
    promoted_signup_id: number | null
  }>(api.delete(`/activities/${activityId}/signup`))
}

export function mySignups(params: MySignupQuery = {}) {
  return unwrap<Paginated<MySignup>>(api.get('/my/signups', { params }))
}

export function activityRoster(activityId: number, params: RosterQuery = {}) {
  return unwrap<Paginated<Signup>>(api.get(`/activities/${activityId}/signups`, { params }))
}

export function exportRoster(activityId: number) {
  return api.get<Blob>(`/activities/${activityId}/signups/export`, {
    responseType: 'blob',
  })
}

export function getCheckinCode(activityId: number) {
  return unwrap<CheckinCode>(api.post(`/activities/${activityId}/checkin-code`))
}

export function submitCheckin(
  activityId: number,
  code: string,
  options: { latitude?: number; longitude?: number; device_info?: string } = {},
) {
  return unwrap<CheckinResult>(
    api.post('/checkin', {
      activity_id: activityId,
      code,
      ...options,
    }),
  )
}

export function manualCheckin(activityId: number, studentNo: string, reason: string) {
  return unwrap<CheckinResult>(
    api.post(`/activities/${activityId}/checkin-manual`, {
      student_no: studentNo,
      reason,
    }),
  )
}
