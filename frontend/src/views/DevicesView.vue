<template>
  <div class="devices-page fade-in">
    <div class="page-header">
      <div>
        <h1><i class="fa fa-microchip"></i> Quản lý thiết bị</h1>
        <p>1,000 thiết bị Pick-to-Light</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-ghost"><i class="fa fa-sync"></i> Sync tất cả</button>
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
        <option value="active">LED đang sáng</option>
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
            <th>LED</th>
            <th>Lần cuối online</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="device in paginatedDevices" :key="device.id">
            <td><strong>{{ device.code }}</strong></td>
            <td>{{ device.zone }}</td>
            <td class="text-muted">{{ device.location }}</td>
            <td>
              <span class="badge" :class="'badge-' + device.status">
                <span class="status-indicator" :class="device.status"></span>
                {{ device.status }}
              </span>
            </td>
            <td>
              <span v-if="device.ledState !== 'off'" class="led-indicator" :style="{ background: device.ledColor }"></span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="text-muted">{{ device.lastSeen }}</td>
            <td>
              <div class="action-btns">
                <button class="btn btn-sm btn-primary" @click="testLed(device)"><i class="fa fa-lightbulb"></i> Test</button>
                <button class="btn btn-sm btn-ghost"><i class="fa fa-cog"></i></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <button class="btn btn-ghost btn-sm" :disabled="page === 1" @click="page--">← Trước</button>
      <span class="page-info">Trang {{ page }} / {{ totalPages }}</span>
      <button class="btn btn-ghost btn-sm" :disabled="page === totalPages" @click="page++">Sau →</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const filterZone = ref('')
const filterStatus = ref('')
const searchQuery = ref('')
const page = ref(1)
const perPage = 20

const zones = ['Zone A', 'Zone B', 'Zone C', 'Zone D', 'Zone E']

// Generate 1000 devices
const devices = ref(
  Array.from({ length: 1000 }, (_, i) => {
    const zone = zones[Math.floor(i / 200)]
    const statusOptions = ['online', 'online', 'online', 'online', 'offline', 'active']
    const status = statusOptions[Math.floor(Math.random() * statusOptions.length)]
    return {
      id: i + 1,
      code: `PTL-${zone.split(' ')[1]}${String((i % 200) + 1).padStart(3, '0')}`,
      zone: zone,
      location: `Kệ ${Math.floor(i / 10) + 1}-${(i % 10) + 1}`,
      status: status,
      ledState: status === 'active' ? 'on' : 'off',
      ledColor: status === 'active' ? '#FBBF24' : '#00FF00',
      lastSeen: status === 'offline'
        ? `${Math.floor(Math.random() * 30) + 1} phút trước`
        : 'Đang kết nối',
    }
  })
)

const filteredDevices = computed(() => {
  return devices.value.filter(d => {
    const matchZone = !filterZone.value || d.zone === filterZone.value
    const matchStatus = !filterStatus.value || d.status === filterStatus.value
    const matchSearch = !searchQuery.value || d.code.toLowerCase().includes(searchQuery.value.toLowerCase())
    return matchZone && matchStatus && matchSearch
  })
})

const totalPages = computed(() => Math.ceil(filteredDevices.value.length / perPage))
const paginatedDevices = computed(() => {
  const start = (page.value - 1) * perPage
  return filteredDevices.value.slice(start, start + perPage)
})

function testLed(device) {
  device.ledState = 'on'
  device.ledColor = '#22C55E'
  device.status = 'active'
  setTimeout(() => {
    device.ledState = 'off'
    device.status = 'online'
  }, 3000)
}
</script>

<style scoped>
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

.text-muted { color: var(--text-muted); font-size: 0.82rem; }
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
</style>
