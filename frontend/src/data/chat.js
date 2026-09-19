import { call, createResource, toast } from 'frappe-ui'
import { computed, reactive } from 'vue'
import { refreshNotifications } from '@/data/notifications'
import { session } from '@/data/session'
import { useSocket } from '@/data/socket'
import { alertTone, askToNotify, chime, notify } from '@/data/sound'
import { translate as __ } from '@/translation'

export const chat = reactive({
  open: false,
  person: null,
  sop: null,
  messages: [],
  loading: false,
  sending: false,
  error: null,
})

export const mail = reactive({
  open: false,
  person: null,
  sop: null,
  subject: '',
})

export const threads = createResource({ url: 'sop.api.chat.threads' })

export const chatUnread = createResource({ url: 'sop.api.chat.unread', auto: true })

export const chatUnreadCount = computed(() => chatUnread.data || 0)

function other(message) {
  return message.sender === session.user.name ? message.recipient : message.sender
}

function viewing(user) {
  return chat.open && chat.person?.name === user && document.visibilityState === 'visible'
}

export function showInbox() {
  askToNotify()
  chat.person = null
  chat.open = true
  threads.reload()
}

export async function openChat(person, sop = null) {
  askToNotify()
  chat.person = person
  chat.sop = sop
  chat.open = true
  chat.messages = []
  chat.error = null
  chat.loading = true

  try {
    chat.messages = await call('sop.api.chat.history', { user: person.name })
    markRead()
  } catch (error) {
    chat.error = error.messages?.[0] || error.message
  } finally {
    chat.loading = false
  }
}

export async function loadEarlier() {
  if (!chat.person || !chat.messages.length) return

  const earlier = await call('sop.api.chat.history', {
    user: chat.person.name,
    before: chat.messages[0].creation,
  })

  chat.messages = [...earlier, ...chat.messages]
  return earlier.length
}

export async function sendMessage(content) {
  if (!chat.person || !content.trim()) return false

  chat.sending = true
  chat.error = null

  try {
    accept(await call('sop.api.chat.send', { to: chat.person.name, content, sop: chat.sop }))
    return true
  } catch (error) {
    chat.error = error.messages?.[0] || error.message
    return false
  } finally {
    chat.sending = false
  }
}

function markRead() {
  if (!chat.person) return

  call('sop.api.chat.mark_read', { user: chat.person.name })
    .then(() => chatUnread.reload())
    .catch(() => {})
}

function accept(message) {
  const person = other(message)

  if (chat.person?.name === person && !chat.messages.some((row) => row.name === message.name)) {
    chat.messages.push(message)
  }

  if (message.recipient !== session.user.name) return

  if (viewing(person)) {
    markRead()
    return
  }

  chatUnread.reload()

  if (message.kind !== 'Text') return

  const name = message.sender_name || person
  chime()
  toast.info(__('{0}: {1}').format(name, message.content))
  notify(name, message.content, () => openChat({ name: person, full_name: name, image: null }))
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
    if (chat.open && !chat.person) threads.reload()
  })

  socket.on('sop_message_read', ({ by }) => {
    if (chat.person?.name !== by) return
    for (const row of chat.messages) {
      if (row.sender === session.user.name) row.read = 1
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
    if (chat.person && viewing(chat.person.name)) markRead()
  })
}
