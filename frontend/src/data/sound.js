import { reactive, watch } from 'vue'

const KEY = 'sop:sounds'

function stored() {
  try {
    return localStorage.getItem(KEY) !== 'off'
  } catch {
    return true
  }
}

export const sounds = reactive({ on: stored() })

watch(
  () => sounds.on,
  (on) => {
    try {
      localStorage.setItem(KEY, on ? 'on' : 'off')
    } catch {}
  },
)

let context = null
let loop = null

function audio() {
  if (typeof AudioContext === 'undefined') return null
  if (!context) context = new AudioContext()
  if (context.state === 'suspended') context.resume().catch(() => {})
  return context
}

function note(frequency, start, length, volume = 0.08) {
  const ctx = audio()
  if (!ctx) return

  const oscillator = ctx.createOscillator()
  const gain = ctx.createGain()
  const at = ctx.currentTime + start

  oscillator.type = 'sine'
  oscillator.frequency.value = frequency
  gain.gain.setValueAtTime(0, at)
  gain.gain.linearRampToValueAtTime(volume, at + 0.02)
  gain.gain.exponentialRampToValueAtTime(0.0001, at + length)

  oscillator.connect(gain).connect(ctx.destination)
  oscillator.start(at)
  oscillator.stop(at + length + 0.05)
}

export function unlockSound() {
  audio()
}

export function chime() {
  if (!sounds.on) return
  note(880, 0, 0.25)
  note(1320, 0.12, 0.35)
}

export function alertTone() {
  if (!sounds.on) return
  note(660, 0, 0.2)
  note(990, 0.14, 0.3)
}

export function startRinging(incoming) {
  stopRinging()

  const play = incoming
    ? () => {
        if (!sounds.on) return
        note(784, 0, 0.35, 0.1)
        note(988, 0.4, 0.35, 0.1)
        note(784, 0.8, 0.35, 0.1)
        note(988, 1.2, 0.35, 0.1)
      }
    : () => {
        note(440, 0, 0.9, 0.05)
        note(480, 0, 0.9, 0.05)
      }

  play()
  loop = setInterval(play, incoming ? 2600 : 3000)
}

export function stopRinging() {
  clearInterval(loop)
  loop = null
}

export function askToNotify() {
  if (typeof Notification === 'undefined' || Notification.permission !== 'default') return
  Notification.requestPermission().catch(() => {})
}

export function notify(title, body, onClick) {
  if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return null
  if (document.visibilityState === 'visible' && document.hasFocus()) return null

  const shown = new Notification(title, { body, icon: '/assets/sop/images/sop-mark.svg', tag: title })
  shown.onclick = () => {
    window.focus()
    onClick?.()
    shown.close()
  }
  return shown
}
