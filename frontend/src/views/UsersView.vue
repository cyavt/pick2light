<template>
  <div class="users-page fade-in">
    <div class="page-header">
      <div>
        <h1><i class="fa fa-users"></i> Quản lý tài khoản</h1>
        <p>Tạo và quản lý người dùng hệ thống</p>
      </div>
      <button class="btn btn-primary" @click="showModal = true">
        <i class="fa fa-plus"></i> Tạo tài khoản
      </button>
    </div>

    <!-- Users Table -->
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Vai trò</th>
            <th>Trạng thái</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="4" class="text-center text-muted">
              <i class="fa fa-spinner fa-spin"></i> Đang tải...
            </td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td colspan="4" class="text-center text-muted">Chưa có tài khoản nào</td>
          </tr>
          <tr v-for="u in users" :key="u.id">
            <td>
              <div class="user-cell">
                <div class="user-cell-avatar">{{ u.username[0].toUpperCase() }}</div>
                <strong>{{ u.username }}</strong>
              </div>
            </td>
            <td>
              <span class="badge" :class="'badge-' + u.role">{{ roleLabels[u.role] }}</span>
            </td>
            <td>
              <span class="badge" :class="u.is_active ? 'badge-online' : 'badge-offline'">
                {{ u.is_active ? 'Hoạt động' : 'Vô hiệu' }}
              </span>
            </td>
            <td>
              <div v-if="u.username !== currentUser?.username" class="action-btns">
                <button
                  class="btn btn-sm"
                  :class="u.is_active ? 'btn-ghost' : 'btn-success'"
                  @click="toggleUser(u)"
                >
                  <i class="fa" :class="u.is_active ? 'fa-ban' : 'fa-check'"></i>
                  {{ u.is_active ? 'Vô hiệu' : 'Kích hoạt' }}
                </button>
                <button class="btn btn-sm btn-danger" @click="confirmDelete(u)">
                  <i class="fa fa-trash"></i> Xoá
                </button>
              </div>
              <span v-else class="text-muted" style="font-size:0.8em;">— Tài khoản hiện tại</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create User Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal card">
        <h3><i class="fa fa-user-plus"></i> Tạo tài khoản mới</h3>

        <div v-if="formError" class="form-error">
          <i class="fa fa-exclamation-circle"></i> {{ formError }}
        </div>

        <div class="modal-form">
          <label>Tên đăng nhập</label>
          <input class="input" v-model="form.username" placeholder="Nhập username..." :disabled="creating" />

          <label>Mật khẩu</label>
          <input class="input" type="password" v-model="form.password" placeholder="Nhập mật khẩu..." :disabled="creating" />

          <label>Vai trò</label>
          <select class="input" v-model="form.role" :disabled="creating">
            <option value="admin">Admin — Quản trị toàn quyền</option>
            <option value="supervisor">Supervisor — Giám sát</option>
            <option value="picker">Picker — Nhân viên pick</option>
          </select>
        </div>

        <div class="modal-actions">
          <button class="btn btn-ghost" @click="closeModal" :disabled="creating">Huỷ</button>
          <button
            class="btn btn-primary"
            @click="createUser"
            :disabled="creating || !form.username || !form.password"
          >
            <i v-if="creating" class="fa fa-spinner fa-spin"></i>
            <span v-else>Tạo tài khoản</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal card">
        <h3 class="delete-title"><i class="fa fa-exclamation-triangle text-danger"></i> Xác nhận xoá</h3>
        <p class="delete-msg">
          Bạn có chắc muốn xoá tài khoản <strong>{{ deleteTarget.username }}</strong>?
          <br>Hành động này không thể hoàn tác.
        </p>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="deleteTarget = null">Huỷ</button>
          <button class="btn btn-danger" @click="deleteUser" :disabled="deleting">
            <i v-if="deleting" class="fa fa-spinner fa-spin"></i>
            <span v-else><i class="fa fa-trash"></i> Xoá</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'

const { authFetch, user: currentUser } = useAuth()

const users = ref([])
const loading = ref(false)
const showModal = ref(false)
const creating = ref(false)
const formError = ref(null)
const form = ref({ username: '', password: '', role: 'picker' })
const deleteTarget = ref(null)
const deleting = ref(false)

const roleLabels = {
  admin: 'Admin',
  supervisor: 'Supervisor',
  picker: 'Picker',
}

onMounted(() => fetchUsers())

async function fetchUsers() {
  loading.value = true
  try {
    const res = await authFetch('/auth/users/')
    if (res.ok) {
      users.value = await res.json()
    }
  } finally {
    loading.value = false
  }
}

async function createUser() {
  creating.value = true
  formError.value = null
  try {
    const res = await authFetch('/auth/users/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })
    if (res.ok) {
      closeModal()
      await fetchUsers()
    } else {
      const data = await res.json().catch(() => ({}))
      formError.value = data.detail || 'Tạo tài khoản thất bại'
    }
  } catch {
    formError.value = 'Lỗi kết nối'
  } finally {
    creating.value = false
  }
}

async function toggleUser(u) {
  const res = await authFetch(`/auth/users/${u.id}/toggle`, { method: 'PUT' })
  if (res.ok) {
    const data = await res.json()
    u.is_active = data.is_active
  }
}

function confirmDelete(u) {
  deleteTarget.value = u
}

async function deleteUser() {
  deleting.value = true
  try {
    const res = await authFetch(`/auth/users/${deleteTarget.value.id}`, { method: 'DELETE' })
    if (res.ok) {
      deleteTarget.value = null
      await fetchUsers()
    }
  } finally {
    deleting.value = false
  }
}

function closeModal() {
  showModal.value = false
  formError.value = null
  form.value = { username: '', password: '', role: 'picker' }
}
</script>

<style scoped>
.text-center { text-align: center; }
.text-muted { color: var(--text-muted); }

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.user-cell-avatar {
  width: 32px;
  height: 32px;
  background: var(--primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.8rem;
  color: #fff;
}

.badge-admin { background: var(--primary); color: #fff; }
.badge-supervisor { background: var(--info); color: #fff; }
.badge-picker { background: var(--warning); color: #fff; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  width: 440px;
  max-width: 90vw;
}
.modal h3 {
  font-size: 1.1rem;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.modal-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.modal-form label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-top: 4px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.form-error {
  background: rgba(237, 85, 101, 0.1);
  border: 1px solid rgba(237, 85, 101, 0.3);
  color: var(--danger);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 0.85em;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.action-btns {
  display: flex;
  gap: 6px;
}
.delete-title {
  color: var(--danger);
}
.delete-msg {
  font-size: 0.9em;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: 0;
}
.text-danger {
  color: var(--danger);
}
</style>
