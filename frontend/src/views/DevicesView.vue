<template>
  <div class="devices-page fade-in">
    <div class="page-header">
      <div>
        <h1><i class="fa fa-microchip"></i> Quản lý thiết bị</h1>
        <p>Danh sách thiết bị Pick-to-Light</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-ghost" @click="fetchDevices"><i class="fa fa-sync"></i> Làm mới</button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters card">
      <select class="input filter-select" v-model="filterZone">
        <option value="">Tất cả Zone</option>
        <option v-for="z in zones" :key="z" :value="z">{{ z }}</option>
      </select>
      <select class="input filter-select" v-model="filterStatus">
        <option value="">Tất cả trạng thái</option>
        <option value="online">Online</option>
        <option value="offline">Offline</option>
      </select>
      <input class="input filter-search" placeholder="Tìm mã thiết bị..." v-model="searchQuery" />
      <span class="filter-count">{{ filteredDevices.length }} thiết bị</span>
    </div>

    <!-- Device Table -->
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Mã</th>
            <th>Zone</th>
            <th>Vị trí</th>
            <th>Trạng thái</th>
            <th>Lần cuối online</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="text-center text-muted">
              <i class="fa fa-spinner fa-spin"></i> Đang tải...
            </td>
          </tr>
          <tr v-else-if="filteredDevices.length === 0">
            <td colspan="7" class="text-center text-muted">Không có thiết bị nào</td>
          </tr>
          <tr v-for="device in paginatedDevices" :key="device.id">
            <td><strong>{{ device.device_code }}</strong></td>
            <td>{{ device.zone || '—' }}</td>
            <td class="text-muted">{{ device.location || '—' }}</td>
            <td>
              <span class="badge" :class="'badge-' + device.status">
                <span class="status-indicator" :class="device.status"></span>
                {{ device.status }}
              </span>
            </td>
            <td class="text-muted">{{ formatDate(device.last_seen) }}</td>
            <td>
              <button
                class="btn btn-sm btn-primary"
                @click="testLed(device)"
                :disabled="testingDevice === device.id"
              >
                <i :class="testingDevice === device.id ? 'fa fa-spinner fa-spin' : 'fa fa-lightbulb'"></i>
                Test
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <button class="btn btn-ghost btn-sm" :disabled="page === 1" @click="page--">← Trước</button>
      <span class="page-info">Trang {{ page }} / {{ totalPages || 1 }}</span>
      <button class="btn btn-ghost btn-sm" :disabled="page >= totalPages" @click="page++">Sau →</button>
    </div>

    <!-- Test Result Toast -->
    <div v-if="testResult" class="test-toast" :class="testResult.ok ? 'toast-success' : 'toast-error'">
      <i :class="testResult.ok ? 'fa fa-check-circle' : 'fa fa-exclamation-circle'"></i>
      {{ testResult.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'

const { authFetch } = useAuth()

const loading = ref(false)
const devices = ref([])
const filterZone = ref('')
const filterStatus = ref('')
const searchQuery = ref('')
const page = ref(1)
const perPage = 20
const testingDevice = ref(null)
const testResult = ref(null)

const zones = computed(() => {
  const zoneSet = new Set(devices.value.map(d => d.zone).filter(Boolean))
  return [...zoneSet].sort()
})

const filteredDevices = computed(() => {
  return devices.value.filter(d => {
    const matchZone = !filterZone.value || d.zone === filterZone.value
    const matchStatus = !filterStatus.value || d.status === filterStatus.value
    const matchSearch = !searchQuery.value || d.device_code.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchZone && matchStatus && matchSearch
  })
})

const totalPages = computed(() => Math.ceil(filteredDevices.value.length / perPage) || 1)
const paginatedDevices = computed(() => {
  const start = (page.value - 1) * perPage
  return filteredDevices.value.slice(start, start + perPage)
})

onMounted(() => {
  fetchDevices()
})

async function fetchDevices() {
  loading.value = true
  try {
    const res = await authFetch('/api/devices/')
    if (res.ok) {
      devices.value = await res.json()
    }
  } finally {
    loading.value = false
  }
}

async function testLed(device) {
  testingDevice.value = device.id
  testResult.value = null
  try {
    const res = await authFetch(`/api/devices/${device.id}/test-led`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ color: '#00FF00', duration: 3 }),
    })
    const data = await res.json()
    if (res.ok) {
      testResult.value = { ok: true, message: data.message }
    } else {
      testResult.value = { ok: false, message: data.detail || 'Test thất bại' }
    }
    await fetchDevices()
  } catch {
    testResult.value = { ok: false, message: 'Lỗi kết nối' }
  } finally {
    testingDevice.value = null
    setTimeout(() => { testResult.value = null }, 4000)
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' }) + ' ' +
         d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.text-center { text-align: center; }
.text-muted { color: var(--text-muted); font-size: 0.82rem; }

.filters {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 14px 20px;
}
.filter-select { width: 180px; }
.filter-search { width: 240px; }
.filter-count {
  margin-left: auto;
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
}

.action-btns { display: flex; gap: 6px; }
.header-actions { display: flex; gap: 10px; }

.status-indicator {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-right: 2px;
}
.status-indicator.online { background: var(--success); }
.status-indicator.offline { background: var(--danger); }
.status-indicator.active { background: var(--warning); animation: blink-led 1s infinite; }

.led-indicator {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  box-shadow: 0 0 8px currentColor;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 20px;
  padding-top: 16px;
}
.page-info {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

/* Test Toast */
.test-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 20px;
  border-radius: var(--radius-lg);
  font-size: 0.88rem;
  font-weight: 500;
  color: #fff;
  z-index: 1000;
  animation: slideUp 0.3s ease;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.toast-success { background: var(--success); }
.toast-error { background: var(--danger); }

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
