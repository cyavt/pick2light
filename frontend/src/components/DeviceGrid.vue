<template>
  <div class="device-grid-wrapper card">
    <!-- Header -->
    <div class="grid-header">
      <h3>Sơ đồ thiết bị</h3>
      <div class="grid-legend">
        <span class="legend-item"><span class="legend-dot online"></span> Online</span>
        <span class="legend-item"><span class="legend-dot active"></span> LED sáng</span>
        <span class="legend-item"><span class="legend-dot offline"></span> Offline</span>
        <span class="legend-item"><span class="legend-dot confirmed"></span> Confirmed</span>
      </div>
    </div>

    <!-- Zone Tabs -->
    <div class="zone-tabs">
      <button
        class="zone-tab"
        :class="{ active: activeZone === 'all' }"
        @click="activeZone = 'all'"
      >
        Tất cả
        <span class="tab-count">{{ devices.length }}</span>
      </button>
      <button
        v-for="zone in zoneList"
        :key="zone"
        class="zone-tab"
        :class="{ active: activeZone === zone }"
        @click="activeZone = zone"
      >
        {{ zone }}
        <span class="tab-count">{{ zoneDeviceCount(zone) }}</span>
      </button>
    </div>

    <!-- Grid Content -->
    <div class="grid-content">
      <template v-if="activeZone === 'all'">
        <!-- All zones with labels -->
        <div v-for="zone in zoneList" :key="zone" class="zone-block">
          <div class="zone-label">
            <span class="zone-label-name">{{ zone }}</span>
            <span class="zone-label-stats">
              <span class="zs-online">● {{ zoneOnline(zone) }}</span>
              <span class="zs-active">● {{ zoneActive(zone) }}</span>
              <span class="zs-offline">● {{ zoneOffline(zone) }}</span>
            </span>
          </div>
          <div class="device-grid" :class="'cols-' + gridCols">
            <div
              v-for="device in devicesInZone(zone)"
              :key="device.id"
              class="device-cell"
              :class="device.status"
              :data-code="device.shortCode"
              :title="`${device.code} — ${device.zone} — ${device.status}`"
              @click="$emit('select', device)"
            ></div>
          </div>
        </div>
      </template>

      <template v-else>
        <!-- Single zone focused -->
        <div class="zone-block zone-focused">
          <div class="zone-label">
            <span class="zone-label-name">{{ activeZone }}</span>
            <span class="zone-label-stats">
              <span class="zs-online">● {{ zoneOnline(activeZone) }} online</span>
              <span class="zs-active">● {{ zoneActive(activeZone) }} LED</span>
              <span class="zs-offline">● {{ zoneOffline(activeZone) }} offline</span>
            </span>
          </div>
          <div class="device-grid cols-focused">
            <div
              v-for="device in devicesInZone(activeZone)"
              :key="device.id"
              class="device-cell cell-lg"
              :class="device.status"
              :data-code="device.shortCode"
              :title="`${device.code} — ${device.zone} — ${device.status}`"
              @click="$emit('select', device)"
            ></div>
          </div>
        </div>
      </template>
    </div>

    <!-- Footer -->
    <div class="grid-footer">
      <span>Tổng: <strong>{{ visibleCount }}</strong></span>
      <span>Online: <strong class="text-success">{{ visibleOnline }}</strong></span>
      <span>LED sáng: <strong class="text-warning">{{ visibleActive }}</strong></span>
      <span>Offline: <strong class="text-danger">{{ visibleOffline }}</strong></span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  devices: { type: Array, required: true },
})

defineEmits(['select'])

const activeZone = ref('all')

// Extract unique zone names, preserving order
const zoneList = computed(() => {
  const seen = new Set()
  return props.devices
    .map(d => d.zone)
    .filter(z => { if (seen.has(z)) return false; seen.add(z); return true })
})

const gridCols = computed(() => {
  // In "all" view: 40 cols per zone row (200 devices / 5 rows = 40)
  return 40
})

function devicesInZone(zone) {
  return props.devices.filter(d => d.zone === zone)
}
function zoneDeviceCount(zone) {
  return devicesInZone(zone).length
}
function zoneOnline(zone) {
  return devicesInZone(zone).filter(d => d.status === 'online').length
}
function zoneActive(zone) {
  return devicesInZone(zone).filter(d => d.status === 'active').length
}
function zoneOffline(zone) {
  return devicesInZone(zone).filter(d => d.status === 'offline').length
}

// Footer stats based on visible devices
const visibleDevices = computed(() => {
  if (activeZone.value === 'all') return props.devices
  return devicesInZone(activeZone.value)
})
const visibleCount = computed(() => visibleDevices.value.length)
const visibleOnline = computed(() => visibleDevices.value.filter(d => d.status === 'online').length)
const visibleActive = computed(() => visibleDevices.value.filter(d => d.status === 'active').length)
const visibleOffline = computed(() => visibleDevices.value.filter(d => d.status === 'offline').length)
</script>

<style scoped>
.device-grid-wrapper.card:hover {
  border-color: var(--glass-border);
  box-shadow: none;
}

/* Header */
.grid-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.grid-header h3 {
  font-size: 1rem;
  font-weight: 600;
}
.grid-legend {
  display: flex;
  gap: 14px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}
.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  border: 1px solid rgba(0,0,0,0.1);
}
.legend-dot.online { background: #1ab394; }
.legend-dot.active { background: #f5a623; }
.legend-dot.offline { background: #c4c8cc; }
.legend-dot.confirmed { background: #1c84c6; }

/* Zone Tabs */
.zone-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 14px;
  padding: 3px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  overflow-x: auto;
}
.zone-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font-family: var(--font);
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.zone-tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.zone-tab.active {
  background: var(--primary);
  color: white;
}
.tab-count {
  font-size: 0.7rem;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: rgba(255,255,255,0.12);
}
.zone-tab.active .tab-count {
  background: rgba(255,255,255,0.25);
}

/* Grid Content */
.grid-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 420px;
  overflow-y: auto;
  padding-right: 4px;
}

/* Zone Block */
.zone-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.zone-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
}
.zone-label-name {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.zone-label-stats {
  display: flex;
  gap: 10px;
  font-size: 0.68rem;
  font-weight: 500;
}
.zs-online { color: #1ab394; }
.zs-active { color: #f5a623; }
.zs-offline { color: #9ca3af; }

/* Grid — all view: compact 40 cols */
.device-grid {
  display: grid;
  gap: 2px;
}
.cols-40 {
  grid-template-columns: repeat(40, 1fr);
}

/* Grid — focused view: larger cells, 25 cols */
.cols-focused {
  grid-template-columns: repeat(25, 1fr);
  gap: 3px;
}

/* Device Cell */
.device-cell {
  aspect-ratio: 1;
  border-radius: 2px;
  cursor: pointer;
  position: relative;
  transition: opacity var(--transition-fast);
}
.device-cell:hover {
  z-index: 10;
}
.device-cell:hover::after {
  content: attr(data-code);
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 28px;
  height: 28px;
  background: inherit;
  border-radius: 4px;
  box-shadow: 0 0 10px rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 7px;
  font-weight: 700;
  color: white;
  pointer-events: none;
}

/* Focused cells are larger — bigger tooltip */
.cell-lg:hover::after {
  width: 36px;
  height: 36px;
  font-size: 9px;
}

/* Status colors — high contrast, easy to distinguish */
.device-cell.online {
  background: #1ab394;
}
.device-cell.active {
  background: #f5a623;
  animation: blink-led 1.5s ease-in-out infinite;
}
.device-cell.offline {
  background: #d1d5db;
}
.device-cell.confirmed {
  background: #1c84c6;
}
.device-cell.idle { background: var(--bg-active); }

/* Footer */
.grid-footer {
  display: flex;
  gap: 20px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.text-success { color: var(--success-light); }
.text-warning { color: var(--warning-light); }
.text-danger { color: var(--danger-light); }
</style>
