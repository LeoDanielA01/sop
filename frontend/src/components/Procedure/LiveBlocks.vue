<template>
  <Teleport v-for="item in items" :key="item.id" :to="item.host">
    <Tooltip :text="tip(item)">
      <span
        v-if="item.kind === 'live'"
        class="inline-flex items-center gap-1 whitespace-nowrap rounded-2 border px-1.5 py-px align-baseline text-[0.95em]"
        :class="pill(item)"
      >
        <span
          :class="state(item).loading ? 'lucide-loader-circle animate-spin' : state(item).missing ? 'lucide-triangle-alert' : 'lucide-activity'"
          class="size-3 shrink-0"
          aria-hidden="true"
        />
        {{ state(item).missing ? item.fallback : state(item).value || item.fallback }}
      </span>

      <span
        v-else
        class="inline-flex max-w-full items-start gap-1.5 rounded-2 border px-2 py-0.5 align-baseline"
        :class="badge(item)"
        role="status"
      >
        <span :class="icon(item)" class="mt-[0.2em] size-4 shrink-0" aria-hidden="true" />
        <span class="min-w-0">
          <span class="text-ink-gray-9">{{ item.fallback }}</span>
          <span v-if="!state(item).loading" class="ml-1.5 text-sm text-ink-gray-5">
            {{ state(item).missing ? state(item).message : `(${state(item).value})` }}
          </span>
        </span>
      </span>
    </Tooltip>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { Tooltip, call } from 'frappe-ui'
import { translate as __ } from '@/translation'

const REFRESH = 120000

const props = defineProps({
  root: { type: [Object, null], default: null },
  sop: { type: String, default: '' },
  revision: { type: [String, Number, null], default: null },
  content: { type: String, default: '' },
})

const items = shallowRef([])
const results = ref({})
const loading = ref(false)
let timer = null

function scan() {
  const root = props.root
  if (!root) return

  const found = []
  for (const anchor of root.querySelectorAll('a[href^="#live:"], a[href^="#check:"]')) {
    const href = anchor.getAttribute('href')
    const host = document.createElement('span')

    found.push({
      id: `${found.length}:${href}`,
      href,
      host,
      kind: href.startsWith('#check:') ? 'check' : 'live',
      fallback: anchor.textContent.trim(),
    })

    anchor.replaceWith(host)
  }

  items.value = found
  if (found.length) load()
}

let latest = 0

async function load() {
  if (!props.sop || !items.value.length) return

  const request = ++latest
  loading.value = true

  try {
    const found = await call('sop.api.live.evaluate', { sop: props.sop, revision: props.revision })
    if (request === latest) results.value = found || {}
  } catch {
    if (request === latest) results.value = {}
  } finally {
    if (request === latest) loading.value = false
  }
}

function state(item) {
  const found = results.value[item.href]
  if (found) return found
  if (loading.value) return { loading: true }
  return { missing: true, message: __('Could not read this right now.') }
}

function tip(item) {
  const found = state(item)
  if (found.loading) return __('Checking…')
  if (found.missing) return found.message
  return `${found.title} · ${found.label} · ${__('live')}`
}

function pill(item) {
  const found = state(item)
  if (found.missing) return 'border-outline-amber-2 bg-surface-amber-1 text-ink-amber-6'
  if (found.tone === 'red') return 'border-outline-red-2 bg-surface-red-1 text-ink-red-6'
  if (found.tone === 'amber') return 'border-outline-amber-2 bg-surface-amber-1 text-ink-amber-6'
  return 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8'
}

function badge(item) {
  const found = state(item)
  if (found.loading) return 'border-outline-gray-2 bg-surface-gray-1'
  if (found.missing) return 'border-outline-amber-2 bg-surface-amber-1'
  if (found.ok) return 'border-outline-gray-2 bg-surface-base'
  return 'border-outline-red-2 bg-surface-red-1'
}

function icon(item) {
  const found = state(item)
  if (found.loading) return 'lucide-loader-circle animate-spin text-ink-gray-5'
  if (found.missing) return 'lucide-triangle-alert text-ink-amber-6'
  return found.ok ? 'lucide-circle-check text-ink-green-3' : 'lucide-circle-x text-ink-red-3'
}

watch(
  () => [props.root, props.content],
  () => scan(),
  { immediate: true, flush: 'post' },
)

function refresh() {
  if (document.visibilityState === 'visible') load()
}

onMounted(() => {
  timer = setInterval(refresh, REFRESH)
  window.addEventListener('focus', refresh)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  window.removeEventListener('focus', refresh)
})
</script>
