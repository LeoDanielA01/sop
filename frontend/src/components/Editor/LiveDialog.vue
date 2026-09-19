<template>
  <Dialog v-model:open="open" :title="mode === 'check' ? __('Add a check') : __('Show a live value')" size="lg">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-sm text-ink-gray-6">
          {{
            mode === 'check'
              ? __('Readers see a green tick or a red cross, worked out fresh every time they open the procedure.')
              : __('Readers always see the current value, taken fresh every time they open the procedure.')
          }}
        </p>

        <section>
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

        <section v-if="record">
          <p class="mb-1.5 flex items-center gap-2 text-sm font-medium text-ink-gray-8">
            <span class="grid size-5 place-content-center rounded-full bg-surface-gray-2 text-xs">2</span>
            {{ mode === 'check' ? __('What should be checked?') : __('What should readers see?') }}
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

        <section v-if="mode === 'check' && picked">
          <p class="mb-1.5 flex items-center gap-2 text-sm font-medium text-ink-gray-8">
            <span class="grid size-5 place-content-center rounded-full bg-surface-gray-2 text-xs">3</span>
            {{ __('When is it OK?') }}
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
          v-if="picked"
          class="rounded-2 border border-dashed border-outline-gray-3 bg-surface-gray-1 px-3 py-2.5"
        >
          <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-ink-gray-5">{{ __('Readers will see') }}</p>

          <p v-if="mode === 'live'" class="text-base text-ink-gray-8">
            <span
              class="inline-flex items-center gap-1 rounded-2 border px-1.5 py-px align-baseline"
              :class="pillTone(picked.tone)"
            >
              <span class="lucide-activity size-3" aria-hidden="true" />
              {{ picked.value }}
            </span>
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

          <p v-if="mode === 'check' && result && !checking" class="mt-1 text-xs text-ink-gray-5">
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
          :icon-left="mode === 'check' ? 'lucide-circle-check' : 'lucide-activity'"
          :label="mode === 'check' ? __('Add check') : __('Add live value')"
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
import { CHECK_WORDS, checkHref, checkPhrase, liveHref } from '@/data/live'
import { translate as __ } from '@/translation'

const props = defineProps({
  editor: { type: Object, default: null },
  mode: { type: String, default: 'live' },
})

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

const needsTarget = computed(() => !!CHECK_WORDS[check.value]?.target)

const sentence = computed(() => {
  if (!picked.value || !record.value) return ''
  return `${record.value.label}: ${picked.value.label} ${checkPhrase(check.value, target.value)}`
})

const ready = computed(() => {
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
  search()
  nextTick(() => searchBox.value?.focus())
})

watch(query, search)

const runPreview = debounce(async () => {
  if (props.mode !== 'check' || !ready.value) {
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
</script>
