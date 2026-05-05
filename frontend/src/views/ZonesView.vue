<template>
  <div class="zones-page fade-in">
    <div class="page-header">
      <div>
        <h1><i class="fa fa-map-marker-alt"></i> Quản lý Zones</h1>
        <p>{{ zones.length }} zones</p>
      </div>
      <button class="btn btn-primary" @click="showCreateModal = true">+ Thêm Zone</button>
    </div>

    <div class="zones-grid">
      <div v-if="loading" class="text-center text-muted" style="grid-column: 1/-1; padding: 40px">
        <i class="fa fa-spinner fa-spin"></i> Đang tải...
      </div>
      <div v-for="zone in zones" :key="zone.id" class="zone-card card">
        <div class="zone-header">
          <div class="zone-name">
            <span class="zone-icon"><i class="fa fa-map-marker-alt"></i></span>
            <div>
              <h3>{{ zone.name }}</h3>
              <span class="zone-slug">{{ zone.slug }}</span>
            </div>
          </div>
          <div class="zone-actions">
            <button class="btn btn-sm btn-ghost" @click="editZone(zone)" title="Sửa"><i class="fa fa-pen"></i></button>
            <button class="btn btn-sm btn-ghost text-danger" @click="deleteZone(zone)" title="Xoá" :disabled="zone.total_devices > 0"><i class="fa fa-trash"></i></button>
          </div>
        </div>

        <p class="zone-desc">{{ zone.description || '—' }}</p>

        <div class="zone-stats">
          <div class="zone-stat">
            <span class="stat-value">{{ zone.total_devices }}</span>
            <span class="stat-label">Thiết bị</span>
          </div>
          <div class="zone-stat">
            <span class="stat-value text-success">{{ zone.devices_online }}</span>
            <span class="stat-label">Online</span>
          </div>
          <div class="zone-stat">
            <span class="stat-value text-danger">{{ zone.devices_offline }}</span>
            <span class="stat-label">Offline</span>
          </div>
        </div>

        <div class="zone-progress">
          <div class="progress-bar">
            <div class="progress-bar-fill" :style="{ width: (zone.total_devices ? zone.devices_online / zone.total_devices * 100 : 0) + '%' }"></div>
          </div>
          <span class="progress-label">{{ zone.total_devices ? Math.round(zone.devices_online / zone.total_devices * 100) : 0 }}% online</span>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal card">
        <h3><i class="fa fa-map-marker-alt"></i> {{ editingZone ? 'Sửa Zone' : 'Thêm Zone' }}</h3>
        <div class="form-group">
          <label>Tên zone</label>
          <input class="input" v-model="form.name" placeholder="Zone A" />
        </div>
        <div class="form-group">
          <label>Mã zone (MQTT topic)</label>
          <input class="input" v-model="form.slug" placeholder="zone-a" />
          <span class="form-hint">Topic: ptl/device/<strong>{{ form.slug || '...' }}</strong>/DEV-001/cmd</span>
        </div>
        <div class="form-group">
          <label>Mô tả</label>
          <input class="input" v-model="form.description" placeholder="Khu vực A — Hàng tiêu dùng" />
        </div>
        <div v-if="formError" class="form-error">{{ formError }}</div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="closeModal">Huỷ</button>
          <button class="btn btn-primary" @click="submitZone" :disabled="saving">
            <i :class="saving ? 'fa fa-spinner fa-spin' : 'fa fa-check'"></i>
            {{ editingZone ? 'Cập nhật' : 'Tạo' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'

const { authFetch } = useAuth()

const zones = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const editingZone = ref(null)
const saving = ref(false)
const formError = ref('')
const form = ref({ name: '', slug: '', description: '' })

onMounted(() => {
  fetchZones()
})

async function fetchZones() {
  loading.value = true
  try {
    const res = await authFetch('/api/zones/')
    if (res.ok) {
      zones.value = await res.json()
    }
  } finally {
    loading.value = false
  }
}

function editZone(zone) {
  editingZone.value = zone
  form.value = { name: zone.name, slug: zone.slug, description: zone.description || '' }
  formError.value = ''
  showCreateModal.value = true
}

function closeModal() {
  showCreateModal.value = false
  editingZone.value = null
  form.value = { name: '', slug: '', description: '' }
  formError.value = ''
}

async function submitZone() {
  if (!form.value.name.trim() || !form.value.slug.trim()) {
    formError.value = 'Tên và mã zone không được để trống'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    const url = editingZone.value
      ? `/api/zones/${editingZone.value.id}`
      : '/api/zones/'
    const method = editingZone.value ? 'PUT' : 'POST'

    const res = await authFetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })
    const data = await res.json()
    if (res.ok) {
      closeModal()
      await fetchZones()
    } else {
      formError.value = data.detail || 'Lỗi không xác định'
    }
  } catch {
    formError.value = 'Lỗi kết nối'
  } finally {
    saving.value = false
  }
}

async function deleteZone(zone) {
  if (!confirm(`Xoá zone "${zone.name}"?`)) return
  const res = await authFetch(`/api/zones/${zone.id}`, { method: 'DELETE' })
  if (res.ok) {
    await fetchZones()
  } else {
    const data = await res.json()
    alert(data.detail || 'Xoá thất bại')
  }
}
</script>

<style scoped>
.zones-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.zone-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 8px;
}
.zone-name {
  display: flex;
  align-items: center;
  gap: 10px;
}
.zone-name h3 {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0;
}
.zone-slug {
  font-size: 0.75rem;
  color: var(--primary);
  font-family: monospace;
  background: var(--bg-secondary);
  padding: 1px 6px;
  border-radius: 4px;
}
.zone-icon {
  font-size: 1.3rem;
  color: var(--primary);
}
.zone-actions {
  display: flex;
  gap: 4px;
}
.zone-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 18px;
}

.zone-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.zone-stat { text-align: center; }
.stat-value { display: block; font-size: 1.4rem; font-weight: 700; }
.stat-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.text-success { color: var(--success-light); }
.text-danger { color: var(--danger-light); }

.zone-progress {
  display: flex;
  align-items: center;
  gap: 10px;
}
.progress-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  min-width: 70px;
}

/* Form */
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 600; margin-bottom: 4px; }
.form-hint { font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; display: block; }
.form-error { color: var(--danger); font-size: 0.82rem; margin-bottom: 10px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }

.text-center { text-align: center; }
.text-muted { color: var(--text-muted); }
</style>
