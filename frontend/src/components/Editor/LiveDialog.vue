<template>
  <Dialog v-model:open="open" :title="__(condition ? 'Change the condition' : TITLES[mode])" size="lg">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-sm text-ink-gray-6">{{ __(BLURBS[mode]) }}</p>

        <div v-if="mode === 'when' && asks.length" class="flex gap-2">
          <button
            v-for="option in SOURCES"
            :key="option.value"
            type="button"
            class="flex flex-1 items-center gap-2.5 rounded-2 border px-3 py-2 text-left transition-colors"
            :class="
              source === option.value
                ? 'border-outline-gray-4 bg-surface-gray-2'
                : 'border-outline-gray-2 hover:bg-surface-gray-1'
            "
            @click="pickSource(option.value)"
          >
            <span :class="option.icon" class="size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
            <span class="min-w-0">
              <span class="block truncate text-base text-ink-gray-8">{{ __(option.label) }}</span>
              <span class="block truncate text-xs text-ink-gray-5">{{ __(option.hint) }}</span>
            </span>
          </button>
        </div>

        <section v-if="source === 'ask'">
          <p class="mb-1.5 flex items-center gap-2 text-sm font-medium text-ink-gray-8">
            <span class="grid size-5 place-content-center rounded-full bg-surface-gray-2 text-xs">1</span>
            {{ __('Which question?') }}
          </p>

          <div class="flex flex-col gap-1.5">
            <button
              v-for="row in asks"
              :key="row.id"
              type="button"
              class="flex items-center gap-3 rounded-2 border px-3 py-2 text-left transition-colors"
              :class="
                row.id === ask?.id
                  ? 'border-outline-gray-4 bg-surface-gray-2'
                  : 'border-outline-gray-2 hover:bg-surface-gray-1'
              "
              @click="pickAsk(row)"
            >
              <span
                :class="row.id === ask?.id ? 'lucide-circle-dot text-ink-gray-9' : 'lucide-circle text-ink-gray-4'"
                class="size-4 shrink-0"
                aria-hidden="true"
              />
              <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
                {{ row.question || __('Untitled question') }}
              </span>
              <span class="shrink-0 text-sm text-ink-gray-5">
                {{ __('{0} answers').format(row.options.length) }}
              </span>
            </button>
          </div>
        </section>

        <section v-if="source === 'ask' && ask">
          <p class="mb-1.5 flex items-center gap-2 text-sm font-medium text-ink-gray-8">
            <span class="grid size-5 place-content-center rounded-full bg-surface-gray-2 text-xs">2</span>
            {{ __('Which answer opens this branch?') }}
          </p>

          <p v-if="!ask.options.length" class="rounded-2 bg-surface-gray-1 px-3 py-3 text-sm text-ink-gray-6">
            {{ __('That question has no answers yet. Add them on the question first.') }}
          </p>

          <div v-else class="flex flex-wrap items-center gap-2">
            <FormControl v-model="askCheck" type="select" :options="askChecks" class="min-w-32" />
            <button
              v-for="option in ask.options"
              :key="option"
              type="button"
              class="rounded-full border px-3 py-1 text-base transition-colors"
              :class="
                option === answer
                  ? 'border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
                  : 'border-outline-gray-2 text-ink-gray-7 hover:bg-surface-gray-1'
              "
              @click="answer = option"
            >
              {{ option }}
            </button>
          </div>
        </section>

        <section v-if="source === 'record'">
          <p class="mb-1.5 flex items-center gap-2 text-sm font-medium text-ink-gray-8">
            <span class="grid size-5 place-content-center rounded-full bg-surface-gray-2 text-xs">1</span>
            {{ __('Which record?') }}
          </p>

          <div
            v-if="record"
            class="flex items-center gap-2.5 rounded-2 border border-outline-gray-2 bg-surface-gray-1 px-3 py-2"
          >
            <span class="lucide-file-text size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
            <span class="min-w-0 flex-1">
              <span class="block truncate text-base text-ink-gray-9">{{ record.label }}</span>
              <span class="block truncate text-xs text-ink-gray-5">{{ type }} · {{ record.name }}</span>
            </span>
            <Button variant="ghost" size="sm" :label="__('Change')" @click="clearRecord" />
          </div>

          <div v-else class="overflow-hidden rounded-2 border border-outline-gray-2">
            <div class="flex items-center gap-2 border-b border-outline-gray-1 px-2.5">
              <button
                v-if="type"
                type="button"
                class="inline-flex shrink-0 items-center gap-1 rounded-1 bg-surface-gray-2 px-1.5 py-0.5 text-sm text-ink-gray-8 hover:bg-surface-gray-3"
                @click="clearType"
              >
                {{ type }}
                <span class="lucide-x size-3" aria-hidden="true" />
              </button>
              <input
                ref="searchBox"
                v-model="query"
                type="text"
                :placeholder="type ? __('Search {0}').format(type) : __('What kind of thing? e.g. Item, Asset, Warehouse')"
                class="min-w-0 flex-1 border-0 bg-transparent px-0 py-2 text-base text-ink-gray-9 placeholder:text-ink-gray-4 focus:ring-0"
              />
            </div>

            <div class="max-h-52 overflow-y-auto p-1">
              <button
                v-for="row in rows"
                :key="row.value"
                type="button"
                class="flex w-full items-center gap-2.5 rounded-2 px-2 py-1.5 text-left hover:bg-surface-gray-2"
                @click="row.isType ? pickType(row.value) : pickRecord(row)"
              >
                <span
                  :class="row.isType ? 'lucide-shapes' : 'lucide-file-text'"
                  class="size-4 shrink-0 text-ink-gray-5"
                  aria-hidden="true"
                />
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-base text-ink-gray-8">{{ row.label }}</span>
                  <span v-if="row.hint" class="block truncate text-xs text-ink-gray-5">{{ row.hint }}</span>
                </span>
              </button>

              <p v-if="!rows.length" class="px-2 py-4 text-center text-sm text-ink-gray-5">
                {{ searching ? __('Looking…') : __('Nothing matches') }}
              </p>
            </div>
          </div>
        </section>

        <section v-if="source === 'record' && record">
          <p class="mb-1.5 flex items-center gap-2 text-sm font-medium text-ink-gray-8">
            <span class="grid size-5 place-content-center rounded-full bg-surface-gray-2 text-xs">2</span>
            {{ mode === 'live' ? __('What should readers see?') : __('What should be checked?') }}
          </p>

          <div v-if="details.loading" class="flex flex-col gap-2">
            <Skeleton class="h-10 w-full rounded-2" />
            <Skeleton class="h-10 w-full rounded-2" />
          </div>

          <ErrorMessage v-else-if="details.error" :message="details.error.messages?.[0] || details.error.message" />

          <p v-else-if="!choices.length" class="rounded-2 bg-surface-gray-1 px-3 py-3 text-sm text-ink-gray-6">
            {{ __('There is nothing live to show for this record yet.') }}
          </p>

          <div v-else class="flex flex-col gap-1.5">
            <button
              v-for="option in choices"
              :key="option.key"
              type="button"
              class="flex items-center gap-3 rounded-2 border px-3 py-2 text-left transition-colors"
              :class="
                option.key === picked?.key
                  ? 'border-outline-gray-4 bg-surface-gray-2'
                  : 'border-outline-gray-2 hover:bg-surface-gray-1'
              "
              @click="pickOption(option)"
            >
              <span
                :class="option.key === picked?.key ? 'lucide-circle-dot text-ink-gray-9' : 'lucide-circle text-ink-gray-4'"
                class="size-4 shrink-0"
                aria-hidden="true"
              />
              <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">{{ option.label }}</span>
              <span class="max-w-[50%] truncate text-sm" :class="toneText(option.tone)">{{ option.value }}</span>
            </button>
          </div>
        </section>

        <section v-if="mode !== 'live' && source === 'record' && picked">
          <p class="mb-1.5 flex items-center gap-2 text-sm font-medium text-ink-gray-8">
            <span class="grid size-5 place-content-center rounded-full bg-surface-gray-2 text-xs">3</span>
            {{ mode === 'when' ? __('When does it apply?') : __('When is it OK?') }}
          </p>

          <div class="flex flex-wrap items-center gap-2 rounded-2 border border-outline-gray-2 px-3 py-2.5">
            <span class="text-base text-ink-gray-8">{{ picked.label }}</span>
            <FormControl v-model="check" type="select" :options="checkOptions" class="min-w-44" />
            <FormControl
              v-if="needsTarget"
              v-model="target"
              :type="CHECK_WORDS[check].target === 'text' ? 'text' : 'number'"
              :placeholder="CHECK_WORDS[check].target === 'days' ? __('days') : __('value')"
              class="w-28"
            />
          </div>
        </section>

        <section
          v-if="ready"
          class="rounded-2 border border-dashed border-outline-gray-3 bg-surface-gray-1 px-3 py-2.5"
        >
          <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">
            {{ mode === 'when' ? __('This section shows when') : __('Readers will see') }}
          </p>

          <p v-if="mode === 'live'" class="text-base text-ink-gray-8">
            <span
              class="inline-flex items-center gap-1 rounded-2 border px-1.5 py-px align-baseline"
              :class="pillTone(picked.tone)"
            >
              <span class="lucide-activity size-3" aria-hidden="true" />
              {{ picked.value }}
            </span>
          </p>

          <p v-else-if="source === 'ask'" class="flex items-center gap-2 text-base text-ink-gray-8">
            <span class="lucide-message-circle-question size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
            {{ sentence }}
          </p>

          <p v-else class="flex items-center gap-2 text-base">
            <span v-if="checking" class="lucide-loader-circle size-4 animate-spin text-ink-gray-5" aria-hidden="true" />
            <span
              v-else
              :class="result?.ok ? 'lucide-circle-check text-ink-green-3' : 'lucide-circle-x text-ink-red-3'"
              class="size-4 shrink-0"
              aria-hidden="true"
            />
            <span class="text-ink-gray-8">{{ sentence }}</span>
          </p>

          <p v-if="mode !== 'live' && source === 'record' && result && !checking" class="mt-1 text-xs text-ink-gray-5">
            {{ result.ok ? __('Right now this passes.') : __('Right now this fails.') }}
            {{ __('Current value: {0}').format(result.value) }}
          </p>
        </section>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="open = false" />
        <Button
          variant="solid"
          :icon-left="ACTIONS[mode].icon"
          :label="__(condition ? 'Save condition' : ACTIONS[mode].label)"
          :disabled="!ready"
          @click="insert"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl, Skeleton, call, createResource, debounce, toast } from 'frappe-ui'
import { CHECK_WORDS, checkHref, liveHref } from '@/data/live'
import {
  askCondition,
  askLabel,
  checkCondition,
  checkLabel,
  parseCondition,
} from '@/data/flow'
import { translate as __ } from '@/translation'

const props = defineProps({
  editor: { type: Object, default: null },
  mode: { type: String, default: 'live' },
  asks: { type: Array, default: () => [] },
  condition: { type: String, default: '' },
  apply: { type: Function, default: null },
})

const TITLES = {
  live: 'Show a live value',
  check: 'Add a check',
  when: 'Show this only when\u2026',
}

const BLURBS = {
  live: 'Readers always see the current value, taken fresh every time they open the procedure.',
  check: 'Readers see a green tick or a red cross, worked out fresh every time they open the procedure.',
  when: 'Readers who do not meet the condition see a single line saying why, instead of this section.',
}

const ACTIONS = {
  live: { icon: 'lucide-activity', label: 'Add live value' },
  check: { icon: 'lucide-circle-check', label: 'Add check' },
  when: { icon: 'lucide-git-branch', label: 'Add branch' },
}

const SOURCES = [
  {
    value: 'record',
    icon: 'lucide-database',
    label: 'On record data',
    hint: 'A value in the system decides',
  },
  {
    value: 'ask',
    icon: 'lucide-message-circle-question',
    label: 'On an answer',
    hint: 'The reader decides',
  },
]

const open = defineModel('open', { type: Boolean, default: false })

const query = ref('')
const type = ref('')
const record = ref(null)
const picked = ref(null)
const check = ref('')
const target = ref('')
const result = ref(null)
const checking = ref(false)
const searchBox = ref(null)
const source = ref('record')
const ask = ref(null)
const answer = ref('')
const askCheck = ref('is')

const types = createResource({ url: 'sop.api.mentions.doctypes' })
const records = createResource({ url: 'sop.api.mentions.find' })
const details = createResource({ url: 'sop.api.live.options' })

const search = debounce(() => {
  if (type.value) records.submit({ doctype: type.value, text: query.value })
  else types.submit({ search: query.value })
}, 180)

const searching = computed(() => types.loading || records.loading)

const rows = computed(() => {
  if (!type.value) return (types.data || []).map((name) => ({ value: name, label: name, isType: true }))

  return (records.data || []).map((row) => ({
    value: row.name,
    name: row.name,
    label: row.label,
    hint: row.hint || (row.name === row.label ? null : row.name),
  }))
})

const choices = computed(() => details.data?.options || [])

const checkOptions = computed(() =>
  (picked.value?.checks || []).map((value) => ({ value, label: __(CHECK_WORDS[value].label) })),
)

const askChecks = computed(() => [
  { value: 'is', label: __('is') },
  { value: 'is_not', label: __('is not') },
])

const needsTarget = computed(() => !!CHECK_WORDS[check.value]?.target)

const sentence = computed(() => {
  if (source.value === 'ask') {
    if (!ask.value || !answer.value) return ''
    return askLabel(ask.value.question, askCheck.value, answer.value)
  }

  if (!picked.value || !record.value) return ''
  return checkLabel(record.value.label, picked.value.label, check.value, target.value)
})

const ready = computed(() => {
  if (source.value === 'ask') return !!ask.value && !!answer.value

  if (!record.value || !picked.value) return false
  if (props.mode === 'live') return true
  return !!check.value && (!needsTarget.value || String(target.value).trim() !== '')
})

watch(open, (value) => {
  if (!value) return
  query.value = ''
  type.value = ''
  record.value = null
  picked.value = null
  result.value = null
  source.value = 'record'
  ask.value = null
  answer.value = ''
  askCheck.value = 'is'
  search()
  prefill()
  nextTick(() => searchBox.value?.focus())
})

function prefill() {
  const spec = parseCondition(props.condition)
  if (!spec) return

  if (spec.kind === 'ask') {
    source.value = 'ask'
    ask.value = props.asks.find((row) => row.id === spec.ask) || null
    askCheck.value = spec.check
    answer.value = spec.target
    return
  }

  type.value = spec.doctype
  record.value = { name: spec.name, label: spec.name }

  details.submit({ doctype: spec.doctype, name: spec.name }).then(() => {
    record.value = { name: spec.name, label: details.data?.title || spec.name }

    const option = choices.value.find((row) => row.key === spec.key)
    if (!option) return

    picked.value = option
    check.value = spec.check
    target.value = spec.target
  })
}

watch(query, search)

const runPreview = debounce(async () => {
  if (props.mode === 'live' || source.value !== 'record' || !ready.value) {
    result.value = null
    return
  }

  checking.value = true
  try {
    result.value = await call('sop.api.live.preview', {
      doctype: type.value,
      name: record.value.name,
      key: picked.value.key,
      check: check.value,
      target: target.value,
    })
  } catch {
    result.value = null
  } finally {
    checking.value = false
  }
}, 300)

watch([check, target, picked], runPreview)

function pickSource(value) {
  source.value = value
}

function pickAsk(row) {
  ask.value = row
  answer.value = row.options.includes(answer.value) ? answer.value : ''
}

function pickType(value) {
  type.value = value
  query.value = ''
  search()
  nextTick(() => searchBox.value?.focus())
}

function clearType() {
  type.value = ''
  query.value = ''
  search()
}

function pickRecord(row) {
  record.value = row
  picked.value = null
  details.submit({ doctype: type.value, name: row.name })
}

function clearRecord() {
  record.value = null
  picked.value = null
  result.value = null
  search()
}

function pickOption(option) {
  picked.value = option
  check.value = option.checks?.[0] || ''
  target.value = ''
}

function toneText(tone) {
  if (tone === 'red') return 'text-ink-red-3'
  if (tone === 'amber') return 'text-ink-amber-6'
  if (tone === 'green') return 'text-ink-green-3'
  return 'text-ink-gray-6'
}

function pillTone(tone) {
  if (tone === 'red') return 'border-outline-red-2 bg-surface-red-1 text-ink-red-6'
  if (tone === 'amber') return 'border-outline-amber-2 bg-surface-amber-1 text-ink-amber-6'
  return 'border-outline-gray-2 bg-surface-gray-1 text-ink-gray-8'
}

function insert() {
  if (!ready.value || !props.editor) return

  if (props.mode === 'when') return branch()

  const doctype = type.value
  const name = record.value.name
  const key = picked.value.key

  const href =
    props.mode === 'check'
      ? checkHref(doctype, name, key, check.value, needsTarget.value ? target.value : '')
      : liveHref(doctype, name, key)

  const text = props.mode === 'check' ? sentence.value : `${record.value.label} · ${picked.value.label}`

  props.editor
    .chain()
    .focus()
    .insertContent([
      { type: 'text', text, marks: [{ type: 'link', attrs: { href } }] },
      { type: 'text', text: ' ' },
    ])
    .run()

  open.value = false
  toast.success(props.mode === 'check' ? __('Check added') : __('Live value added'))
}

function branch() {
  const attrs =
    source.value === 'ask'
      ? { when: askCondition(ask.value.id, askCheck.value, answer.value), label: sentence.value }
      : {
          when: checkCondition(
            type.value,
            record.value.name,
            picked.value.key,
            check.value,
            needsTarget.value ? target.value : '',
          ),
          label: sentence.value,
        }

  if (props.apply) props.apply(attrs)
  else if (props.editor.state.selection.empty) props.editor.chain().focus().insertWhen(attrs).run()
  else props.editor.chain().focus().wrapInWhen(attrs).run()

  open.value = false
  toast.success(props.condition ? __('Condition saved') : __('Branch added'))
}
</script>
