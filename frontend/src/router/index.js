import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('../views/OrdersView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/devices',
    name: 'Devices',
    component: () => import('../views/DevicesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/zones',
    name: 'Zones',
    component: () => import('../views/ZonesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('../views/ReportsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/UsersView.vue'),
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ─── Navigation Guard ─────────────────────────────────────
let sessionChecked = false

router.beforeEach(async (to, from, next) => {
  // Login page is always accessible
  if (!to.meta.requiresAuth) {
    return next()
  }

  const { isAuthenticated, tryRestoreSession, user } = useAuth()

  // If already authenticated, proceed
  if (isAuthenticated.value) {
    // Check admin-only routes
    if (to.meta.adminOnly && user.value?.role !== 'admin') {
      return next({ name: 'Dashboard' })
    }
    return next()
  }

  // On first load, try to restore session from refresh token
  if (!sessionChecked) {
    sessionChecked = true
    const restored = await tryRestoreSession()
    if (restored) {
      return next()
    }
  }

  // Not authenticated — redirect to login
  return next({ name: 'Login', query: { redirect: to.fullPath } })
})

export default router
