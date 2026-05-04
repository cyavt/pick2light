<template>
  <header class="app-header">
    <div class="header-left">
      <h2 class="header-title">{{ currentPageTitle }}</h2>
    </div>

    <div class="header-right">
      <!-- Search -->
      <div class="header-search">
        <span class="search-icon"><i class="fa fa-search"></i></span>
        <input type="text" placeholder="Tìm thiết bị, đơn hàng..." class="input search-input" />
      </div>

      <!-- Notifications -->
      <button class="header-icon-btn" title="Thông báo">
        <i class="fa fa-bell"></i>
        <span class="notification-dot"></span>
      </button>

      <!-- Theme Toggle -->
      <button class="header-icon-btn theme-toggle" :title="isDark ? 'Chuyển Light mode' : 'Chuyển Dark mode'" @click="toggleTheme">
        <i class="fa" :class="isDark ? 'fa-sun' : 'fa-moon'"></i>
      </button>

      <!-- User Dropdown -->
      <div class="header-user" @click="showDropdown = !showDropdown">
        <div class="user-avatar">{{ userInitial }}</div>
        <div class="user-info">
          <span class="user-name">{{ displayName }}</span>
          <span class="user-role">{{ displayRole }}</span>
        </div>
        <i class="fa fa-caret-down" style="color: var(--text-muted); margin-left: 4px;"></i>
      </div>

      <!-- Dropdown menu -->
      <div v-if="showDropdown" class="user-dropdown">
        <div class="dropdown-header">
          <strong>{{ displayName }}</strong>
          <span>{{ displayRole }}</span>
        </div>
        <div class="dropdown-divider"></div>
        <button class="dropdown-item" @click="handleLogout">
          <i class="fa fa-sign-out-alt"></i> Đăng xuất
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { useAuth } from '../composables/useAuth'

const route = useRoute()
const { isDark, toggleTheme } = useTheme()
const { user, logout } = useAuth()

const showDropdown = ref(false)

const roleLabels = {
  admin: 'Quản trị viên',
  supervisor: 'Giám sát',
  picker: 'Nhân viên pick',
}

const displayName = computed(() => user.value?.username || 'User')
const displayRole = computed(() => roleLabels[user.value?.role] || user.value?.role || '')
const userInitial = computed(() => (user.value?.username || 'U')[0].toUpperCase())

const pageTitles = {
  '/': 'Dashboard',
  '/orders': 'Quản lý đơn hàng',
  '/devices': 'Quản lý thiết bị',
  '/zones': 'Quản lý Zones',
  '/reports': 'Báo cáo',
  '/users': 'Quản lý tài khoản',
}

const currentPageTitle = computed(() => pageTitles[route.path] || 'PTL System')

function handleLogout() {
  showDropdown.value = false
  logout()
}

// Close dropdown when clicking outside
function onClickOutside(e) {
  if (!e.target.closest('.header-user') && !e.target.closest('.user-dropdown')) {
    showDropdown.value = false
  }
}
onMounted(() => document.addEventListener('click', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
/* Inspinia top navbar — clean, flat */
.app-header {
  height: var(--header-height);
  min-height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  gap: 16px;
}

.header-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-heading);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Search — Inspinia style */
.header-search {
  position: relative;
  display: flex;
  align-items: center;
}
.search-icon {
  position: absolute;
  left: 10px;
  font-size: 0.85rem;
  pointer-events: none;
  opacity: 0.6;
}
.search-input {
  width: 220px;
  padding-left: 32px;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--border);
  border-radius: 0;
  font-size: 0.9em;
  height: 34px;
  color: var(--text-primary);
}
.search-input:focus {
  width: 280px;
  border-bottom-color: var(--primary);
}

/* Icon buttons — minimal Inspinia style */
.header-icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  font-size: 1rem;
  cursor: pointer;
  position: relative;
  transition: background var(--transition-fast);
  color: var(--text-muted);
}
.header-icon-btn:hover {
  background: var(--bg-hover);
}
.notification-dot {
  position: absolute;
  top: 5px;
  right: 5px;
  width: 8px;
  height: 8px;
  background: var(--danger);
  border-radius: 50%;
  border: 2px solid var(--bg-surface);
}

/* User — Inspinia profile dropdown look */
.header-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.header-user:hover {
  background: var(--bg-hover);
}
.user-avatar {
  width: 32px;
  height: 32px;
  background: var(--primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.8rem;
  color: #fff;
}
.user-info {
  display: flex;
  flex-direction: column;
}
.user-name {
  font-size: 0.9em;
  font-weight: 600;
  color: var(--text-heading);
}
.user-role {
  font-size: 0.75em;
  color: var(--text-muted);
}

/* Theme Toggle */
.theme-toggle {
  overflow: hidden;
}

/* User Dropdown */
.user-dropdown {
  position: absolute;
  top: calc(var(--header-height) - 4px);
  right: 20px;
  width: 200px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  overflow: hidden;
}
.dropdown-header {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dropdown-header strong {
  font-size: 0.9em;
  color: var(--text-heading);
}
.dropdown-header span {
  font-size: 0.75em;
  color: var(--text-muted);
}
.dropdown-divider {
  height: 1px;
  background: var(--border);
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 14px;
  background: none;
  border: none;
  font-family: var(--font);
  font-size: 0.85em;
  color: var(--danger);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.dropdown-item:hover {
  background: var(--bg-hover);
}
</style>
