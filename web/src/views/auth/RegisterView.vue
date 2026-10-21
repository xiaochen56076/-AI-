<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import AuthLayout from '@/layouts/AuthLayout.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  student_no: '',
  real_name: '',
  nickname: '',
  email: '',
  phone: '',
  college: '',
  major: '',
  grade: null as number | null,
  password: '',
  confirm_password: '',
})

const rules: FormRules = {
  student_no: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9]+$/, message: '学号只能包含字母和数字', trigger: 'blur' },
    { min: 4, max: 20, message: '学号长度应为 4-20 位', trigger: 'blur' },
  ],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 8, max: 64, message: '密码长度应为 8-64 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (value !== form.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await auth.register({
      student_no: form.student_no,
      password: form.password,
      confirm_password: form.confirm_password,
      real_name: form.real_name,
      nickname: form.nickname,
      email: form.email,
      phone: form.phone,
      college: form.college,
      major: form.major,
      grade: form.grade,
    })
    ElMessage.success(`注册成功，欢迎加入 CampusHub，${auth.displayName}`)
    await router.replace('/')
  } catch {
    // 错误提示由请求拦截器统一处理
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AuthLayout
    eyebrow="Join CampusHub"
    title="创建你的校园账号"
    description="填写基础信息即可开始探索活动。学号将作为你的唯一登录凭证。"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      size="large"
      class="register-form"
      @submit.prevent="submit"
    >
      <div class="form-grid">
        <el-form-item label="学号" prop="student_no">
          <el-input v-model="form.student_no" placeholder="例如：20260001" autocomplete="username" clearable />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="用于活动名单与签到" clearable />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="展示在活动页面（可选）" clearable />
        </el-form-item>
        <el-form-item label="电子邮箱" prop="email">
          <el-input v-model="form.email" placeholder="example@school.edu.cn" clearable />
        </el-form-item>
        <el-form-item label="学院">
          <el-input v-model="form.college" placeholder="例如：计算机学院" clearable />
        </el-form-item>
        <el-form-item label="专业">
          <el-input v-model="form.major" placeholder="例如：软件工程" clearable />
        </el-form-item>
        <el-form-item label="入学年级">
          <el-input-number
            v-model="form.grade"
            :min="2000"
            :max="2100"
            :step="1"
            controls-position="right"
            placeholder="例如：2026"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="便于活动通知（可选）" clearable />
        </el-form-item>
        <el-form-item label="设置密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="至少 8 位字符"
            show-password
            autocomplete="new-password"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="form.confirm_password"
            type="password"
            placeholder="再次输入密码"
            show-password
            autocomplete="new-password"
          />
        </el-form-item>
      </div>

      <div class="register-note">
        <el-icon><InfoFilled /></el-icon>
        注册即代表你同意遵守校园活动平台的使用规范，活动名额与签到记录将真实生效。
      </div>

      <el-button
        type="primary"
        size="large"
        class="submit-button ch-button-gradient"
        :loading="submitting"
        native-type="submit"
      >
        创建账号
        <el-icon class="submit-arrow"><Right /></el-icon>
      </el-button>
    </el-form>

    <div class="auth-switch">
      已经有账号了？
      <RouterLink to="/login">直接登录</RouterLink>
    </div>
  </AuthLayout>
</template>

<style scoped>
.register-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.register-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 4px 0 20px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #f7f9fe;
  color: var(--ch-muted);
  font-size: 12px;
  line-height: 1.6;
}

.register-note .el-icon {
  flex: 0 0 auto;
  margin-top: 2px;
  color: var(--ch-primary);
}

.submit-button {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 15px;
}

.submit-arrow {
  margin-left: 4px;
}

.auth-switch {
  margin-top: 22px;
  text-align: center;
  color: var(--ch-muted);
  font-size: 13.5px;
}

.auth-switch a {
  margin-left: 4px;
  color: var(--ch-primary);
  font-weight: 700;
}

.auth-switch a:hover {
  text-decoration: underline;
}
</style>
