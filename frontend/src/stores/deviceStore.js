/**
 * Pinia store for device state management.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDeviceStore = defineStore('devices', () => {
  const devices = ref([])
  const loading = ref(false)

  async function fetchDevices() {
    loading.value = true
    try {
      const response = await fetch('/api/devices')
      devices.value = await response.json()
    } catch (error) {
      console.error('Failed to fetch devices:', error)
    } finally {
      loading.value = false
    }
  }

  function updateDevice(deviceId, update) {
    const index = devices.value.findIndex(d => d.device_id === deviceId)
    if (index !== -1) {
      devices.value[index] = { ...devices.value[index], ...update }
    }
  }

  return { devices, loading, fetchDevices, updateDevice }
})
