<template>
  <div class="mock-order-page fade-in">
    <div class="page-header">
      <div>
        <h1><i class="fa fa-flask"></i> Tạo đơn hàng giả</h1>
        <p>Tạo nhanh đơn picking với dữ liệu giả để test hệ thống</p>
      </div>
    </div>

    <!-- Generator Settings -->
    <div class="generator-section">
      <div class="gen-row">
        <!-- Left: Settings -->
        <div class="gen-settings card">
          <div class="card-title"><i class="fa fa-cog"></i> Cài đặt</div>

          <div class="form-group">
            <label>Mã đơn hàng (order_ref)</label>
            <div class="input-with-btn">
              <input class="input" v-model="orderRef" placeholder="VD: ORD-20260505-001" />
              <button class="btn btn-ghost btn-sm" @click="generateOrderRef" title="Tạo mã ngẫu nhiên">
                <i class="fa fa-random"></i>
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>Số lượng task (sản phẩm cần pick)</label>
            <div class="task-count-control">
              <button class="btn btn-ghost btn-sm" @click="taskCount = Math.max(1, taskCount - 1)">
                <i class="fa fa-minus"></i>
              </button>
              <input class="input task-count-input" type="number" v-model.number="taskCount" min="1" :max="availableDevices.length || 20" />
              <button class="btn btn-ghost btn-sm" @click="taskCount = Math.min(availableDevices.length || 20, taskCount + 1)">
                <i class="fa fa-plus"></i>
              </button>
            </div>
            <span class="form-hint" v-if="availableDevices.length">Tối đa {{ availableDevices.length }} (số thiết bị hiện có)</span>
          </div>

          <div class="form-group">
            <label>Phạm vi số lượng (mỗi task)</label>
            <div class="range-inputs">
              <input class="input range-input" type="number" v-model.number="qtyMin" min="1" placeholder="Min" />
              <span class="range-sep">—</span>
              <input class="input range-input" type="number" v-model.number="qtyMax" min="1" placeholder="Max" />
            </div>
          </div>

          <div class="form-actions">
            <button class="btn btn-primary" @click="generatePreview" :disabled="!orderRef || availableDevices.length === 0">
              <i class="fa fa-eye"></i> Xem trước
            </button>
            <button class="btn btn-ghost" @click="resetForm">
              <i class="fa fa-undo"></i> Reset
            </button>
          </div>
        </div>

        <!-- Right: Quick Info -->
        <div class="gen-info">
          <div class="info-card card">
            <div class="info-icon"><i class="fa fa-microchip"></i></div>
            <div class="info-body">
              <div class="info-value">{{ availableDevices.length }}</div>
              <div class="info-label">Thiết bị khả dụng</div>
            </div>
          </div>

          <div class="info-card card">
            <div class="info-icon text-warning"><i class="fa fa-list-alt"></i></div>
            <div class="info-body">
              <div class="info-value">{{ taskCount }}</div>
              <div class="info-label">Tasks sẽ tạo</div>
            </div>
          </div>

          <div class="info-card card">
            <div class="info-icon text-info"><i class="fa fa-barcode"></i></div>
            <div class="info-body">
              <div class="info-value">{{ orderRef || '—' }}</div>
              <div class="info-label">Mã đơn hàng</div>
            </div>
          </div>

          <div class="info-card card" :class="{ 'info-loading': loadingDevices }">
            <div class="info-icon text-success"><i class="fa" :class="loadingDevices ? 'fa-spinner fa-spin' : 'fa-check-circle'"></i></div>
            <div class="info-body">
              <div class="info-value">{{ loadingDevices ? '...' : 'Sẵn sàng' }}</div>
              <div class="info-label">{{ loadingDevices ? 'Đang tải devices' : 'Hệ thống' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Preview Table -->
    <div v-if="previewItems.length > 0" class="preview-section fade-in">
      <div class="preview-header">
        <h3><i class="fa fa-table"></i> Xem trước đơn hàng — {{ orderRef }}</h3>
        <div class="preview-actions">
          <button class="btn btn-ghost btn-sm" @click="shufflePreview">
            <i class="fa fa-random"></i> Đổi ngẫu nhiên
          </button>
          <button class="btn btn-primary" @click="submitOrder" :disabled="submitting">
            <i v-if="submitting" class="fa fa-spinner fa-spin"></i>
            <template v-else><i class="fa fa-paper-plane"></i> Tạo đơn hàng</template>
          </button>
        </div>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th class="th-stt">#</th>
              <th>Thiết bị</th>
              <th>Zone</th>
              <th>SKU</th>
              <th>Tên sản phẩm</th>
              <th>Số lượng</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in previewItems" :key="idx">
              <td class="td-stt">{{ idx + 1 }}</td>
              <td><strong>{{ item.device_code }}</strong></td>
              <td><span class="badge badge-zone">{{ item.zone || '—' }}</span></td>
              <td><code class="sku-code">{{ item.sku }}</code></td>
              <td class="product-name">{{ item.productName }}</td>
              <td>
                <input class="input qty-input" type="number" v-model.number="item.quantity" min="1" />
              </td>
              <td>
                <button class="btn btn-ghost btn-sm btn-remove" @click="removeItem(idx)" title="Xoá">
                  <i class="fa fa-times"></i>
                </button>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="5" class="text-right"><strong>Tổng số lượng</strong></td>
              <td><strong class="text-primary">{{ totalQty }}</strong></td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- Result -->
    <div v-if="result" class="result-banner card fade-in" :class="result.ok ? 'result-success' : 'result-error'">
      <div class="result-icon">
        <i class="fa" :class="result.ok ? 'fa-check-circle' : 'fa-exclamation-circle'"></i>
      </div>
      <div class="result-body">
        <strong>{{ result.ok ? 'Tạo thành công!' : 'Thất bại' }}</strong>
        <p>{{ result.message }}</p>
      </div>
      <button class="btn btn-ghost btn-sm" @click="result = null">×</button>
    </div>

    <!-- Recent Created Orders -->
    <div v-if="recentOrders.length > 0" class="recent-section">
      <h3><i class="fa fa-history"></i> Đơn vừa tạo (phiên này)</h3>
      <div class="recent-list">
        <div v-for="order in recentOrders" :key="order.order_ref" class="recent-item card">
          <div class="recent-ref">
            <i class="fa fa-check-circle text-primary"></i>
            <strong>{{ order.order_ref }}</strong>
          </div>
          <span class="badge badge-pending">{{ order.status }}</span>
          <span class="recent-meta">{{ order.taskCount }} tasks · tổng {{ order.totalQty }} SP</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'

const { authFetch } = useAuth()

// ─── State ────────────────────────────────────────────────
const orderRef = ref('')
const taskCount = ref(3)
const qtyMin = ref(1)
const qtyMax = ref(10)
const previewItems = ref([])
const availableDevices = ref([])
const loadingDevices = ref(false)
const submitting = ref(false)
const result = ref(null)
const recentOrders = ref([])

// ─── Mock Data ────────────────────────────────────────────
const PRODUCT_CATALOG = [
  { sku: 'EL-001', name: 'Đèn LED Panel 600x600' },
  { sku: 'EL-002', name: 'Đèn LED Downlight 12W' },
  { sku: 'EL-003', name: 'Đèn LED Ống T8 1.2m' },
  { sku: 'EL-004', name: 'Đèn LED Bulb 9W' },
  { sku: 'EL-005', name: 'Đèn LED Dây 5m RGB' },
  { sku: 'CB-001', name: 'Cáp điện VC 2x1.5mm' },
  { sku: 'CB-002', name: 'Cáp mạng CAT6 UTP' },
  { sku: 'CB-003', name: 'Dây HDMI 2.0 (3m)' },
  { sku: 'CB-004', name: 'Cáp USB-C to USB-C' },
  { sku: 'SW-001', name: 'Công tắc đơn Panasonic' },
  { sku: 'SW-002', name: 'Ổ cắm đôi có USB' },
  { sku: 'SW-003', name: 'Aptomat MCB 2P 20A' },
  { sku: 'MT-001', name: 'Motor DC 12V 300RPM' },
  { sku: 'MT-002', name: 'Servo SG90 180°' },
  { sku: 'MT-003', name: 'Step Motor NEMA17' },
  { sku: 'SN-001', name: 'Cảm biến nhiệt độ DS18B20' },
  { sku: 'SN-002', name: 'Cảm biến khoảng cách HC-SR04' },
  { sku: 'SN-003', name: 'Cảm biến ánh sáng BH1750' },
  { sku: 'SN-004', name: 'Cảm biến chuyển động PIR' },
  { sku: 'PC-001', name: 'Board ESP32 DevKitC' },
  { sku: 'PC-002', name: 'Raspberry Pi 4B (4GB)' },
  { sku: 'PC-003', name: 'Arduino Uno R3' },
  { sku: 'PW-001', name: 'Nguồn tổ ong 12V 10A' },
  { sku: 'PW-002', name: 'Adapter 5V 3A USB-C' },
  { sku: 'PW-003', name: 'Pin Li-Po 3.7V 2000mAh' },
  { sku: 'TL-001', name: 'Kìm bấm mạng RJ45' },
  { sku: 'TL-002', name: 'Mỏ hàn Hakko T12' },
  { sku: 'TL-003', name: 'Đồng hồ vạn năng DT830B' },
  { sku: 'BX-001', name: 'Hộp nhựa đựng linh kiện' },
  { sku: 'BX-002', name: 'Túi chống tĩnh điện 10x15cm' },
]

const totalQty = computed(() => previewItems.value.reduce((sum, i) => sum + (i.quantity || 0), 0))

// ─── Methods ──────────────────────────────────────────────
onMounted(async () => {
  generateOrderRef()
  await fetchDevices()
})

async function fetchDevices() {
  loadingDevices.value = true
  try {
    const res = await authFetch('/api/devices/')
    if (res.ok) {
      availableDevices.value = await res.json()
    }
  } finally {
    loadingDevices.value = false
  }
}

function generateOrderRef() {
  const now = new Date()
  const date = now.toISOString().slice(0, 10).replace(/-/g, '')
  const seq = String(Math.floor(Math.random() * 999) + 1).padStart(3, '0')
  orderRef.value = `ORD-${date}-${seq}`
}

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function shuffle(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

function generatePreview() {
  if (availableDevices.value.length === 0) return
  result.value = null

  const count = Math.min(taskCount.value, availableDevices.value.length)
  const selectedDevices = shuffle(availableDevices.value).slice(0, count)
  const selectedProducts = shuffle(PRODUCT_CATALOG).slice(0, count)

  previewItems.value = selectedDevices.map((device, i) => ({
    device_code: device.device_code,
    zone: device.zone || null,
    sku: selectedProducts[i]?.sku || `SKU-${randInt(100, 999)}`,
    productName: selectedProducts[i]?.name || `Sản phẩm test #${i + 1}`,
    quantity: randInt(qtyMin.value, qtyMax.value),
  }))
}

function shufflePreview() {
  generatePreview()
}

function removeItem(idx) {
  previewItems.value.splice(idx, 1)
}

function resetForm() {
  generateOrderRef()
  taskCount.value = 3
  qtyMin.value = 1
  qtyMax.value = 10
  previewItems.value = []
  result.value = null
}

async function submitOrder() {
  if (previewItems.value.length === 0) return
  submitting.value = true
  result.value = null

  const body = {
    order_ref: orderRef.value,
    items: previewItems.value.map(item => ({
      device_code: item.device_code,
      quantity: item.quantity,
      sku: item.sku,
    })),
  }

  try {
    const res = await authFetch('/api/orders/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    const data = await res.json()

    if (res.ok) {
      result.value = {
        ok: true,
        message: `Đơn "${orderRef.value}" đã được tạo với ${previewItems.value.length} tasks, tổng ${totalQty.value} sản phẩm.`,
      }
      // Add to recent list
      recentOrders.value.unshift({
        order_ref: orderRef.value,
        status: 'pending',
        taskCount: previewItems.value.length,
        totalQty: totalQty.value,
      })
      // Reset for next order
      previewItems.value = []
      generateOrderRef()
    } else {
      result.value = {
        ok: false,
        message: typeof data.detail === 'string' ? data.detail : data.detail?.message || JSON.stringify(data.detail) || 'Tạo đơn thất bại',
      }
    }
  } catch {
    result.value = { ok: false, message: 'Lỗi kết nối đến server' }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
/* ─── Generator Layout ──────────────────────────────────── */
.gen-row {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
  margin-bottom: 20px;
}

.gen-settings .card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ─── Form Groups ───────────────────────────────────────── */
.form-group {
  margin-bottom: 18px;
}
.form-group label {
  display: block;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-heading);
  margin-bottom: 6px;
}
.form-hint {
  display: block;
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.input-with-btn {
  display: flex;
  gap: 6px;
}
.input-with-btn .input {
  flex: 1;
}

/* Task count */
.task-count-control {
  display: flex;
  align-items: center;
  gap: 6px;
  width: fit-content;
}
.task-count-input {
  width: 70px !important;
  text-align: center;
  font-weight: 700;
  font-size: 1.1rem;
}

/* Range inputs */
.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}
.range-input {
  width: 90px !important;
  text-align: center;
}
.range-sep {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

/* ─── Info Cards ────────────────────────────────────────── */
.gen-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.info-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
}
.info-icon {
  font-size: 1.6rem;
  color: var(--primary);
  width: 36px;
  text-align: center;
}
.info-body {
  flex: 1;
}
.info-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-heading);
  line-height: 1.2;
  word-break: break-all;
}
.info-label {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 2px;
}
.info-loading {
  opacity: 0.7;
}

/* ─── Preview Section ───────────────────────────────────── */
.preview-section {
  margin-bottom: 20px;
}
.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.preview-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
}
.preview-actions {
  display: flex;
  gap: 8px;
}

/* Table tweaks */
.th-stt, .td-stt {
  width: 40px;
  text-align: center;
  color: var(--text-muted);
}
.sku-code {
  background: var(--bg-elevated);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.88em;
  font-family: 'Consolas', 'Courier New', monospace;
  color: var(--primary-dark);
}
.product-name {
  color: var(--text-secondary);
  font-size: 0.92em;
}
.qty-input {
  width: 75px !important;
  text-align: center;
  font-weight: 600;
}
.badge-zone {
  background: var(--bg-active);
  color: var(--text-heading);
  font-size: 0.78em;
}
.btn-remove {
  color: var(--text-muted);
  border: none;
}
.btn-remove:hover {
  color: var(--danger);
  background: rgba(237, 85, 101, 0.08);
}
.text-right {
  text-align: right;
}
tfoot td {
  border-top: 2px solid var(--border);
  font-size: 0.95em;
}

/* ─── Result Banner ─────────────────────────────────────── */
.result-banner {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  margin-bottom: 20px;
}
.result-icon {
  font-size: 1.8rem;
}
.result-body {
  flex: 1;
}
.result-body strong {
  font-size: 1rem;
}
.result-body p {
  font-size: 0.85rem;
  margin-top: 2px;
  color: var(--text-secondary);
}
.result-success {
  border-left: 4px solid var(--primary);
  background: rgba(26, 179, 148, 0.06);
}
.result-success .result-icon {
  color: var(--primary);
}
.result-error {
  border-left: 4px solid var(--danger);
  background: rgba(237, 85, 101, 0.06);
}
.result-error .result-icon {
  color: var(--danger);
}

/* ─── Recent Orders ─────────────────────────────────────── */
.recent-section {
  margin-bottom: 20px;
}
.recent-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  margin-bottom: 12px;
}
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.recent-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 18px;
}
.recent-ref {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.recent-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
}

/* ─── Responsive ────────────────────────────────────────── */
@media (max-width: 900px) {
  .gen-row {
    grid-template-columns: 1fr;
  }
  .gen-info {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .info-card {
    flex: 1;
    min-width: 140px;
  }
}
</style>
