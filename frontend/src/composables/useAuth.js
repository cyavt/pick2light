/**
 * Auth composable — JWT login, logout, token refresh.
 * access_token stored in memory, refresh_token in localStorage.
 */

import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

// ─── Module-level shared state ─────────────────────────────
const user = ref(null)
let accessToken = null
const loading = ref(false)
const error = ref(null)

const AUTH_BASE = '/auth'
const REFRESH_KEY = 'ptl_refresh_token'

export function useAuth() {
  const router = useRouter()

  const isAuthenticated = computed(() => !!user.value && !!accessToken)

  /**
   * Login with username + password.
   */
  async function login(username, password) {
    loading.value = true
    error.value = null

    try {
      const res = await fetch(`${AUTH_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Đăng nhập thất bại')
      }

      const data = await res.json()
      accessToken = data.access_token
      localStorage.setItem(REFRESH_KEY, data.refresh_token)
      user.value = data.user

      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Logout — clear tokens and redirect to login.
   */
  async function logout() {
    try {
      await fetch(`${AUTH_BASE}/logout`, {
        method: 'POST',
        headers: authHeaders(),
      })
    } catch {
      // ignore network errors on logout
    }

    accessToken = null
    user.value = null
    localStorage.removeItem(REFRESH_KEY)
    router.push('/login')
  }

  /**
   * Refresh the access token using stored refresh_token.
   * Returns true if successful.
   */
  async function refreshToken() {
    const rt = localStorage.getItem(REFRESH_KEY)
    if (!rt) return false

    try {
      const res = await fetch(`${AUTH_BASE}/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      })

      if (!res.ok) {
        // Refresh token expired or invalid
        localStorage.removeItem(REFRESH_KEY)
        return false
      }

      const data = await res.json()
      accessToken = data.access_token

      // Also fetch user info if not loaded
      if (!user.value) {
        await fetchUser()
      }

      return true
    } catch {
      return false
    }
  }

  /**
   * Fetch current user info from /auth/me.
   */
  async function fetchUser() {
    if (!accessToken) return false

    try {
      const res = await fetch(`${AUTH_BASE}/me`, {
        headers: authHeaders(),
      })

      if (!res.ok) return false

      user.value = await res.json()
      return true
    } catch {
      return false
    }
  }

  /**
   * Authenticated fetch wrapper.
   * Automatically attaches Bearer token and retries once on 401 (token refresh).
   */
  async function authFetch(url, options = {}) {
    options.headers = { ...options.headers, ...authHeaders() }
    let res = await fetch(url, options)

    // If 401, try refreshing token and retry once
    if (res.status === 401) {
      const refreshed = await refreshToken()
      if (refreshed) {
        options.headers = { ...options.headers, ...authHeaders() }
        res = await fetch(url, options)
      }
    }

    return res
  }

  /**
   * Check if we have a stored refresh token and try to restore the session.
   * Called by router guard on app startup.
   */
  async function tryRestoreSession() {
    if (accessToken && user.value) return true
    return await refreshToken()
  }

  // ─── Helpers ────────────────────────────────────────────
  function authHeaders() {
    if (!accessToken) return {}
    return { Authorization: `Bearer ${accessToken}` }
  }

  return {
    user,
    loading,
    error,
    isAuthenticated,
    login,
    logout,
    refreshToken,
    fetchUser,
    authFetch,
    tryRestoreSession,
  }
}
