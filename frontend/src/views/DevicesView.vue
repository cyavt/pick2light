<template>
  <div class="devices-page fade-in">
    <div class="page-header">
      <div>
        <h1><i class="fa fa-microchip"></i> Quản lý thiết bị</h1>
        <p>Danh sách thiết bị Pick-to-Light</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-ghost" @click="fetchDevices"><i class="fa fa-sync"></i> Làm mới</button>
        <button class="btn btn-primary" @click="openCreateModal">+ Thêm thiết bị</button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters card">
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
            <th>Vị trí</th>
            <th>Trạng thái</th>
            <th>Lần cuối online</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="text-center text-muted">
              <i class="fa fa-spinner fa-spin"></i> Đang tải...
            </td>
          </tr>
          <tr v-else-if="filteredDevices.length === 0">
            <td colspan="5" class="text-center text-muted">Không có thiết bị nào</td>
          </tr>
          <tr v-for="device in paginatedDevices" :key="device.id">
            <td><strong>{{ device.device_code }}</strong></td>
            <td class="text-muted">{{ device.location || '—' }}</td>
            <td>
              <span class="badge" :class="'badge-' + device.status">
                <span class="status-indicator" :class="device.status"></span>
                {{ device.status }}
              </span>
            </td>
            <td class="text-muted">{{ formatDate(device.last_seen) }}</td>
            <td>
              <div class="action-btns">
                <button
                  class="btn btn-sm btn-primary"
                  @click="testLed(device)"
                  :disabled="testingDevice === device.id"
                >
                  <i :class="testingDevice === device.id ? 'fa fa-spinner fa-spin' : 'fa fa-lightbulb'"></i>
                  Test
                </button>
                <button class="btn btn-sm btn-ghost" @click="openEditModal(device)" title="Sửa">
                  <i class="fa fa-pen"></i>
                </button>
                <button class="btn btn-sm btn-ghost text-danger" @click="deleteDevice(device)" title="Xoá">
                  <i class="fa fa-trash"></i>
                </button>
              </div>
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

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal card">
        <h3><i class="fa fa-microchip"></i> {{ editingDevice ? 'Sửa thiết bị' : 'Thêm thiết bị' }}</h3>
        <div class="form-group">
          <label>Mã thiết bị</label>
          <input class="input" v-model="form.device_code" placeholder="PTL-A001" />
        </div>
        <div class="form-group">
          <label>Vị trí</label>
          <input class="input" v-model="form.location" placeholder="A/Row1/Slot01" />
        </div>
        <div v-if="formError" class="form-error">{{ formError }}</div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="closeModal">Huỷ</button>
          <button class="btn btn-primary" @click="submitDevice" :disabled="saving">
            <i :class="saving ? 'fa fa-spinner fa-spin' : 'fa fa-check'"></i>
            {{ editingDevice ? 'Cập nhật' : 'Tạo' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'

const { authFetch } = useAuth()

const loading = ref(false)
const devices = ref([])
const filterStatus = ref('')
const searchQuery = ref('')
const page = ref(1)
const perPage = 20
const testingDevice = ref(null)
const testResult = ref(null)

// Modal state
const showModal = ref(false)
const editingDevice = ref(null)
const saving = ref(false)
const formError = ref('')
const form = ref({ device_code: '', location: '' })

const filteredDevices = computed(() => {
  return devices.value.filter(d => {
    const matchStatus = !filterStatus.value || d.status === filterStatus.value
    const matchSearch = !searchQuery.value || d.device_code.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchStatus && matchSearch
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

// ─── CRUD ─────────────────────────────────────────────────
function openCreateModal() {
  editingDevice.value = null
  form.value = { device_code: '', location: '' }
  formError.value = ''
  showModal.value = true
}

function openEditModal(device) {
  editingDevice.value = device
  form.value = { device_code: device.device_code, location: device.location || '' }
  formError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingDevice.value = null
  formError.value = ''
}

async function submitDevice() {
  if (!form.value.device_code.trim()) {
    formError.value = 'Mã thiết bị không được để trống'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    const url = editingDevice.value
      ? `/api/devices/${editingDevice.value.id}`
      : '/api/devices/'
    const method = editingDevice.value ? 'PUT' : 'POST'

    const res = await authFetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })
    const data = await res.json()
    if (res.ok) {
      closeModal()
      await fetchDevices()
      showToast(true, editingDevice.value ? 'Cập nhật thành công' : 'Thêm thiết bị thành công')
    } else {
      formError.value = data.detail || 'Lỗi không xác định'
    }
  } catch {
    formError.value = 'Lỗi kết nối'
  } finally {
    saving.value = false
  }
}

async function deleteDevice(device) {
  if (!confirm(`Xoá thiết bị "${device.device_code}"?`)) return
  const res = await authFetch(`/api/devices/${device.id}`, { method: 'DELETE' })
  if (res.ok) {
    await fetchDevices()
    showToast(true, `Đã xoá ${device.device_code}`)
  } else {
    const data = await res.json()
    showToast(false, data.detail || 'Xoá thất bại')
  }
}

// ─── Test LED ─────────────────────────────────────────────
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
      showToast(true, data.message)
    } else {
      showToast(false, data.detail || 'Test thất bại')
    }
    await fetchDevices()
  } catch {
    showToast(false, 'Lỗi kết nối')
  } finally {
    testingDevice.value = null
  }
}

function showToast(ok, message) {
  testResult.value = { ok, message }
  setTimeout(() => { testResult.value = null }, 4000)
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

/* Form */
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 600; margin-bottom: 4px; }
.form-error { color: var(--danger); font-size: 0.82rem; margin-bottom: 10px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
</style>
