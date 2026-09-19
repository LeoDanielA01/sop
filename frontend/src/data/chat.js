import { call, createResource, toast } from 'frappe-ui'
import { computed, reactive } from 'vue'
import { refreshNotifications } from '@/data/notifications'
import { session } from '@/data/session'
import { useSocket } from '@/data/socket'
import { alertTone, askToNotify, chime, notify } from '@/data/sound'
import { translate as __ } from '@/translation'

const QUIET = ['Email', 'Call']
const TYPING_FOR = 4000

export const chat = reactive({
  open: false,
  person: null,
  room: null,
  sop: null,
  messages: [],
  loading: false,
  sending: false,
  error: null,
})

export const typing = reactive({})

export const mail = reactive({
  open: false,
  person: null,
  sop: null,
  subject: '',
})

export const threads = createResource({ url: 'sop.api.chat.threads' })

export const chatUnread = createResource({ url: 'sop.api.chat.unread', auto: true })

export const chatUnreadCount = computed(() => chatUnread.data?.total || 0)

export function roomUnread(sop) {
  return chatUnread.data?.rooms?.[sop] || 0
}

export function attachmentUrl(message) {
  return `/api/method/sop.api.chat.attachment?message=${encodeURIComponent(message.name)}`
}

const typingTimers = {}
let lastTyping = 0

function me() {
  return session.user.name
}

function keyOf(message) {
  if (message.channel === 'Procedure') return `sop:${message.sop}`
  return `user:${message.sender === me() ? message.recipient : message.sender}`
}

export function currentKey() {
  if (chat.room) return `sop:${chat.room.sop}`
  if (chat.person) return `user:${chat.person.name}`
  return null
}

function viewing(key) {
  return chat.open && currentKey() === key && document.visibilityState === 'visible'
}

function reset() {
  chat.messages = []
  chat.error = null
  chat.loading = true
}

function failed(error) {
  chat.error = error.messages?.[0] || error.message
}

export function showInbox() {
  askToNotify()
  chat.person = null
  chat.room = null
  chat.open = true
  threads.reload()
}

export async function openChat(person, sop = null) {
  askToNotify()
  chat.room = null
  chat.person = person
  chat.sop = sop
  chat.open = true
  reset()

  try {
    chat.messages = await call('sop.api.chat.history', { user: person.name })
    markRead()
  } catch (error) {
    failed(error)
  } finally {
    chat.loading = false
  }
}

export async function openRoom(sop) {
  askToNotify()
  chat.person = null
  chat.sop = sop
  chat.room = { sop, sop_no: sop, title: '', members: [] }
  chat.open = true
  reset()

  try {
    const [info, messages] = await Promise.all([
      call('sop.api.chat.room', { sop }),
      call('sop.api.chat.history', { sop }),
    ])
    if (chat.room?.sop !== sop) return
    chat.room = info
    chat.messages = messages
    markRead()
  } catch (error) {
    failed(error)
  } finally {
    chat.loading = false
  }
}

export async function loadEarlier() {
  if (!chat.messages.length) return 0

  const scope = chat.room ? { sop: chat.room.sop } : { user: chat.person.name }
  const earlier = await call('sop.api.chat.history', { ...scope, before: chat.messages[0].creation })

  chat.messages = [...earlier, ...chat.messages]
  return earlier.length
}

export async function sendMessage(content, file = null) {
  if (!currentKey() || (!content.trim() && !file)) return false

  const scope = chat.room
    ? { room: 1, sop: chat.room.sop }
    : { to: chat.person.name, sop: chat.sop }

  chat.sending = true
  chat.error = null

  try {
    accept(await call('sop.api.chat.send', { ...scope, content, file }))
    lastTyping = 0
    return true
  } catch (error) {
    failed(error)
    return false
  } finally {
    chat.sending = false
  }
}

export function announceTyping() {
  if (!currentKey() || Date.now() - lastTyping < 2500) return
  lastTyping = Date.now()

  const scope = chat.room ? { sop: chat.room.sop } : { to: chat.person.name }
  call('sop.api.chat.typing', scope).catch(() => {})
}

function stopTyping(key, user) {
  clearTimeout(typingTimers[`${key}|${user}`])
  if (!typing[key]) return

  delete typing[key][user]
  if (!Object.keys(typing[key]).length) delete typing[key]
}

function heardTyping({ from, sop }) {
  const key = sop ? `sop:${sop}` : `user:${from.name}`
  const timer = `${key}|${from.name}`

  typing[key] = { ...(typing[key] || {}), [from.name]: from.full_name }

  clearTimeout(typingTimers[timer])
  typingTimers[timer] = setTimeout(() => stopTyping(key, from.name), TYPING_FOR)
}

function markRead() {
  const scope = chat.room ? { sop: chat.room.sop } : chat.person ? { user: chat.person.name } : null
  if (!scope) return

  call('sop.api.chat.mark_read', scope)
    .then(() => chatUnread.reload())
    .catch(() => {})
}

function preview(message) {
  if (message.kind === 'File') return message.content || __('Sent a file: {0}').format(message.file_name)
  return message.content
}

function accept(message) {
  const key = keyOf(message)

  if (currentKey() === key && !chat.messages.some((row) => row.name === message.name)) {
    chat.messages.push(message)
  }

  stopTyping(key, message.sender)

  if (message.sender === me()) return

  if (viewing(key)) {
    markRead()
    return
  }

  chatUnread.reload()

  if (QUIET.includes(message.kind)) return

  const name = message.sender_name || message.sender
  const room = message.room
  const title = room ? __('{0} in {1}').format(name, room.sop_no) : name
  const open = room
    ? () => openRoom(room.sop)
    : () => openChat({ name: message.sender, full_name: name, image: null })

  chime()
  toast.info(`${title}: ${preview(message)}`)
  notify(title, preview(message), open)
}

export function openMail(person, sop = null, subject = '') {
  mail.person = person
  mail.sop = sop
  mail.subject = subject
  mail.open = true
}

export function sendMail(values) {
  return call('sop.api.chat.mail', { to: mail.person.name, sop: mail.sop, ...values })
}

export function applyTemplate(template) {
  return call('sop.api.chat.use_template', { template, to: mail.person.name, sop: mail.sop })
}

export function saveTemplate(values) {
  return call('sop.api.chat.save_template', values)
}

export function listenForMessages() {
  const socket = useSocket()

  socket.on('sop_message', (message) => {
    accept(message)
    if (chat.open && !currentKey()) threads.reload()
  })

  socket.on('sop_typing', heardTyping)

  socket.on('sop_message_read', ({ by }) => {
    if (chat.person?.name !== by) return
    for (const row of chat.messages) {
      if (row.sender === me()) row.read = 1
    }
  })

  socket.on('notification', () => {
    alertTone()
    refreshNotifications()
  })

  socket.on('connect', () => {
    chatUnread.reload()
    refreshNotifications()
  })

  document.addEventListener('visibilitychange', () => {
    const key = currentKey()
    if (key && viewing(key)) markRead()
  })
}
