export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
  request_id: string
}

export interface Paginated<T> {
  total: number
  page: number
  page_size: number
  results: T[]
}

export interface RoleBrief {
  code: string
  name: string
}

export interface User {
  id: number
  student_no: string
  real_name: string
  nickname: string
  display_name: string
  avatar_url: string
  email: string
  phone: string
  college: string
  major: string
  grade: number | null
  status: number
  roles: RoleBrief[]
  permissions: string[]
  is_staff: boolean
  last_login_at: string | null
  created_at: string
}

export interface AuthPayload {
  access: string
  refresh: string
  expires_in: number
  user: User
}

export interface RefreshPayload {
  access: string
  refresh?: string
  expires_in?: number
}

export interface Category {
  id: number
  name: string
  slug: string
  icon: string
  color: string
  sort_order: number
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface Tag {
  id: number
  name: string
  color: string
  is_active?: boolean
  created_at?: string
}

export interface Club {
  id: number
  name: string
  logo_url: string
}

export interface OrganizerBrief {
  id: number
  real_name: string
  display_name: string
  college: string
  avatar_url: string
}

export interface ActivityBrief {
  id: number
  title: string
  summary: string
  cover_url: string
  location: string
  start_time: string
  end_time: string
  signup_start: string
  signup_end: string
  capacity: number
  signup_count: number
  waitlist_count: number
  remaining: number
  waitlist_enabled: boolean
  waitlist_limit: number
  checkin_mode: number
  checkin_mode_text: string
  status: number
  status_text: string
  view_count: number
  is_signup_open: boolean
  is_favorited: boolean
  category: Category
  tags: Tag[]
  club: Club
  organizer: OrganizerBrief
  created_at: string
}

export interface AuditRecord {
  id: number
  action: number
  action_text: string
  comment: string
  auditor_name: string
  created_at: string
}

export interface MySignupSummary {
  id: number
  status: number
  status_text: string
  queue_no: number | null
  checked_in: boolean
}

export interface ActivityDetail extends ActivityBrief {
  description: string
  cancel_reason: string
  updated_at: string
  can_manage: boolean
  can_submit: boolean
  can_audit: boolean
  audit_records: AuditRecord[]
  checkin_open: boolean
  checkin_window_start: string
  checkin_window_end: string
  checked_in_count: number
  my_signup: MySignupSummary | null
}

export interface ActivityPayload {
  title: string
  summary?: string
  description?: string
  cover_url?: string
  location: string
  start_time: string
  end_time: string
  signup_start: string
  signup_end: string
  capacity: number
  waitlist_enabled?: boolean
  waitlist_limit?: number
  checkin_mode?: number
  category_id: number
  tag_ids?: number[]
}

export interface Signup {
  id: number
  status: number
  status_text: string
  queue_no: number | null
  queue_position: number | null
  remark: string
  signup_at: string
  cancel_at: string | null
  checked_in_at: string | null
  checkin_method: number | null
  checkin_method_text: string | null
  user: {
    id: number
    student_no: string
    real_name: string
    nickname: string
    college: string
    major: string
    grade: number | null
    avatar_url: string
  }
}

export interface MySignup {
  id: number
  status: number
  status_text: string
  queue_no: number | null
  queue_position: number | null
  signup_at: string
  cancel_at: string | null
  checked_in_at: string | null
  checkin_method_text: string | null
  activity: ActivityBrief
}

export interface SignupResult {
  signup_id: number
  status: number
  status_text: string
  activity_id: number
  remaining: number
  position: number | null
}

export interface CheckinCode {
  activity_id: number
  code: string
  qr_content: string
  expires_at: string | null
  server_time: string
  checkin_mode: number
  checkin_mode_text: string
  checkin_window_start: string
  checkin_window_end: string
  checked_in_count: number
  signup_count: number
}

export interface CheckinResult {
  checkin_id: number
  activity_id: number
  signup_id: number
  student_no: string
  real_name: string
  checkin_method: number
  checkin_method_text: string
  checked_in_at: string
  checked_in_count: number
}

export interface Notification {
  id: number
  type: number
  type_text: string
  title: string
  content: string
  activity_id: number | null
  activity_title: string | null
  is_read: boolean
  read_at: string | null
  created_at: string
}

export interface RateSummary {
  fill_rate: number
  checkin_rate: number
  waitlist_promotion_rate: number
  view_conversion_rate: number
}

export interface DistributionItem {
  name: string
  value: number
}

export interface ActivityStatistics {
  activity: {
    id: number
    title: string
    status: number
    status_text: string
    capacity: number
    view_count: number
  }
  counts: {
    total: number
    success: number
    waitlist: number
    cancelled: number
    checked_in: number
    no_show: number
    waitlisted_ever: number
    promoted: number
    signup_count: number
    waitlist_count: number
  }
  rates: RateSummary
  checkin_method_distribution: DistributionItem[]
  college_distribution: DistributionItem[]
  grade_distribution: DistributionItem[]
  signup_trend: { date: string; value: number }[]
}

export interface Dashboard {
  generated_at: string
  totals: {
    users: number
    clubs: number
    categories: number
    activities: number
    signups: number
    checked_in: number
    no_show: number
    waitlist: number
  }
  activity_status: {
    total: number
    draft: number
    pending: number
    published: number
    ended: number
    cancelled: number
    rejected: number
  }
  signup_status: {
    total: number
    success: number
    checked_in: number
    no_show: number
    waitlist: number
  }
  rates: { checkin_rate: number }
  status_distribution: { status: number; name: string; value: number }[]
  popular_categories: {
    id: number
    name: string
    color: string
    activity_count: number
    participant_count: number
  }[]
  weekly_trend: { week: string; activities: number; signups: number }[]
}

export interface ActivityQuery {
  keyword?: string
  category?: string
  tag?: number | string
  scope?: 'upcoming' | 'past' | 'all'
  sort?: 'start_time' | 'latest' | 'hot' | 'deadline'
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export interface MySignupQuery {
  group?: 'upcoming' | 'waitlist' | 'attended' | 'cancelled'
  page?: number
  page_size?: number
}

export interface RosterQuery {
  status?: number | string
  keyword?: string
  page?: number
  page_size?: number
}

export interface NotificationQuery {
  status?: 'unread' | 'read'
  type?: number
  keyword?: string
  page?: number
  page_size?: number
}

export interface AdminUserQuery {
  keyword?: string
  role?: string
  status?: number | string
  page?: number
  page_size?: number
}
