<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Calendar,
  ChatDotRound,
  Iphone,
  Lock,
  Reading,
  School,
  User,
} from '@element-plus/icons-vue'

import UserAvatar from '@/components/UserAvatar.vue'
import { changePassword } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { formatDate, formatDateTime, roleLabel } from '@/utils/format'

const auth = useAuthStore()
const router = useRouter()

const activeTab = ref('profile')
const profileRef = ref<FormInstance>()
const passwordRef = ref<FormInstance>()
const savingProfile = ref(false)
const savingPassword = ref(false)

const profileForm = reactive({
  nickname: auth.user?.nickname ?? '',
  avatar_url: auth.user?.avatar_url ?? '',
  email: auth.user?.email ?? '',
  phone: auth.user?.phone ?? '',
  college: auth.user?.college ?? '',
  major: auth.user?.major ?? '',
  grade: auth.user?.grade ?? (null as number | null),
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const profileRules: FormRules = {
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  avatar_url: [
    {
      validator: (_rule, value: string, callback) => {
        if (value && !/^https?:\/\//.test(value)) callback(new Error('头像地址必须为 http(s) URL'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

const passwordRules: FormRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 64, message: '密码长度应为 8-64 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (value !== passwordForm.new_password) callback(new Error('两次输入的新密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

async function saveProfile() {
  const valid = await profileRef.value?.validate().catch(() => false)
  if (!valid) return
  savingProfile.value = true
  try {
    await auth.updateProfile({
      nickname: profileForm.nickname,
      avatar_url: profileForm.avatar_url,
      email: profileForm.email,
      phone: profileForm.phone,
      college: profileForm.college,
      major: profileForm.major,
      grade: profileForm.grade,
    })
    ElMessage.success('个人资料已更新')
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    savingProfile.value = false
  }
}

async function savePassword() {
  const valid = await passwordRef.value?.validate().catch(() => false)
  if (!valid) return
  savingPassword.value = true
  try {
    await changePassword({ ...passwordForm })
    ElMessage.success('密码已修改，请使用新密码重新登录')
    await auth.logout()
    await router.replace({ name: 'login' })
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    savingPassword.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <section class="page-hero">
      <div class="page-container">
        <span class="eyebrow">My account</span>
        <h1>个人中心</h1>
        <p>管理你的基础资料与账号安全，让活动组织方更好地认识你。</p>
      </div>
    </section>

    <section class="page-container page-block">
      <div class="profile-grid">
        <aside class="profile-card surface">
          <div class="profile-card__cover"></div>
          <div class="profile-card__avatar">
            <UserAvatar :name="auth.displayName" :src="auth.user?.avatar_url" :size="82" />
          </div>
          <div class="profile-card__body">
            <h2>{{ auth.displayName }}</h2>
            <span class="student-no">{{ auth.user?.student_no }}</span>
            <div class="role-row">
              <span v-for="role in auth.user?.roles" :key="role.code" class="role-pill">
                {{ roleLabel(role.code) }}
              </span>
            </div>

            <div class="profile-facts">
              <div>
                <span class="fact-icon"><el-icon><School /></el-icon></span>
                <div>
                  <span>学院</span>
                  <strong>{{ auth.user?.college || '未填写' }}</strong>
                </div>
              </div>
              <div>
                <span class="fact-icon"><el-icon><Reading /></el-icon></span>
                <div>
                  <span>专业</span>
                  <strong>{{ auth.user?.major || '未填写' }}</strong>
                </div>
              </div>
              <div>
                <span class="fact-icon"><el-icon><Calendar /></el-icon></span>
                <div>
                  <span>入学年级</span>
                  <strong>{{ auth.user?.grade ? `${auth.user.grade} 级` : '未填写' }}</strong>
                </div>
              </div>
              <div>
                <span class="fact-icon"><el-icon><ChatDotRound /></el-icon></span>
                <div>
                  <span>邮箱</span>
                  <strong>{{ auth.user?.email || '未填写' }}</strong>
                </div>
              </div>
              <div>
                <span class="fact-icon"><el-icon><Iphone /></el-icon></span>
                <div>
                  <span>手机号</span>
                  <strong>{{ auth.user?.phone || '未填写' }}</strong>
                </div>
              </div>
            </div>

            <div class="profile-card__footer">
              <span>加入于 {{ formatDate(auth.user?.created_at) }}</span>
              <span>最近登录 {{ formatDateTime(auth.user?.last_login_at) }}</span>
            </div>
          </div>
        </aside>

        <div class="profile-panel surface">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="个人资料" name="profile">
              <div class="panel-head">
                <div>
                  <h3>基础资料</h3>
                  <p>昵称会展示在活动页面，其他信息仅用于活动组织与通知。</p>
                </div>
              </div>

              <el-alert
                type="info"
                :closable="false"
                show-icon
                title="学号与真实姓名是活动签到与名单核验的依据，如需修改请联系平台管理员。"
                style="margin-bottom: 22px; border-radius: 10px"
              />

              <el-form
                ref="profileRef"
                :model="profileForm"
                :rules="profileRules"
                label-position="top"
                @submit.prevent="saveProfile"
              >
                <div class="form-grid">
                  <el-form-item label="昵称">
                    <el-input v-model="profileForm.nickname" placeholder="展示在活动页面的称呼" clearable />
                  </el-form-item>
                  <el-form-item label="头像地址" prop="avatar_url">
                    <el-input v-model="profileForm.avatar_url" placeholder="https://..." clearable />
                  </el-form-item>
                  <el-form-item label="电子邮箱" prop="email">
                    <el-input v-model="profileForm.email" placeholder="example@school.edu.cn" clearable />
                  </el-form-item>
                  <el-form-item label="手机号">
                    <el-input v-model="profileForm.phone" placeholder="便于接收活动通知" clearable />
                  </el-form-item>
                  <el-form-item label="学院">
                    <el-input v-model="profileForm.college" placeholder="例如：计算机学院" clearable />
                  </el-form-item>
                  <el-form-item label="专业">
                    <el-input v-model="profileForm.major" placeholder="例如：软件工程" clearable />
                  </el-form-item>
                  <el-form-item label="入学年级">
                    <el-input-number
                      v-model="profileForm.grade"
                      :min="2000"
                      :max="2100"
                      controls-position="right"
                      placeholder="例如：2026"
                      style="width: 100%"
                    />
                  </el-form-item>
                  <el-form-item label="账号角色">
                    <el-input
                      :model-value="auth.user?.roles.map((role) => role.name).join(' / ') || '学生'"
                      disabled
                      :prefix-icon="User"
                    />
                  </el-form-item>
                </div>

                <div class="form-actions">
                  <el-button
                    type="primary"
                    size="large"
                    :loading="savingProfile"
                    class="ch-button-gradient"
                    @click="saveProfile"
                  >
                    保存修改
                  </el-button>
                </div>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="账号安全" name="security">
              <div class="panel-head">
                <div>
                  <h3>修改密码</h3>
                  <p>建议使用至少 8 位、包含字母与数字的密码，并定期更换。</p>
                </div>
              </div>

              <div class="security-card">
                <span class="security-icon"><el-icon><Lock /></el-icon></span>
                <div>
                  <strong>密码安全</strong>
                  <p>修改密码后当前登录状态会失效，需要使用新密码重新登录。</p>
                </div>
              </div>

              <el-form
                ref="passwordRef"
                :model="passwordForm"
                :rules="passwordRules"
                label-position="top"
                class="password-form"
                @submit.prevent="savePassword"
              >
                <el-form-item label="原密码" prop="old_password">
                  <el-input
                    v-model="passwordForm.old_password"
                    type="password"
                    show-password
                    placeholder="请输入当前使用的密码"
                  />
                </el-form-item>
                <el-form-item label="新密码" prop="new_password">
                  <el-input
                    v-model="passwordForm.new_password"
                    type="password"
                    show-password
                    placeholder="至少 8 位字符"
                  />
                </el-form-item>
                <el-form-item label="确认新密码" prop="confirm_password">
                  <el-input
                    v-model="passwordForm.confirm_password"
                    type="password"
                    show-password
                    placeholder="再次输入新密码"
                  />
                </el-form-item>
                <div class="form-actions">
                  <el-button
                    type="primary"
                    size="large"
                    :loading="savingPassword"
                    @click="savePassword"
                  >
                    更新密码
                  </el-button>
                </div>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.profile-card {
  overflow: hidden;
}

.profile-card__cover {
  height: 116px;
  background:
    radial-gradient(280px 180px at 15% 0%, rgba(255, 255, 255, 0.22), transparent 60%),
    linear-gradient(135deg, #4a68f2, #3757e8 52%, #2439a8);
}

.profile-card__avatar {
  display: flex;
  justify-content: center;
  margin-top: -42px;
}

.profile-card__avatar :deep(.user-avatar) {
  border: 4px solid #fff;
  box-shadow: 0 10px 26px rgba(16, 26, 51, 0.14);
}

.profile-card__body {
  padding: 14px 24px 24px;
  text-align: center;
}

.profile-card__body h2 {
  font-size: 21px;
  letter-spacing: -0.02em;
}

.student-no {
  display: inline-block;
  margin-top: 3px;
  color: var(--ch-muted-light);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.role-row {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.role-pill {
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--ch-primary-soft);
  color: var(--ch-primary);
  font-size: 10.5px;
  font-weight: 600;
}

.profile-facts {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 24px;
  padding-top: 22px;
  border-top: 1px solid #f0f3fa;
  text-align: left;
}

.profile-facts > div {
  display: flex;
  align-items: center;
  gap: 11px;
}

.fact-icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: #f5f7fd;
  color: var(--ch-primary);
  font-size: 14px;
}

.profile-facts div div {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.4;
}

.profile-facts div div span {
  color: var(--ch-muted-light);
  font-size: 10.5px;
}

.profile-facts strong {
  overflow: hidden;
  color: var(--ch-ink-soft);
  font-size: 12px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-card__footer {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid #f0f3fa;
  color: var(--ch-muted-light);
  font-size: 10.5px;
}

.profile-panel {
  padding: 10px 30px 30px;
}

.profile-panel :deep(.el-tabs__header) {
  margin-bottom: 22px;
}

.profile-panel :deep(.el-tabs__item) {
  height: 52px;
  font-size: 14px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.panel-head h3 {
  font-size: 19px;
  letter-spacing: -0.02em;
}

.panel-head p {
  margin-top: 4px;
  color: var(--ch-muted);
  font-size: 12.5px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.security-card {
  display: flex;
  gap: 14px;
  margin-bottom: 24px;
  padding: 18px;
  border: 1px solid #e7ecf9;
  border-radius: 12px;
  background: #f8faff;
}

.security-icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: #fff;
  color: var(--ch-primary);
  font-size: 18px;
  box-shadow: 0 4px 12px rgba(16, 26, 51, 0.06);
}

.security-card strong {
  font-size: 13px;
}

.security-card p {
  margin-top: 3px;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.6;
}

.password-form {
  max-width: 420px;
}

@media (max-width: 980px) {
  .profile-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .profile-card {
    display: grid;
    grid-template-columns: 220px minmax(0, 1fr);
    align-items: stretch;
  }

  .profile-card__cover {
    display: none;
  }

  .profile-card__avatar {
    margin: 0;
    padding: 24px;
    align-items: flex-start;
    justify-content: center;
    background: linear-gradient(160deg, #eef2ff, #f8faff);
  }

  .profile-card__body {
    text-align: left;
    padding: 24px;
  }

  .role-row {
    justify-content: flex-start;
  }

  .profile-facts {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    margin-top: 18px;
    padding-top: 18px;
  }

  .profile-card__footer {
    display: none;
  }
}

@media (max-width: 640px) {
  .profile-card {
    display: block;
  }

  .profile-card__avatar {
    justify-content: center;
    margin-top: -42px;
    padding: 0;
    background: transparent;
  }

  .profile-card__body {
    text-align: center;
  }

  .role-row {
    justify-content: center;
  }

  .profile-facts {
    grid-template-columns: minmax(0, 1fr);
    text-align: left;
  }

  .profile-panel {
    padding: 6px 18px 22px;
  }

  .form-actions {
    justify-content: stretch;
  }

  .form-actions .el-button {
    width: 100%;
  }
}
</style>
