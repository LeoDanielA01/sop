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

  <Teleport v-for="item in asks" :key="item.id" :to="item.host">
    <div class="my-4 rounded-3 border border-outline-gray-2 bg-surface-gray-1 px-4 py-3">
      <p class="flex items-start gap-2 text-base font-medium text-ink-gray-9">
        <span
          class="lucide-message-circle-question mt-[0.2em] size-4 shrink-0 text-ink-gray-5"
          aria-hidden="true"
        />
        {{ item.question }}
      </p>

      <div class="mt-2.5 flex flex-wrap items-center gap-2">
        <button
          v-for="option in item.options"
          :key="option"
          type="button"
          class="rounded-full border px-3 py-1 text-base transition-colors"
          :class="
            answers[item.ask] === option
              ? 'border-outline-gray-5 bg-surface-gray-3 text-ink-gray-9'
              : 'border-outline-gray-2 bg-surface-base text-ink-gray-7 hover:border-outline-gray-3'
          "
          :aria-pressed="answers[item.ask] === option"
          @click="answer(item.ask, option)"
        >
          {{ option }}
        </button>

        <Button
          v-if="answers[item.ask]"
          variant="ghost"
          size="sm"
          :label="__('Clear')"
          @click="answer(item.ask, '')"
        />
      </div>
    </div>
  </Teleport>

  <Teleport v-for="item in whens" :key="item.id" :to="item.host">
    <div
      v-if="!verdict(item).ok || verdict(item).unknown"
      class="my-2 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-2 border px-3 py-1.5 text-sm"
      :class="
        verdict(item).unknown
          ? 'border-outline-amber-2 bg-surface-amber-1 text-ink-amber-6'
          : 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-6'
      "
      role="status"
    >
      <span
        :class="
          verdict(item).loading
            ? 'lucide-loader-circle animate-spin'
            : verdict(item).unknown
              ? 'lucide-triangle-alert'
              : 'lucide-git-branch'
        "
        class="size-3.5 shrink-0"
        aria-hidden="true"
      />

      <span class="min-w-0">{{ verdict(item).message }}</span>

      <button
        v-if="!verdict(item).unknown"
        type="button"
        class="ml-auto shrink-0 underline underline-offset-2 hover:text-ink-gray-8"
        @click="toggle(item)"
      >
        {{ shown.includes(item.id) ? __('Hide it') : __('Show it anyway') }}
      </button>
    </div>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { Button, Tooltip, call } from 'frappe-ui'
import { answerPasses, answersOf, parseCondition } from '@/data/flow'
import { translate as __ } from '@/translation'

const REFRESH = 120000

const props = defineProps({
  root: { type: [Object, null], default: null },
  sop: { type: String, default: '' },
  revision: { type: [String, Number, null], default: null },
  content: { type: String, default: '' },
})

const items = shallowRef([])
const asks = shallowRef([])
const whens = shallowRef([])
const results = ref({})
const answers = ref({})
const shown = ref([])
const loading = ref(false)
let timer = null

function storageKey() {
  return `sop-flow:${props.sop}:${props.revision ?? 'current'}`
}

function remember() {
  try {
    sessionStorage.setItem(storageKey(), JSON.stringify(answers.value))
  } catch {
    return
  }
}

function recall() {
  try {
    answers.value = JSON.parse(sessionStorage.getItem(storageKey()) || '{}')
  } catch {
    answers.value = {}
  }
}

function host(tag) {
  const element = document.createElement(tag)
  element.className = 'sop-flow-host'

  return element
}

function scan() {
  const root = props.root
  if (!root) return

  const found = []
  for (const anchor of root.querySelectorAll('a[href^="#live:"], a[href^="#check:"]')) {
    const href = anchor.getAttribute('href')
    const spot = host('span')

    found.push({
      id: `${found.length}:${href}`,
      href,
      host: spot,
      kind: href.startsWith('#check:') ? 'check' : 'live',
      fallback: anchor.textContent.trim(),
    })

    anchor.replaceWith(spot)
  }

  const questions = []
  for (const element of root.querySelectorAll('[data-sop-ask]')) {
    const spot = host('div')

    questions.push({
      id: `ask:${questions.length}`,
      ask: element.getAttribute('data-sop-ask'),
      question: element.textContent.trim(),
      options: answersOf(element.getAttribute('data-sop-options')),
      host: spot,
    })

    element.replaceWith(spot)
  }

  const branches = []
  for (const element of root.querySelectorAll('[data-sop-when]')) {
    const raw = element.getAttribute('data-sop-when')
    const spot = host('div')

    branches.push({
      id: `when:${branches.length}`,
      raw,
      spec: parseCondition(raw),
      label: element.getAttribute('data-sop-label') || '',
      element,
      host: spot,
    })

    element.insertBefore(spot, element.firstChild)
  }

  items.value = found
  asks.value = questions
  whens.value = branches
  shown.value = []

  if (found.length || branches.length) load()
  paint()
}

let latest = 0

async function load() {
  if (!props.sop) return

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

function questionOf(id) {
  return asks.value.find((row) => row.ask === id)?.question || __('the question above')
}

function verdict(item) {
  if (!item.spec) {
    return { unknown: true, ok: true, message: __('This condition could not be read, so it is shown.') }
  }

  if (item.spec.kind === 'ask') {
    const passed = answerPasses(item.spec, answers.value)

    if (passed === null) {
      return { message: __('Answer “{0}” to see this.').format(questionOf(item.spec.ask)) }
    }

    return {
      ok: passed,
      message: __('Not applicable — {0}.').format(item.label || questionOf(item.spec.ask)),
    }
  }

  const found = results.value[item.raw]

  if (!found) {
    if (loading.value) return { loading: true, message: __('Checking…') }
    return { unknown: true, ok: true, message: __('This condition could not be read, so it is shown.') }
  }

  if (found.missing) return { unknown: true, ok: true, message: found.message }

  return {
    ok: !!found.ok,
    message: __('Not applicable — {0} is {1}.').format(found.label, found.value),
  }
}

function paint() {
  for (const item of whens.value) {
    const hide = !verdict(item).ok && !shown.value.includes(item.id)
    item.element.classList.toggle('sop-when-off', hide)
  }
}

function toggle(item) {
  shown.value = shown.value.includes(item.id)
    ? shown.value.filter((id) => id !== item.id)
    : [...shown.value, item.id]
}

function answer(ask, option) {
  answers.value = { ...answers.value, [ask]: option }
  remember()
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
  () => {
    recall()
    scan()
  },
  { immediate: true, flush: 'post' },
)

watch([results, answers, shown, loading], paint, { flush: 'post' })

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
