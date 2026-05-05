<template>
  <aside class="sidebar">
    <!-- Logo / Nav Header -->
    <div class="nav-header">
      <div class="logo-icon"><i class="fa fa-bolt"></i></div>
      <span class="logo-text">PTL System</span>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ active: $route.path === item.to }"
      >
        <span class="nav-icon"><i :class="item.icon"></i></span>
        <span class="nav-label">{{ item.label }}</span>
        <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
      </router-link>
    </nav>

    <!-- Bottom section -->
    <div class="sidebar-footer">
      <div class="sidebar-status">
        <div class="status-dot online"></div>
        <span>Hệ thống hoạt động</span>
      </div>
      <button class="sidebar-logout" @click="handleLogout">
        <i class="fa fa-sign-out-alt"></i> Đăng xuất
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAuth } from '../composables/useAuth'

const { logout, user } = useAuth()

const navItems = computed(() => {
  const items = [
    { icon: 'fa fa-th-large', label: 'Dashboard', to: '/' },
    { icon: 'fa fa-list-alt', label: 'Đơn hàng', to: '/orders', badge: 3 },
    { icon: 'fa fa-microchip', label: 'Thiết bị', to: '/devices' },
    { icon: 'fa fa-map-marker-alt', label: 'Zones', to: '/zones' },
    { icon: 'fa fa-bar-chart', label: 'Báo cáo', to: '/reports' },
    { icon: 'fa fa-flask', label: 'Tạo đơn giả', to: '/mock-order' },
  ]
  // Admin-only menu
  if (user.value?.role === 'admin') {
    items.push({ icon: 'fa fa-users', label: 'Tài khoản', to: '/users' })
  }
  return items
})

function handleLogout() {
  logout()
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  height: 100vh;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 100;
}

/* Nav Header — Inspinia style */
.nav-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 24px 20px;
  background: var(--sidebar-bg);
}
.logo-icon {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--sidebar-brand);
  border-radius: var(--radius-md);
  font-size: 1.1rem;
}
.logo-text {
  font-size: 1.15rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.01em;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px 14px 25px;
  color: var(--sidebar-text);
  font-size: 1rem;
  font-weight: 600;
  transition: all var(--transition-fast);
  text-decoration: none;
  border-left: 4px solid transparent;
}
.nav-item:hover {
  background: var(--sidebar-active);
  color: #ffffff;
}
.nav-item.active {
  background: var(--sidebar-active);
  color: #ffffff;
  border-left-color: var(--sidebar-brand);
}

.nav-icon {
  font-size: 1.05rem;
  width: 22px;
  text-align: center;
  color: var(--sidebar-brand);
}
.nav-item.active .nav-icon {
  color: #fff;
}

.nav-label {
  flex: 1;
}

.nav-badge {
  background: var(--sidebar-brand);
  color: white;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  min-width: 20px;
  text-align: center;
}

/* Footer */
.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.sidebar-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--sidebar-text);
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-dot.online {
  background: var(--sidebar-brand);
  animation: pulse-glow 2s ease-in-out infinite;
}
.sidebar-logout {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  width: 100%;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.06);
  border: none;
  border-radius: var(--radius-md);
  color: var(--sidebar-text);
  font-family: var(--font);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.sidebar-logout:hover {
  background: rgba(237, 85, 101, 0.15);
  color: var(--danger);
}
</style>
