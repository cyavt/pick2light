<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <div class="logo-icon-lg"><i class="fa fa-bolt"></i></div>
        <h1>PTL System</h1>
        <p>Pick-to-Light Dashboard</p>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="login-error">
        <i class="fa fa-exclamation-circle"></i>
        {{ error }}
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Tên đăng nhập</label>
          <div class="input-icon-wrap">
            <i class="fa fa-user input-icon"></i>
            <input
              class="input input-with-icon"
              type="text"
              v-model="username"
              placeholder="admin"
              autofocus
              :disabled="loading"
            />
          </div>
        </div>
        <div class="form-group">
          <label>Mật khẩu</label>
          <div class="input-icon-wrap">
            <i class="fa fa-lock input-icon"></i>
            <input
              class="input input-with-icon"
              type="password"
              v-model="password"
              placeholder="••••••••"
              :disabled="loading"
            />
          </div>
        </div>
        <button type="submit" class="btn btn-primary login-btn" :disabled="loading || !username || !password">
          <i v-if="loading" class="fa fa-spinner fa-spin"></i>
          <span v-else>Đăng nhập</span>
        </button>
      </form>

      <div class="login-footer">
        <span>PTL System v2.0.0 · © 2026</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const route = useRoute()
const { login, loading, error } = useAuth()

const username = ref('')
const password = ref('')

async function handleLogin() {
  const success = await login(username.value, password.value)
  if (success) {
    // Redirect to original page or dashboard
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-base);
}

.login-card {
  width: 400px;
  max-width: 90vw;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 40px;
}

.login-logo {
  text-align: center;
  margin-bottom: 28px;
}
.logo-icon-lg {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary);
  border-radius: var(--radius-md);
  font-size: 2rem;
  color: #fff;
}
.login-logo h1 {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.login-logo p {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-top: 4px;
}

/* Error */
.login-error {
  background: rgba(237, 85, 101, 0.1);
  border: 1px solid rgba(237, 85, 101, 0.3);
  color: var(--danger);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 0.85em;
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

/* Input with icon */
.input-icon-wrap {
  position: relative;
}
.input-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 0.85rem;
  pointer-events: none;
}
.input-with-icon {
  padding-left: 36px;
}

.login-btn {
  width: 100%;
  padding: 10px;
  font-size: 0.95rem;
  font-weight: 600;
  margin-top: 8px;
}
.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-footer {
  text-align: center;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  font-size: 0.75rem;
  color: var(--text-muted);
}
</style>
