import { call as request, toast } from 'frappe-ui'
import { reactive } from 'vue'
import { useSocket } from '@/data/socket'
import { translate as __ } from '@/translation'

const RING_FOR = 40000
const ICE_SERVERS = window.sop_ice_servers || [{ urls: 'stun:stun.l.google.com:19302' }]

export const phone = reactive({
  state: 'idle',
  id: null,
  person: null,
  sop: null,
  outgoing: false,
  muted: false,
  startedAt: null,
  note: '',
})

let peer = null
let local = null
let pending = []
let ringTimer = null
let dropTimer = null
let tone = null

const speaker = typeof Audio !== 'undefined' ? new Audio() : null
if (speaker) speaker.autoplay = true

function signal(kind, data = null, to = phone.person?.name, id = phone.id) {
  return request('sop.api.calls.signal', { to, kind, call: id, data }).catch(() => {})
}

function logCall(outcome) {
  const duration = phone.startedAt ? Math.round((Date.now() - phone.startedAt) / 1000) : 0

  request('sop.api.calls.log', {
    to: phone.person.name,
    outcome,
    duration,
    sop: phone.sop,
  }).catch(() => {})
}

async function microphone() {
  if (!navigator.mediaDevices?.getUserMedia) {
    toast.error(__('Calls need a secure (https) connection.'))
    return null
  }

  try {
    return await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
  } catch {
    toast.error(__('Allow microphone access to make calls.'))
    return null
  }
}

function ring(outgoing) {
  quiet()

  try {
    const context = new AudioContext()
    const beep = () => {
      const oscillator = context.createOscillator()
      const gain = context.createGain()
      oscillator.frequency.value = outgoing ? 425 : 520
      gain.gain.value = 0.06
      oscillator.connect(gain).connect(context.destination)
      oscillator.start()
      oscillator.stop(context.currentTime + (outgoing ? 1 : 0.6))
    }

    beep()
    tone = { context, timer: setInterval(beep, outgoing ? 3000 : 1800) }
  } catch {
    tone = null
  }
}

function quiet() {
  if (!tone) return
  clearInterval(tone.timer)
  tone.context.close().catch(() => {})
  tone = null
}

function connect() {
  peer = new RTCPeerConnection({ iceServers: ICE_SERVERS })

  for (const track of local.getTracks()) peer.addTrack(track, local)

  peer.onicecandidate = ({ candidate }) => {
    if (candidate) signal('candidate', candidate.toJSON())
  }

  peer.ontrack = ({ streams }) => {
    if (speaker) speaker.srcObject = streams[0]
  }

  peer.onconnectionstatechange = () => {
    const state = peer?.connectionState

    if (state === 'connected') {
      clearTimeout(dropTimer)
      if (phone.state !== 'live') {
        phone.state = 'live'
        phone.startedAt = Date.now()
      }
    } else if (state === 'disconnected') {
      clearTimeout(dropTimer)
      dropTimer = setTimeout(() => hangUp(__('Connection lost')), 8000)
    } else if (state === 'failed') {
      hangUp(__('Could not connect'))
    }
  }
}

async function flush() {
  for (const candidate of pending) {
    await peer.addIceCandidate(candidate).catch(() => {})
  }
  pending = []
}

function finish(note) {
  quiet()
  clearTimeout(ringTimer)
  clearTimeout(dropTimer)

  local?.getTracks().forEach((track) => track.stop())
  peer?.close()
  if (speaker) speaker.srcObject = null

  local = null
  peer = null
  pending = []

  const id = phone.id
  phone.state = 'ended'
  phone.note = note

  setTimeout(() => {
    if (phone.id !== id || phone.state !== 'ended') return
    Object.assign(phone, {
      state: 'idle',
      id: null,
      person: null,
      sop: null,
      outgoing: false,
      muted: false,
      startedAt: null,
      note: '',
    })
  }, 1800)
}

export async function startCall(person, sop = null) {
  if (phone.state !== 'idle' && phone.state !== 'ended') {
    toast.warning(__('You are already on a call.'))
    return
  }

  local = await microphone()
  if (!local) return

  Object.assign(phone, {
    state: 'calling',
    id: crypto.randomUUID(),
    person,
    sop,
    outgoing: true,
    muted: false,
    startedAt: null,
    note: '',
  })

  ring(true)
  signal('ring', { sop })

  ringTimer = setTimeout(() => {
    if (phone.state !== 'calling') return
    signal('cancel')
    logCall('Missed')
    finish(__('No answer'))
  }, RING_FOR)
}

export async function answer() {
  if (phone.state !== 'ringing') return

  quiet()
  clearTimeout(ringTimer)

  local = await microphone()
  if (!local) {
    decline()
    return
  }

  phone.state = 'connecting'
  connect()
  signal('accept')
}

export function decline() {
  if (phone.state !== 'ringing') return
  signal('decline')
  finish(__('Declined'))
}

export function hangUp(note = __('Call ended')) {
  if (phone.state === 'idle' || phone.state === 'ended') return

  if (phone.state === 'calling') {
    signal('cancel')
    logCall('Missed')
    finish(__('Cancelled'))
    return
  }

  if (phone.state === 'ringing') {
    decline()
    return
  }

  signal('end')
  if (phone.outgoing) logCall(phone.startedAt ? 'Completed' : 'Missed')
  finish(note)
}

export function toggleMute() {
  if (!local) return
  phone.muted = !phone.muted
  local.getAudioTracks().forEach((track) => (track.enabled = !phone.muted))
}

async function receive({ kind, call: id, data, from }) {
  if (kind === 'ring') {
    if (phone.state !== 'idle' && phone.state !== 'ended') {
      signal('busy', null, from.name, id)
      return
    }

    Object.assign(phone, {
      state: 'ringing',
      id,
      person: from,
      sop: data?.sop || null,
      outgoing: false,
      muted: false,
      startedAt: null,
      note: '',
    })

    ring(false)
    ringTimer = setTimeout(() => {
      if (phone.state === 'ringing') finish(__('Missed call'))
    }, RING_FOR)
    return
  }

  if (kind === 'taken') {
    if (id === phone.id && phone.state === 'ringing') finish(__('Answered elsewhere'))
    return
  }

  if (id !== phone.id || from.name !== phone.person?.name) return

  if (kind === 'accept' && phone.state === 'calling') {
    quiet()
    clearTimeout(ringTimer)
    phone.state = 'connecting'
    connect()

    const offer = await peer.createOffer()
    await peer.setLocalDescription(offer)
    signal('offer', peer.localDescription.toJSON())
  } else if (kind === 'offer' && peer) {
    await peer.setRemoteDescription(data)
    await flush()

    const reply = await peer.createAnswer()
    await peer.setLocalDescription(reply)
    signal('answer', peer.localDescription.toJSON())
  } else if (kind === 'answer' && peer) {
    await peer.setRemoteDescription(data)
    await flush()
  } else if (kind === 'candidate') {
    if (peer?.remoteDescription) await peer.addIceCandidate(data).catch(() => {})
    else pending.push(data)
  } else if (kind === 'decline' && phone.state === 'calling') {
    logCall('Declined')
    finish(__('Declined'))
  } else if (kind === 'busy' && phone.state === 'calling') {
    logCall('Busy')
    finish(__('Busy on another call'))
  } else if (kind === 'cancel') {
    finish(__('Missed call'))
  } else if (kind === 'end') {
    if (phone.outgoing) logCall(phone.startedAt ? 'Completed' : 'Missed')
    finish(__('Call ended'))
  }
}

export function listenForCalls() {
  useSocket().on('sop_call', (payload) => {
    receive(payload).catch(() => hangUp(__('Could not connect')))
  })

  window.addEventListener('pagehide', () => {
    if (phone.state !== 'idle' && phone.state !== 'ended') signal('end')
  })
}
