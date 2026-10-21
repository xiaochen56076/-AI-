<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'

import AuthLayout from '@/layouts/AuthLayout.vue'
import { useAuthStore } from '@/stores/auth'

const REMEMBER_KEY = 'campushub.remember-student'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const formRef = ref<FormInstance>()
const remember = ref(false)
const form = reactive({
  student_no: '',
  password: '',
})

onMounted(() => {
  const saved = localStorage.getItem(REMEMBER_KEY)
  if (saved) {
    form.student_no = saved
    remember.value = true
  }
})

watch(remember, (value) => {
  if (!value) localStorage.removeItem(REMEMBER_KEY)
})

const rules: FormRules = {
  student_no: [
    { required: true, message: '请输入学号', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9]+$/, message: '学号只能包含字母和数字', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const expired = route.query.expired === '1'

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  try {
    await auth.login(form.student_no, form.password)
    if (remember.value) {
      localStorage.setItem(REMEMBER_KEY, form.student_no.trim())
    } else {
      localStorage.removeItem(REMEMBER_KEY)
    }
    ElMessage.success(`欢迎回来，${auth.displayName}`)
    const redirect =
      typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/')
        ? route.query.redirect
        : '/'
    await router.replace(redirect)
  } catch {
    // 错误提示由请求拦截器统一处理
  }
}
</script>

<template>
  <AuthLayout
    eyebrow="Welcome back"
    title="登录 CampusHub"
    description="使用学号和密码，继续发现校园里的下一场精彩。"
  >
    <el-alert
      v-if="expired"
      type="warning"
      :closable="false"
      show-icon
      title="登录状态已过期，请重新登录"
      style="margin-top: 20px; border-radius: 10px"
    />

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      size="large"
      @submit.prevent="submit"
    >
      <el-form-item label="学号" prop="student_no">
        <el-input
          v-model="form.student_no"
          placeholder="请输入你的学号"
          :prefix-icon="User"
          autocomplete="username"
          clearable
          @keyup.enter="submit"
        />
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="请输入登录密码"
          :prefix-icon="Lock"
          show-password
          autocomplete="current-password"
          @keyup.enter="submit"
        />
      </el-form-item>

      <div class="login-options">
        <el-checkbox v-model="remember">记住登录状态</el-checkbox>
        <span class="forgot">忘记密码？请联系平台管理员</span>
      </div>

      <el-button
        type="primary"
        size="large"
        class="submit-button ch-button-gradient"
        :loading="auth.loading"
        native-type="submit"
      >
        登录
        <el-icon class="submit-arrow"><Right /></el-icon>
      </el-button>
    </el-form>

    <div class="auth-switch">
      还没有账号？
      <RouterLink to="/register">立即注册</RouterLink>
    </div>
  </AuthLayout>
</template>

<style scoped>
.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: -6px 0 22px;
}

.forgot {
  color: var(--ch-muted-light);
  font-size: 12px;
}

.submit-button {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 15px;
  letter-spacing: 0.02em;
}

.submit-arrow {
  margin-left: 4px;
}

.auth-switch {
  margin-top: 26px;
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
