import { io } from 'socket.io-client'
import { reactive } from 'vue'

export const realtime = reactive({ connected: false, error: null, address: '' })

let socket = null

function address() {
  const { protocol, hostname, port } = window.location
  const site = window.site_name || hostname

  if (!port) return `${protocol}//${hostname}/${site}`

  return `http://${hostname}:${window.socketio_port || 9000}/${site}`
}

export function useSocket() {
  if (socket) return socket

  realtime.address = address()

  socket = io(realtime.address, {
    withCredentials: true,
    reconnection: true,
    reconnectionDelayMax: 10000,
  })

  socket.on('connect', () => {
    realtime.connected = true
    realtime.error = null
  })

  socket.on('disconnect', () => {
    realtime.connected = false
  })

  socket.on('connect_error', (error) => {
    realtime.connected = false
    realtime.error = error.message
    console.warn(`[sop] realtime connection to ${address()} failed: ${error.message}`)
  })

  return socket
}
