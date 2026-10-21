import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import dayjsRelativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(dayjsRelativeTime)
dayjs.locale('zh-cn')

export const DATE_TIME_FORMAT = 'YYYY-MM-DD HH:mm'
export const DATE_FORMAT = 'YYYY-MM-DD'

export function formatDateTime(value?: string | null, fallback = '—') {
  if (!value) return fallback
  return dayjs(value).format(DATE_TIME_FORMAT)
}

export function formatDate(value?: string | null, fallback = '—') {
  if (!value) return fallback
  return dayjs(value).format(DATE_FORMAT)
}

export function formatMonthDay(value?: string | null) {
  if (!value) return '—'
  return dayjs(value).format('MM月DD日')
}

export function formatWeekday(value?: string | null) {
  if (!value) return ''
  return dayjs(value).format('ddd')
}

export function formatTimeRange(start?: string | null, end?: string | null) {
  if (!start || !end) return '时间待定'
  const startAt = dayjs(start)
  const endAt = dayjs(end)
  if (startAt.isSame(endAt, 'day')) {
    return `${startAt.format('YYYY-MM-DD HH:mm')} - ${endAt.format('HH:mm')}`
  }
  return `${startAt.format('MM-DD HH:mm')} - ${endAt.format('MM-DD HH:mm')}`
}

export function relativeTime(value?: string | null) {
  if (!value) return ''
  return dayjs(value).fromNow()
}

export function countdownText(target?: string | null, now = Date.now()) {
  if (!target) return ''
  const diff = dayjs(target).valueOf() - now
  if (diff <= 0) return '已开始'
  const seconds = Math.floor(diff / 1000)
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (days > 0) return `${days} 天 ${hours} 小时`
  if (hours > 0) return `${hours} 小时 ${minutes} 分`
  if (minutes > 0) return `${minutes} 分 ${secs} 秒`
  return `${secs} 秒`
}

export function formatPercent(rate?: number | null, digits = 1) {
  if (rate === null || rate === undefined) return '0%'
  return `${(rate * 100).toFixed(digits)}%`
}

export function formatNumber(value?: number | null) {
  return (value ?? 0).toLocaleString('zh-CN')
}

export function toDateTimeValue(value?: string | null) {
  if (!value) return ''
  return dayjs(value).format('YYYY-MM-DDTHH:mm:ssZ')
}

export function toApiDateTime(value?: string | null) {
  if (!value) return undefined
  return dayjs(value).toISOString()
}

export function isBetween(value: string | null | undefined, start?: string | null, end?: string | null) {
  if (!value) return false
  const at = dayjs(value)
  return (!start || !at.isBefore(dayjs(start))) && (!end || !at.isAfter(dayjs(end)))
}

export interface StatusMeta {
  label: string
  type: 'primary' | 'success' | 'warning' | 'info' | 'danger'
  className: string
}

const ACTIVITY_STATUS: Record<number, StatusMeta> = {
  0: { label: '草稿', type: 'info', className: 'is-draft' },
  1: { label: '待审核', type: 'warning', className: 'is-pending' },
  2: { label: '已发布', type: 'success', className: 'is-published' },
  3: { label: '已结束', type: 'info', className: 'is-ended' },
  4: { label: '已取消', type: 'danger', className: 'is-cancelled' },
  5: { label: '已驳回', type: 'danger', className: 'is-rejected' },
}

export function activityStatusMeta(status: number): StatusMeta {
  return ACTIVITY_STATUS[status] ?? { label: '未知', type: 'info', className: 'is-unknown' }
}

const SIGNUP_STATUS: Record<number, StatusMeta> = {
  0: { label: '候补中', type: 'warning', className: 'is-waitlist' },
  1: { label: '报名成功', type: 'success', className: 'is-success' },
  2: { label: '已取消', type: 'info', className: 'is-cancelled' },
  3: { label: '已签到', type: 'primary', className: 'is-checked' },
  4: { label: '未签到', type: 'danger', className: 'is-noshow' },
}

export function signupStatusMeta(status: number): StatusMeta {
  return SIGNUP_STATUS[status] ?? { label: '未知', type: 'info', className: 'is-unknown' }
}

export interface NotificationMeta {
  label: string
  icon: string
  color: string
  background: string
}

const NOTIFICATION_TYPES: Record<number, NotificationMeta> = {
  0: { label: '系统通知', icon: 'Bell', color: '#3757e8', background: '#eef2ff' },
  1: { label: '报名成功', icon: 'CircleCheck', color: '#0f9f6e', background: '#e8f8f2' },
  2: { label: '候补提醒', icon: 'Clock', color: '#d98a00', background: '#fff6e6' },
  3: { label: '候补转正', icon: 'Promotion', color: '#0f9f6e', background: '#e8f8f2' },
  4: { label: '活动提醒', icon: 'AlarmClock', color: '#7a5af8', background: '#f1edff' },
  5: { label: '活动取消', icon: 'Warning', color: '#e0484b', background: '#fdecec' },
  6: { label: '审核结果', icon: 'Stamp', color: '#3757e8', background: '#eef2ff' },
  7: { label: '签到成功', icon: 'Select', color: '#0f9f6e', background: '#e8f8f2' },
}

export function notificationMeta(type: number): NotificationMeta {
  return NOTIFICATION_TYPES[type] ?? NOTIFICATION_TYPES[0]
}

export function checkinModeLabel(mode: number) {
  return ['无需签到', '静态码签到', '动态码签到'][mode] ?? '未知'
}

export function roleLabel(code: string) {
  const map: Record<string, string> = {
    STUDENT: '学生',
    ORGANIZER: '主办方',
    AUDITOR: '审核员',
    ADMIN: '管理员',
  }
  return map[code] ?? code
}

export function withAlpha(hex: string, alpha: number) {
  const normalized = hex.replace('#', '')
  if (normalized.length !== 6) return `rgba(55, 87, 232, ${alpha})`
  const r = parseInt(normalized.slice(0, 2), 16)
  const g = parseInt(normalized.slice(2, 4), 16)
  const b = parseInt(normalized.slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

export function categoryGradient(color?: string | null) {
  const base = color || '#3757e8'
  return `linear-gradient(135deg, ${withAlpha(base, 0.96)} 0%, ${withAlpha(base, 0.62)} 58%, #101a33 130%)`
}

export function initialOf(name?: string | null) {
  if (!name) return 'C'
  return name.trim().slice(0, 1).toUpperCase()
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
