import { api, unwrap } from './http'
import type {
  AdminUserQuery,
  Category,
  Paginated,
  RoleBrief,
  Tag,
  User,
} from '@/types'

export function listUsers(params: AdminUserQuery = {}) {
  return unwrap<Paginated<User>>(api.get('/admin/users', { params }))
}

export function listRoles() {
  return unwrap<RoleBrief[]>(api.get('/admin/roles'))
}

export function updateUser(
  id: number,
  payload: { status?: number; roles?: string[] },
) {
  return unwrap<User>(api.patch(`/admin/users/${id}`, payload))
}

export function listAdminCategories() {
  return unwrap<Category[]>(api.get('/admin/categories'))
}

export function createCategory(payload: Partial<Category>) {
  return unwrap<Category>(api.post('/admin/categories', payload))
}

export function updateCategory(id: number, payload: Partial<Category>) {
  return unwrap<Category>(api.patch(`/admin/categories/${id}`, payload))
}

export function listAdminTags() {
  return unwrap<Tag[]>(api.get('/admin/tags'))
}

export function createTag(payload: Partial<Tag>) {
  return unwrap<Tag>(api.post('/admin/tags', payload))
}

export function updateTag(id: number, payload: Partial<Tag>) {
  return unwrap<Tag>(api.patch(`/admin/tags/${id}`, payload))
}
