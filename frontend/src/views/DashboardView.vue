<template>
  <div class="dashboard fade-in">
    <!-- Stats Cards -->
    <div class="grid-stats">
      <StatsCard icon="fa fa-microchip" label="Thiết bị Online" :value="stats.online" variant="success" :trend="2.5" />
      <StatsCard icon="fa fa-list-alt" label="Đơn đang chạy" :value="stats.activeOrders" variant="warning" />
      <StatsCard icon="fa fa-check-circle" label="Hoàn thành hôm nay" :value="stats.completedToday" variant="default" :trend="12" />
      <StatsCard icon="fa fa-exclamation-triangle" label="Thiết bị Offline" :value="stats.offline" variant="danger" :trend="-3" />
    </div>

    <!-- Device Grid + Active Orders -->
    <div class="grid-2">
      <!-- Device Grid -->
      <DeviceGrid :devices="mockDevices" @select="onDeviceSelect" />

      <!-- Right Column -->
      <div class="right-column">
        <!-- Active Orders -->
        <div class="card active-orders">
          <div class="section-header">
            <h3>Đơn đang xử lý</h3>
            <button class="btn btn-primary btn-sm" @click="showCreateOrder = true">+ Tạo đơn</button>
          </div>
          <div class="order-list">
            <div v-for="order in activeOrders" :key="order.id" class="order-item">
              <div class="order-info">
                <span class="order-ref">{{ order.ref }}</span>
                <span class="order-meta">{{ order.tasks }} tasks · {{ order.zone }}</span>
              </div>
              <div class="order-progress">
                <div class="progress-bar">
                  <div class="progress-bar-fill" :style="{ width: order.progress + '%' }"></div>
                </div>
                <span class="progress-text">{{ order.progress }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="card recent-activity">
          <h3 class="section-title">Hoạt động gần đây</h3>
          <div class="activity-list">
            <div v-for="(activity, i) in recentActivities" :key="i" class="activity-item">
              <span class="activity-icon"><i :class="activity.icon"></i></span>
              <div class="activity-content">
                <span class="activity-text">{{ activity.text }}</span>
                <span class="activity-time">{{ activity.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StatsCard from '../components/StatsCard.vue'
import DeviceGrid from '../components/DeviceGrid.vue'

// ─── Mock Stats ──────────────────────────────────────────────
const stats = ref({
  online: 947,
  activeOrders: 3,
  completedToday: 28,
  offline: 53,
})

// ─── Generate 1,000 mock devices ─────────────────────────────
const zones = ['A', 'B', 'C', 'D', 'E']
const statuses = ['online', 'online', 'online', 'online', 'online',
  'online', 'online', 'online', 'active', 'active',
  'confirmed', 'offline']

const mockDevices = ref(
  Array.from({ length: 1000 }, (_, i) => {
    const zone = zones[Math.floor(i / 200)]
    const status = statuses[Math.floor(Math.random() * statuses.length)]
    return {
      id: `dev-${String(i + 1).padStart(4, '0')}`,
      code: `PTL-${zone}${String((i % 200) + 1).padStart(3, '0')}`,
      shortCode: String((i % 200) + 1),
      zone: `Zone ${zone}`,
      status: status,
    }
  })
)

// ─── Active Orders ───────────────────────────────────────────
const activeOrders = ref([
  { id: 1, ref: 'ORD-2026-0504-001', tasks: 12, zone: 'Zone A', progress: 75 },
  { id: 2, ref: 'ORD-2026-0504-002', tasks: 8, zone: 'Zone B', progress: 38 },
  { id: 3, ref: 'ORD-2026-0504-003', tasks: 20, zone: 'Zone C', progress: 10 },
])

// ─── Recent Activity ────────────────────────────────────────
const recentActivities = ref([
  { icon: 'fa fa-check-circle text-primary', text: 'Task #127 confirmed — PTL-A042', time: '2 phút trước' },
  { icon: 'fa fa-list-alt text-info', text: 'ORD-2026-0504-003 khởi tạo', time: '5 phút trước' },
  { icon: 'fa fa-exclamation-circle text-danger', text: 'PTL-B089 mất kết nối', time: '8 phút trước' },
  { icon: 'fa fa-lightbulb text-warning', text: 'LED sáng — Zone A (12 devices)', time: '10 phút trước' },
  { icon: 'fa fa-check-circle text-primary', text: 'ORD-2026-0504-001 hoàn thành 9/12', time: '12 phút trước' },
  { icon: 'fa fa-plug text-success', text: 'PTL-C155 reconnected', time: '15 phút trước' },
])

const showCreateOrder = ref(false)

function onDeviceSelect(device) {
  console.log('Selected device:', device)
}
</script>

<style scoped>
.right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Active Orders */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.section-header h3 {
  font-size: 1rem;
  font-weight: 600;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.order-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}
.order-item:hover {
  background: var(--bg-hover);
}
.order-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.order-ref {
  font-weight: 600;
  font-size: 0.85rem;
}
.order-meta {
  font-size: 0.75rem;
  color: var(--text-muted);
}
.order-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 120px;
}
.progress-text {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--primary-light);
  min-width: 36px;
  text-align: right;
}

/* Recent Activity */
.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 14px;
}
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.activity-item:hover {
  background: var(--bg-hover);
}
.activity-icon {
  font-size: 1rem;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
  margin-top: 1px;
}
.activity-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.activity-text {
  font-size: 0.82rem;
}
.activity-time {
  font-size: 0.7rem;
  color: var(--text-muted);
}
</style>
