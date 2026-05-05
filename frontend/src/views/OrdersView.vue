<template>
  <div class="orders-page fade-in">
    <div class="page-header">
      <div>
        <h1><i class="fa fa-list-alt"></i> Quản lý đơn hàng</h1>
        <p>Tạo, theo dõi và quản lý đơn picking</p>
      </div>
    </div>

    <!-- Barcode Scanner -->
    <div class="scanner-section card">
      <div class="scanner-icon">
        <i class="fa fa-barcode"></i>
      </div>
      <div class="scanner-body">
        <h3>Quét barcode để kích hoạt đơn hàng</h3>
        <p>Quét mã đơn hoặc nhập thủ công rồi nhấn Enter</p>
      </div>
      <form class="scanner-input-wrapper" @submit.prevent="activateOrder">
        <input
          ref="scanInput"
          class="input scanner-input"
          v-model="scanCode"
          placeholder="Quét hoặc nhập mã đơn..."
          :disabled="activating"
          autofocus
        />
        <button class="btn btn-primary" type="submit" :disabled="activating || !scanCode">
          <i v-if="activating" class="fa fa-spinner fa-spin"></i>
          <span v-else><i class="fa fa-bolt"></i> Kích hoạt</span>
        </button>
      </form>
    </div>

    <!-- Scanner result -->
    <div v-if="scanResult" class="scan-result card" :class="scanResult.ok ? 'scan-success' : 'scan-error'">
      <i class="fa" :class="scanResult.ok ? 'fa-check-circle' : 'fa-exclamation-circle'"></i>
      <span>{{ scanResult.message }}</span>
      <button class="btn btn-ghost btn-sm" @click="scanResult = null">×</button>
    </div>

    <!-- Filters -->
    <div class="filters card">
      <select class="input filter-select" v-model="filterStatus">
        <option value="">Tất cả trạng thái</option>
        <option value="active">Đang chạy</option>
        <option value="pending">Chờ xử lý</option>
        <option value="completed">Hoàn thành</option>
        <option value="cancelled">Đã huỷ</option>
      </select>
      <input type="date" class="input filter-date" v-model="filterFrom" title="Từ ngày" />
      <span class="filter-sep">—</span>
      <input type="date" class="input filter-date" v-model="filterTo" title="Đến ngày" />
      <input class="input filter-search" placeholder="Tìm mã đơn..." v-model="searchQuery" />
      <span class="filter-count">{{ filteredOrders.length }}/{{ orders.length }} đơn</span>
    </div>

    <!-- Order Table -->
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th class="th-stt">STT</th>
            <th>Mã đơn</th>
            <th>Tasks</th>
            <th>Tiến độ</th>
            <th>Trạng thái</th>
            <th>Tạo lúc</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="text-center text-muted">
              <i class="fa fa-spinner fa-spin"></i> Đang tải...
            </td>
          </tr>
          <tr v-else-if="filteredOrders.length === 0">
            <td colspan="7" class="text-center text-muted">Chưa có đơn hàng nào</td>
          </tr>
          <tr v-for="(order, index) in filteredOrders" :key="order.id" @click="selectOrder(order)" class="clickable-row">
            <td class="td-stt">{{ index + 1 }}</td>
            <td><strong>{{ order.order_ref }}</strong></td>
            <td>{{ order.progress?.done || 0 }}/{{ order.progress?.total || 0 }}</td>
            <td>
              <div class="td-progress">
                <div class="progress-bar">
                  <div class="progress-bar-fill" :style="{ width: (order.progress?.percent || 0) + '%' }"></div>
                </div>
                <span class="progress-value">{{ order.progress?.percent || 0 }}%</span>
              </div>
            </td>
            <td>
              <span class="badge" :class="'badge-' + order.status">{{ statusLabels[order.status] }}</span>
            </td>
            <td class="text-muted">{{ formatDate(order.created_at) }}</td>
            <td>
              <div class="action-btns" @click.stop>
                <button v-if="order.status === 'pending'" class="btn btn-success btn-sm" @click="doActivate(order.order_ref)">
                  <i class="fa fa-play"></i> Kích hoạt
                </button>
                <button v-if="order.status === 'active'" class="btn btn-danger btn-sm" @click="cancelOrder(order)">
                  <i class="fa fa-times"></i> Huỷ
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Order Detail Modal -->
    <div v-if="selectedOrder" class="modal-overlay" @click.self="selectedOrder = null">
      <div class="modal card modal-lg">
        <div class="modal-header-row">
          <h3><i class="fa fa-list-alt"></i> {{ selectedOrder.order_ref }}</h3>
          <span class="badge" :class="'badge-' + selectedOrder.status">{{ statusLabels[selectedOrder.status] }}</span>
        </div>

        <div class="task-progress-summary">
          <div class="progress-bar" style="height: 8px;">
            <div class="progress-bar-fill" :style="{ width: (selectedOrder.progress?.percent || 0) + '%' }"></div>
          </div>
          <span>{{ selectedOrder.progress?.done || 0 }}/{{ selectedOrder.progress?.total || 0 }} tasks hoàn thành</span>
        </div>

        <table class="task-table">
          <thead>
            <tr>
              <th>Thiết bị</th>
              <th>SKU</th>
              <th>SL cần</th>
              <th>SL đã lấy</th>
              <th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in selectedOrder.tasks" :key="task.id">
              <td><strong>{{ task.device_code }}</strong></td>
              <td>{{ task.sku || '—' }}</td>
              <td>{{ task.quantity_required }}</td>
              <td>{{ task.quantity_picked }}</td>
              <td><span class="badge" :class="'badge-task-' + task.status">{{ taskStatusLabels[task.status] }}</span></td>
            </tr>
          </tbody>
        </table>

        <div class="modal-actions">
          <button class="btn btn-ghost" @click="selectedOrder = null">Đóng</button>
        </div>
      </div>
    </div>

    <!-- Busy Order Modal -->
    <div v-if="busyModal" class="modal-overlay" @click.self="busyModal = null">
      <div class="modal card">
        <div class="busy-modal-icon">
          <i class="fa fa-exclamation-triangle"></i>
        </div>
        <h3 class="busy-modal-title">Không thể kích hoạt</h3>
        <p class="busy-modal-msg">
          Đang có đơn hàng <strong>{{ busyModal.active_order_ref }}</strong> đang chạy.<br>
          Hoàn thành hoặc huỷ đơn hiện tại trước khi kích hoạt đơn mới.
        </p>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="busyModal = null">Đóng</button>
          <button class="btn btn-danger" @click="cancelBusyOrder">Huỷ đơn đang chạy</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuth } from '../composables/useAuth'

const { authFetch } = useAuth()

const loading = ref(false)
const orders = ref([])
const filterStatus = ref('')
const filterFrom = ref('')
const filterTo = ref('')
const searchQuery = ref('')
const scanCode = ref('')
const activating = ref(false)
const scanResult = ref(null)
const selectedOrder = ref(null)
const scanInput = ref(null)
const busyModal = ref(null)

const statusLabels = {
  pending: 'Chờ xử lý',
  active: 'Đang chạy',
  completed: 'Hoàn thành',
  cancelled: 'Đã huỷ',
}

const taskStatusLabels = {
  waiting: 'Chờ',
  active: 'Đang pick',
  confirmed: 'Đã lấy',
  skipped: 'Bỏ qua',
}

const filteredOrders = computed(() => {
  return orders.value.filter(o => {
    const matchStatus = !filterStatus.value || o.status === filterStatus.value
    const matchSearch = !searchQuery.value || o.order_ref.toLowerCase().includes(searchQuery.value.toLowerCase())

    // Date range filter (convert UTC → local date)
    let matchDateRange = true
    if ((filterFrom.value || filterTo.value) && o.created_at) {
      const d = new Date(o.created_at)
      const orderDate = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      if (filterFrom.value && orderDate < filterFrom.value) matchDateRange = false
      if (filterTo.value && orderDate > filterTo.value) matchDateRange = false
    }

    return matchStatus && matchSearch && matchDateRange
  })
})

// ─── WebSocket ──────────────────────────────────────────────
let ws = null
let wsReconnectTimer = null
const wsUrl = (import.meta.env.VITE_WS_URL || 'ws://localhost:8003') + '/ws/dashboard'

function connectWS() {
  if (ws && ws.readyState === WebSocket.OPEN) return

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('[WS] Connected to dashboard')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('[WS] Received:', data)
      // Refresh orders when task confirmed or order updated
      fetchOrders()

      // Update selectedOrder detail if open
      if (selectedOrder.value && data.order_id === selectedOrder.value.id) {
        refreshSelectedOrder()
      }
    } catch (e) {
      console.warn('[WS] Parse error:', e)
    }
  }

  ws.onclose = () => {
    console.log('[WS] Disconnected, reconnecting in 3s...')
    wsReconnectTimer = setTimeout(connectWS, 3000)
  }

  ws.onerror = (err) => {
    console.error('[WS] Error:', err)
    ws.close()
  }
}

async function refreshSelectedOrder() {
  if (!selectedOrder.value) return
  try {
    const res = await authFetch(`/api/orders/${selectedOrder.value.id}`)
    if (res.ok) {
      selectedOrder.value = await res.json()
    }
  } catch { /* ignore */ }
}

onMounted(() => {
  fetchOrders()
  connectWS()
  // Auto-focus scanner
  setTimeout(() => scanInput.value?.focus(), 300)
})

onUnmounted(() => {
  if (wsReconnectTimer) clearTimeout(wsReconnectTimer)
  if (ws) ws.close()
})

async function fetchOrders() {
  loading.value = true
  try {
    const res = await authFetch('/api/orders/')
    if (res.ok) {
      orders.value = await res.json()
    }
  } finally {
    loading.value = false
  }
}

async function activateOrder() {
  if (!scanCode.value.trim()) return
  await doActivate(scanCode.value.trim())
  scanCode.value = ''
  scanInput.value?.focus()
}

async function doActivate(orderRef) {
  activating.value = true
  scanResult.value = null
  try {
    const res = await authFetch('/api/orders/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_ref: orderRef }),
    })
    const data = await res.json()
    if (res.ok) {
      scanResult.value = {
        ok: true,
        message: `${data.message} — ${data.activated_devices?.join(', ')}`,
      }
      await fetchOrders()
    } else if (res.status === 409 && data.detail?.active_order_ref) {
      // Another order is running — show modal
      busyModal.value = data.detail
    } else {
      scanResult.value = {
        ok: false,
        message: (typeof data.detail === 'string' ? data.detail : data.detail?.message) || 'Kích hoạt thất bại',
      }
    }
  } catch {
    scanResult.value = { ok: false, message: 'Lỗi kết nối' }
  } finally {
    activating.value = false
  }
}

async function cancelOrder(order) {
  const res = await authFetch(`/api/orders/${order.id}/cancel`, { method: 'POST' })
  if (res.ok) {
    await fetchOrders()
  }
}

function selectOrder(order) {
  selectedOrder.value = order
}

async function cancelBusyOrder() {
  if (!busyModal.value?.active_order_id) return
  const res = await authFetch(`/api/orders/${busyModal.value.active_order_id}/cancel`, { method: 'POST' })
  if (res.ok) {
    busyModal.value = null
    await fetchOrders()
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
.text-muted { color: var(--text-muted); font-size: 0.8rem; }

/* Scanner */
.scanner-section {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 24px;
  margin-bottom: 16px;
  border-left: 4px solid var(--primary);
}
.scanner-icon {
  font-size: 2rem;
  color: var(--primary);
}
.scanner-body {
  flex: 1;
}
.scanner-body h3 {
  font-size: 0.95rem;
  margin: 0 0 2px;
}
.scanner-body p {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin: 0;
}
.scanner-input-wrapper {
  display: flex;
  gap: 8px;
}
.scanner-input {
  width: 280px;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

/* Scan Result */
.scan-result {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  margin-bottom: 16px;
  font-size: 0.85rem;
  font-weight: 500;
}
.scan-success {
  border-left: 4px solid var(--primary);
  background: rgba(26, 179, 148, 0.08);
  color: var(--primary-dark);
}
.scan-error {
  border-left: 4px solid var(--danger);
  background: rgba(237, 85, 101, 0.08);
  color: var(--danger);
}
.scan-result .btn { margin-left: auto; }

/* Filters */
.filters {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 14px 20px;
}
.filter-select { width: 180px; }
.filter-date { width: 160px; }
.filter-sep {
  color: var(--text-muted);
  font-size: 0.9rem;
  flex-shrink: 0;
}
.filter-search { width: 220px; }
.filter-count {
  margin-left: auto;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
}

/* STT column */
.th-stt, .td-stt {
  width: 50px;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.td-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 140px;
}
.progress-value {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary-light);
  min-width: 32px;
}

.action-btns { display: flex; gap: 6px; }
.clickable-row { cursor: pointer; }
.clickable-row:hover { background: var(--bg-hover); }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal { width: 440px; max-width: 90vw; }
.modal-lg { width: 680px; }
.modal h3 {
  font-size: 1.1rem;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.modal-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.modal-header-row h3 { margin-bottom: 0; }
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

/* Task table inside modal */
.task-progress-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.task-progress-summary .progress-bar { flex: 1; }
.task-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.task-table th, .task-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.task-table th {
  font-size: 0.72rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
}

/* Task status badges */
.badge-task-waiting { background: var(--bg-active); color: var(--text-secondary); }
.badge-task-active { background: #f5a623; color: #fff; }
.badge-task-confirmed { background: var(--primary); color: #fff; }
.badge-task-skipped { background: var(--bg-active); color: var(--text-muted); }

/* Busy modal */
.busy-modal-icon {
  text-align: center;
  font-size: 2.5rem;
  color: var(--warning);
  margin-bottom: 8px;
}
.busy-modal-title {
  text-align: center;
  color: var(--text-heading);
  margin-bottom: 12px;
}
.busy-modal-msg {
  text-align: center;
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--text-secondary);
}
</style>
