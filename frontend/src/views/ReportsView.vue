<template>
  <div class="reports-page fade-in">
    <div class="page-header">
      <div>
        <h1><i class="fa fa-bar-chart"></i> Báo cáo</h1>
        <p>Thống kê hiệu suất hệ thống</p>
      </div>
      <div class="header-actions">
        <select class="input" v-model="period" style="width: 160px;">
          <option value="today">Hôm nay</option>
          <option value="week">7 ngày</option>
          <option value="month">30 ngày</option>
        </select>
      </div>
    </div>

    <!-- Summary Stats -->
    <div class="grid-stats">
      <div class="report-stat card">
        <div class="report-stat-icon"><i class="fa fa-cube"></i></div>
        <div class="report-stat-value">{{ report.totalOrders }}</div>
        <div class="report-stat-label">Tổng đơn hàng</div>
      </div>
      <div class="report-stat card">
        <div class="report-stat-icon"><i class="fa fa-check-circle"></i></div>
        <div class="report-stat-value">{{ report.completedOrders }}</div>
        <div class="report-stat-label">Đơn hoàn thành</div>
      </div>
      <div class="report-stat card">
        <div class="report-stat-icon"><i class="fa fa-bolt"></i></div>
        <div class="report-stat-value">{{ report.avgPickTime }}s</div>
        <div class="report-stat-label">Thời gian pick TB</div>
      </div>
      <div class="report-stat card">
        <div class="report-stat-icon"><i class="fa fa-chart-pie"></i></div>
        <div class="report-stat-value">{{ report.accuracy }}%</div>
        <div class="report-stat-label">Độ chính xác</div>
      </div>
    </div>

    <!-- Zone Performance -->
    <div class="card">
      <h3 class="section-title">Hiệu suất theo Zone</h3>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Zone</th>
              <th>Đơn xử lý</th>
              <th>Tasks hoàn thành</th>
              <th>Thời gian TB</th>
              <th>Uptime thiết bị</th>
              <th>Hiệu suất</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="zone in zonePerformance" :key="zone.name">
              <td><strong>{{ zone.name }}</strong></td>
              <td>{{ zone.orders }}</td>
              <td>{{ zone.tasks }}</td>
              <td>{{ zone.avgTime }}s</td>
              <td>
                <div class="td-progress">
                  <div class="progress-bar">
                    <div class="progress-bar-fill" :style="{ width: zone.uptime + '%' }"></div>
                  </div>
                  <span>{{ zone.uptime }}%</span>
                </div>
              </td>
              <td>
                <span class="badge" :class="zone.score >= 90 ? 'badge-online' : zone.score >= 70 ? 'badge-active' : 'badge-offline'">
                  {{ zone.score >= 90 ? 'Xuất sắc' : zone.score >= 70 ? 'Tốt' : 'Cần cải thiện' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const period = ref('today')

const report = ref({
  totalOrders: 31,
  completedOrders: 28,
  avgPickTime: 4.2,
  accuracy: 99.2,
})

const zonePerformance = ref([
  { name: 'Zone A', orders: 8, tasks: 96, avgTime: 3.8, uptime: 97.5, score: 95 },
  { name: 'Zone B', orders: 6, tasks: 48, avgTime: 4.5, uptime: 93.5, score: 88 },
  { name: 'Zone C', orders: 10, tasks: 200, avgTime: 4.1, uptime: 96.0, score: 92 },
  { name: 'Zone D', orders: 4, tasks: 24, avgTime: 3.5, uptime: 99.0, score: 97 },
  { name: 'Zone E', orders: 3, tasks: 12, avgTime: 5.2, uptime: 87.5, score: 72 },
])
</script>

<style scoped>
.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 16px;
}

.report-stat {
  text-align: center;
  padding: 24px;
}
.report-stat-icon {
  font-size: 1.8rem;
  margin-bottom: 10px;
  color: var(--primary);
}
.report-stat-value {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 6px;
}
.report-stat-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.td-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 130px;
}
.td-progress span {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 36px;
}

.header-actions {
  display: flex;
  gap: 10px;
}
</style>
