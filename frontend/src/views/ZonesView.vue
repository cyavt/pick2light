<template>
  <div class="zones-page fade-in">
    <div class="page-header">
      <div>
        <h1><i class="fa fa-map-marker-alt"></i> Quản lý Zones</h1>
        <p>Kho Chính — 5 zones</p>
      </div>
      <button class="btn btn-primary">+ Thêm Zone</button>
    </div>

    <div class="zones-grid">
      <div v-for="zone in zones" :key="zone.id" class="zone-card card">
        <div class="zone-header">
          <div class="zone-name">
            <span class="zone-icon"><i class="fa fa-map-marker-alt"></i></span>
            <h3>{{ zone.name }}</h3>
          </div>
          <span class="badge" :class="zone.devicesOffline > 5 ? 'badge-warning' : 'badge-online'">
            {{ zone.devicesOffline > 5 ? 'Cảnh báo' : 'Bình thường' }}
          </span>
        </div>

        <p class="zone-desc">{{ zone.description }}</p>

        <div class="zone-stats">
          <div class="zone-stat">
            <span class="stat-value">{{ zone.totalDevices }}</span>
            <span class="stat-label">Thiết bị</span>
          </div>
          <div class="zone-stat">
            <span class="stat-value text-success">{{ zone.devicesOnline }}</span>
            <span class="stat-label">Online</span>
          </div>
          <div class="zone-stat">
            <span class="stat-value text-danger">{{ zone.devicesOffline }}</span>
            <span class="stat-label">Offline</span>
          </div>
          <div class="zone-stat">
            <span class="stat-value text-warning">{{ zone.activeTasks }}</span>
            <span class="stat-label">Tasks</span>
          </div>
        </div>

        <div class="zone-progress">
          <div class="progress-bar">
            <div class="progress-bar-fill" :style="{ width: (zone.devicesOnline / zone.totalDevices * 100) + '%' }"></div>
          </div>
          <span class="progress-label">{{ Math.round(zone.devicesOnline / zone.totalDevices * 100) }}% online</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const zones = ref([
  { id: 1, name: 'Zone A', description: 'Khu vực A — Hàng tiêu dùng', totalDevices: 200, devicesOnline: 195, devicesOffline: 5, activeTasks: 12 },
  { id: 2, name: 'Zone B', description: 'Khu vực B — Điện tử', totalDevices: 200, devicesOnline: 187, devicesOffline: 13, activeTasks: 8 },
  { id: 3, name: 'Zone C', description: 'Khu vực C — Thực phẩm', totalDevices: 200, devicesOnline: 192, devicesOffline: 8, activeTasks: 20 },
  { id: 4, name: 'Zone D', description: 'Khu vực D — Dược phẩm', totalDevices: 200, devicesOnline: 198, devicesOffline: 2, activeTasks: 0 },
  { id: 5, name: 'Zone E', description: 'Khu vực E — Hàng cồng kềnh', totalDevices: 200, devicesOnline: 175, devicesOffline: 25, activeTasks: 4 },
])
</script>

<style scoped>
.zones-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.zone-header {
  display: flex;
  align-items: center;
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
}
.zone-icon {
  font-size: 1.3rem;
  color: var(--primary);
}
.zone-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 18px;
}

.zone-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.zone-stat {
  text-align: center;
}
.stat-value {
  display: block;
  font-size: 1.4rem;
  font-weight: 700;
}
.stat-label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.text-success { color: var(--success-light); }
.text-danger { color: var(--danger-light); }
.text-warning { color: var(--warning-light); }

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
</style>
