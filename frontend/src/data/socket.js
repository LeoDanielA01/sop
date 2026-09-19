import { io } from 'socket.io-client'

let socket = null

function address() {
  const { protocol, hostname, origin } = window.location
  const site = window.site_name || hostname

  if (!window.dev_server) return `${origin}/${site}`

  return `${protocol}//${hostname}:${window.socketio_port || 9000}/${site}`
}

export function useSocket() {
  if (socket) return socket

  socket = io(address(), {
    withCredentials: true,
    reconnectionAttempts: 20,
    transports: ['websocket', 'polling'],
  })

  return socket
}
