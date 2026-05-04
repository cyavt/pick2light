/**
 * WebSocket composable for real-time dashboard updates.
 */

import { ref, onMounted, onUnmounted } from 'vue'

export function useWebSocket(channel = 'dashboard') {
  const data = ref(null)
  const isConnected = ref(false)
  let ws = null

  const connect = () => {
    const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.host}`
    ws = new WebSocket(`${wsUrl}/ws/${channel}`)

    ws.onopen = () => {
      isConnected.value = true
      console.log(`[WS] Connected to ${channel}`)
    }

    ws.onmessage = (event) => {
      data.value = JSON.parse(event.data)
    }

    ws.onclose = () => {
      isConnected.value = false
      console.log(`[WS] Disconnected from ${channel}, reconnecting in 3s...`)
      setTimeout(connect, 3000)
    }

    ws.onerror = (error) => {
      console.error('[WS] Error:', error)
    }
  }

  onMounted(connect)
  onUnmounted(() => {
    if (ws) ws.close()
  })

  return { data, isConnected }
}
