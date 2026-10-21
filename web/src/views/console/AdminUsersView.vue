<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Lock,
  Search,
  Setting,
  User,
} from '@element-plus/icons-vue'

import { listRoles, listUsers, updateUser } from '@/api/admin'
import EmptyState from '@/components/EmptyState.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useAuthStore } from '@/stores/auth'
import type { RoleBrief, User as UserModel } from '@/types'
import { formatDateTime, roleLabel } from '@/utils/format'

const auth = useAuthStore()

const loading = ref(true)
const rows = ref<UserModel[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const keyword = ref('')
const appliedKeyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const roles = ref<RoleBrief[]>([])

const dialogVisible = ref(false)
const editing = ref<UserModel | null>(null)
const saving = ref(false)
const editForm = reactive<{ status: number; roles: string[] }>({ status: 0, roles: [] })

const roleDescriptions: Record<string, string> = {
  STUDENT: '浏览活动、报名、候补与签到',
  ORGANIZER: '创建活动、管理报名名单与签到',
  AUDITOR: '审核活动，处理通过或驳回',
  ADMIN: '平台全站数据、用户与字典管理',
}

const roleTone: Record<string, string> = {
  STUDENT: 'role-student',
  ORGANIZER: 'role-organizer',
  AUDITOR: 'role-auditor',
  ADMIN: 'role-admin',
}

async function loadRoles() {
  try {
    roles.value = await listRoles()
  } catch {
    roles.value = []
  }
}

async function load() {
  loading.value = true
  try {
    const data = await listUsers({
      keyword: appliedKeyword.value || undefined,
      role: roleFilter.value || undefined,
      status: statusFilter.value === '' ? undefined : Number(statusFilter.value),
      page: page.value,
      page_size: pageSize,
    })
    rows.value = data.results
    total.value = data.total
  } catch {
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  appliedKeyword.value = keyword.value.trim()
  page.value = 1
  load()
}

function resetFilters() {
  keyword.value = ''
  appliedKeyword.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  page.value = 1
  load()
}

function handlePageChange(value: number) {
  page.value = value
  load()
}

function openEditor(user: UserModel) {
  editing.value = user
  editForm.status = user.status
  editForm.roles = user.roles.map((role) => role.code)
  dialogVisible.value = true
}

async function submitEdit() {
  if (!editing.value) return
  if (!editForm.roles.length) {
    ElMessage.warning('用户至少需要一个角色')
    return
  }
  saving.value = true
  try {
    const updated = await updateUser(editing.value.id, {
      status: editForm.status,
      roles: editForm.roles,
    })
    ElMessage.success(`${updated.display_name} 的账号设置已更新`)
    dialogVisible.value = false
    editing.value = null
    await load()
    if (updated.id === auth.user?.id) {
      await auth.refreshUser()
    }
  } catch {
    // 接口错误由拦截器提示
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadRoles(), load()])
})
</script>

<template>
  <div class="users-page" v-loading="loading">
    <div class="page-head">
      <div>
        <span class="eyebrow">Account governance</span>
        <h1>用户管理</h1>
        <p>查看平台账号，分配角色并处理账号禁用状态。</p>
      </div>
      <div class="user-total">
        <el-icon><User /></el-icon>
        共 {{ total }} 个账号
      </div>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索学号、姓名或昵称"
        :prefix-icon="Search"
        clearable
        style="width: 260px"
        @keyup.enter="applyFilters"
        @clear="applyFilters"
      />
      <el-select v-model="roleFilter" placeholder="全部角色" clearable style="width: 150px">
        <el-option v-for="role in roles" :key="role.code" :label="role.name" :value="role.code" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 140px">
        <el-option label="正常" :value="0" />
        <el-option label="已禁用" :value="1" />
      </el-select>
      <el-button type="primary" @click="applyFilters">筛选</el-button>
      <el-button text @click="resetFilters">重置</el-button>
      <div class="filter-spacer"></div>
      <span class="filter-hint">角色变更将在用户下次请求时生效</span>
    </div>

    <div class="table-card">
      <el-table v-if="rows.length" :data="rows" style="width: 100%">
        <el-table-column label="学生" min-width="220">
          <template #default="{ row }">
            <div class="user-cell">
              <UserAvatar :name="row.real_name" :src="row.avatar_url" :size="38" />
              <div>
                <div class="user-cell__name">
                  <strong>{{ row.real_name }}</strong>
                  <span v-if="row.id === auth.user?.id" class="self-tag">当前账号</span>
                </div>
                <span>{{ row.student_no }} · {{ row.nickname || '未设置昵称' }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="学院 / 专业" min-width="190">
          <template #default="{ row }">
            <div class="dept-cell">
              <span>{{ row.college || '未填写学院' }}</span>
              <small>{{ row.major || '未填写专业' }}<template v-if="row.grade"> · {{ row.grade }} 级</template></small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" min-width="190">
          <template #default="{ row }">
            <div class="role-chips">
              <span
                v-for="role in row.roles"
                :key="role.code"
                class="role-chip"
                :class="roleTone[role.code]"
              >
                {{ roleLabel(role.code) }}
              </span>
              <span v-if="!row.roles.length" class="muted-light">未分配</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span class="status-pill" :class="row.status === 0 ? 'is-published' : 'is-cancelled'">
              {{ row.status === 0 ? '正常' : '已禁用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="最近登录" min-width="150">
          <template #default="{ row }">
            <span class="table-muted">
              {{ row.last_login_at ? formatDateTime(row.last_login_at) : '从未登录' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" round :icon="Setting" @click="openEditor(row)">管理</el-button>
          </template>
        </el-table-column>
      </el-table>

      <EmptyState
        v-else-if="!loading"
        title="没有匹配的用户"
        description="尝试调整搜索关键词或筛选条件。"
      >
        <el-button round @click="resetFilters">重置筛选</el-button>
      </EmptyState>
    </div>

    <div v-if="total > pageSize" class="pager-row">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      title="账号权限管理"
      width="min(560px, 94vw)"
      :close-on-click-modal="false"
    >
      <template v-if="editing">
        <div class="editor-user">
          <UserAvatar :name="editing.real_name" :src="editing.avatar_url" :size="46" />
          <div>
            <strong>{{ editing.real_name }}</strong>
            <span>{{ editing.student_no }} · {{ editing.college || '未填写学院' }}</span>
          </div>
          <span
            class="status-pill"
            :class="editing.status === 0 ? 'is-published' : 'is-cancelled'"
          >
            {{ editing.status === 0 ? '正常' : '已禁用' }}
          </span>
        </div>

        <div class="editor-section">
          <div class="editor-section__head">
            <h3>账号状态</h3>
            <span>禁用后该账号将无法登录平台</span>
          </div>
          <el-radio-group v-model="editForm.status">
            <el-radio-button :value="0">正常使用</el-radio-button>
            <el-radio-button :value="1">禁用账号</el-radio-button>
          </el-radio-group>
          <p v-if="editing.id === auth.user?.id" class="editor-warning">
            <el-icon><Lock /></el-icon>
            不能禁用当前登录账号，也不能移除自己的管理员角色。
          </p>
        </div>

        <div class="editor-section">
          <div class="editor-section__head">
            <h3>角色分配</h3>
            <span>至少保留一个角色</span>
          </div>
          <el-checkbox-group v-model="editForm.roles" class="role-options">
            <el-checkbox
              v-for="role in roles"
              :key="role.code"
              :value="role.code"
              class="role-option"
            >
              <div class="role-option__content">
                <strong>{{ role.name }}</strong>
                <span>{{ roleDescriptions[role.code] || role.code }}</span>
              </div>
            </el-checkbox>
          </el-checkbox-group>
        </div>
      </template>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitEdit">保存设置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: 22px;
  min-height: 460px;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.page-head h1 {
  margin-top: 10px;
  font-size: 30px;
  letter-spacing: -0.03em;
}

.page-head p {
  margin-top: 6px;
  color: var(--ch-muted);
  font-size: 14px;
}

.user-total {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 16px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--ch-border);
  color: var(--ch-muted);
  font-size: 12px;
  white-space: nowrap;
}

.filter-hint {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-cell > div {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-cell__name {
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-cell strong {
  font-size: 13px;
  font-weight: 650;
}

.user-cell span {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.self-tag {
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary) !important;
  font-size: 10px !important;
  font-weight: 600;
}

.dept-cell {
  display: flex;
  flex-direction: column;
  font-size: 13px;
}

.dept-cell small {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.role-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.role-chip {
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.role-student {
  background: rgba(102, 112, 138, 0.1);
  color: #5b6885;
}

.role-organizer {
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
}

.role-auditor {
  background: #fff6e6;
  color: #b77400;
}

.role-admin {
  background: #f1edff;
  color: #7a5af8;
}

.table-muted {
  color: var(--ch-muted);
  font-size: 12px;
}

.muted-light {
  color: var(--ch-muted-light);
  font-size: 12px;
}

.editor-user {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 20px;
  border-radius: 14px;
  background: #fafbfe;
  border: 1px solid #eff2f9;
}

.editor-user div {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.editor-user strong {
  font-size: 14px;
}

.editor-user span {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.editor-section {
  margin-bottom: 22px;
}

.editor-section__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.editor-section__head h3 {
  font-size: 14px;
}

.editor-section__head span {
  color: var(--ch-muted-light);
  font-size: 11px;
}

.editor-warning {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 9px 12px;
  border-radius: 10px;
  background: #fff6e6;
  color: #a56a00;
  font-size: 11px;
}

.role-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

.role-option {
  display: flex;
  align-items: flex-start;
  width: 100%;
  height: auto;
  margin-right: 0;
  padding: 12px 14px;
  border: 1px solid var(--ch-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.role-option.is-checked {
  border-color: var(--ch-primary);
  background: var(--ch-primary-soft);
}

.role-option :deep(.el-checkbox__label) {
  width: 100%;
  padding-left: 8px;
  white-space: normal;
}

.role-option :deep(.el-checkbox__input) {
  margin-top: 2px;
}

.role-option__content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.role-option__content strong {
  font-size: 13px;
  color: var(--ch-ink);
}

.role-option__content span {
  color: var(--ch-muted);
  font-size: 11px;
  line-height: 1.5;
}

@media (max-width: 760px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-bar :deep(.el-input),
  .filter-bar :deep(.el-select) {
    width: 100% !important;
  }

  .role-options {
    grid-template-columns: minmax(0, 1fr);
  }

  .filter-hint {
    display: none;
  }
}
</style>
