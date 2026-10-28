<template>
  <Dialog v-model:open="open" :title="__('Find and replace')" size="4xl">
    <template #default>
      <div class="flex flex-col gap-4">
        <TabButtons
          v-model="mode"
          :options="[
            { label: __('Text'), value: 'text' },
            { label: __('Linked record'), value: 'record' },
            { label: __('History'), value: 'history' },
          ]"
        />

        <ErrorMessage
          :message="
            claim.error?.messages?.[0] ||
            apply.error?.messages?.[0] ||
            preview.error?.messages?.[0] ||
            undoing.error?.messages?.[0]
          "
        />

        <p
          v-if="someoneElse"
          class="flex items-start gap-2 rounded-4 border border-outline-amber-1 bg-surface-amber-1 px-3 py-2.5 text-sm text-ink-amber-6"
        >
          <span class="lucide-lock mt-0.5 size-4 shrink-0" aria-hidden="true" />
          {{ __('{0} is running a replace right now. Wait until it finishes.').format(busy.data.holder) }}
        </p>

        <template v-if="mode === 'text'">
          <div class="flex flex-col gap-2">
            <div v-for="(rule, index) in rules" :key="rule.key" class="flex items-end gap-2">
              <FormControl
                class="flex-1"
                type="text"
                :label="index ? '' : __('Find')"
                :placeholder="regex ? 'Mixer ([A-Z])' : __('Mixer A')"
                v-model="rule.find"
                @keyup.enter="look"
              />
              <span class="lucide-arrow-right mb-2 size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
              <FormControl
                class="flex-1"
                type="text"
                :label="index ? '' : __('Replace with')"
                :placeholder="regex ? __('Planetary mixer $1') : __('Mixer B')"
                v-model="rule.replace"
              />
              <Button
                v-if="rules.length > 1"
                variant="ghost"
                icon="lucide-x"
                :label="__('Remove rule')"
                @click="rules.splice(index, 1)"
              />
            </div>
            <div>
              <Button size="sm" variant="ghost" icon-left="lucide-plus" :label="__('Add another rule')" @click="addRule" />
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
            <FormControl type="checkbox" :label="__('Match case')" v-model="matchCase" />
            <FormControl type="checkbox" :label="__('Whole word only')" v-model="wholeWord" />
            <FormControl type="checkbox" :label="__('Keep capitals')" v-model="keepCase" />
            <FormControl type="checkbox" :label="__('Pattern (regex)')" v-model="regex" />
          </div>
          <p v-if="regex" class="-mt-2 text-sm text-ink-gray-5">
            {{ __('Use ( ) to capture part of a match and $1, $2 to put it back. Example: Mixer ([A-Z]) → Planetary mixer $1.') }}
          </p>

          <div class="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
            <span class="text-ink-gray-5">{{ __('Look in') }}</span>
            <FormControl type="checkbox" :label="__('Title')" v-model="lookIn.title" />
            <FormControl type="checkbox" :label="__('Summary')" v-model="lookIn.summary" />
            <FormControl type="checkbox" :label="__('Body')" v-model="lookIn.content" />
            <span class="h-4 w-px bg-outline-gray-2" />
            <FormControl type="checkbox" :label="__('This space only')" v-model="thisSpace" />
            <span v-if="preview.loading" class="ml-auto text-ink-gray-5">{{ __('Searching…') }}</span>
          </div>
        </template>

        <template v-else-if="mode === 'record'">
          <div class="grid gap-3 sm:grid-cols-2">
            <div class="flex flex-col gap-1.5">
              <span class="text-xs text-ink-gray-5">{{ __('Record type') }}</span>
              <Select v-model="record.doctype" :options="typeOptions" :placeholder="__('Pick a record type')" />
            </div>
            <div class="flex flex-col gap-1.5">
              <span class="text-xs text-ink-gray-5">{{ __('Which records') }}</span>
              <TabButtons
                v-model="record.find"
                :options="[
                  { label: __('Pick them'), value: 'pick' },
                  { label: __('By filter'), value: 'filter' },
                ]"
              />
            </div>
          </div>

          <div v-if="record.doctype && record.find === 'pick'" class="flex flex-col gap-2">
            <div class="flex flex-wrap items-center gap-1.5">
              <button
                v-for="name in record.names"
                :key="name"
                type="button"
                class="inline-flex items-center gap-1 rounded-3 border border-outline-gray-2 bg-surface-gray-1 px-2 py-0.5 text-sm text-ink-gray-8 hover:bg-surface-gray-2"
                @click="record.names = record.names.filter((row) => row !== name)"
              >
                {{ linkedLabel(name) }}
                <span class="lucide-x size-3 text-ink-gray-5" aria-hidden="true" />
              </button>
              <Combobox
                class="w-72"
                :options="linkedOptions"
                :modelValue="null"
                :loading="linked.loading"
                :placeholder="__('Add a linked {0}').format(record.doctype)"
                @update:modelValue="(value) => value && !record.names.includes(value) && record.names.push(value)"
              />
            </div>
            <p class="text-sm text-ink-gray-5">
              <template v-if="record.replaceBy === 'map'">
                {{ __('Leave empty to list every linked {0} below and map the ones you want.').format(record.doctype) }}
              </template>
              <template v-else>{{ __('Only records that procedures link to are listed.') }}</template>
            </p>
          </div>

          <div v-if="record.doctype && record.find === 'filter'" class="flex flex-col gap-2">
            <div v-for="(row, index) in record.filters" :key="index" class="flex items-center gap-2">
              <Select v-model="row.field" :options="fieldOptions" class="w-56" :placeholder="__('Field')" />
              <Select v-model="row.operator" :options="OPERATORS" class="w-36" />
              <TextInput v-model="row.value" class="flex-1" :placeholder="__('Value, e.g. Raw Material')" />
              <Button variant="ghost" icon="lucide-x" :label="__('Remove filter')" @click="record.filters.splice(index, 1)" />
            </div>
            <div>
              <Button size="sm" variant="ghost" icon-left="lucide-plus" :label="__('Add filter')" @click="addFilter" />
            </div>
          </div>

          <div v-if="record.doctype" class="grid gap-3 sm:grid-cols-2">
            <div class="flex flex-col gap-1.5">
              <span class="text-xs text-ink-gray-5">{{ __('Replace with') }}</span>
              <TabButtons
                v-model="record.replaceBy"
                :options="[
                  { label: __('One record for all'), value: 'one' },
                  { label: __('Record by record'), value: 'map' },
                ]"
              />
            </div>
            <div v-if="record.replaceBy === 'one'" class="flex flex-col gap-1.5">
              <span class="text-xs text-ink-gray-5">{{ __('New {0}').format(record.doctype) }}</span>
              <RecordPicker v-model="record.to" :doctype="record.doctype" />
            </div>
          </div>

          <div v-if="record.replaceBy === 'map' && foundRecords.length" class="flex flex-col gap-1.5">
            <span class="text-xs text-ink-gray-5">{{ __('Found in procedures → replace with') }}</span>
            <div
              v-for="old in foundRecords"
              :key="old.value"
              class="flex items-center gap-2 rounded-4 border border-outline-gray-2 px-3 py-1.5"
            >
              <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-8">{{ old.label }}</span>
              <span class="lucide-arrow-right size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
              <RecordPicker v-model="record.map[old.value]" class="w-72" :doctype="record.doctype" :placeholder="__('Keep as is')" />
            </div>
          </div>

          <div class="flex items-center gap-4 text-sm">
            <FormControl type="checkbox" :label="__('This space only')" v-model="thisSpace" />
            <span v-if="preview.loading" class="ml-auto text-ink-gray-5">{{ __('Searching…') }}</span>
          </div>
        </template>

        <template v-else>
          <div v-if="past.data?.length" class="flex flex-col divide-y divide-outline-gray-1 rounded-4 border border-outline-gray-2">
            <div v-for="row in past.data" :key="row.name" class="flex items-center gap-3 px-3 py-2.5">
              <span
                :class="row.kind === 'Record' ? 'lucide-link-2' : 'lucide-replace'"
                class="size-4 shrink-0 text-ink-gray-5"
                aria-hidden="true"
              />
              <div class="min-w-0 flex-1">
                <p class="truncate text-base text-ink-gray-8">{{ row.description }}</p>
                <p class="text-sm text-ink-gray-5">
                  {{ row.owner_name }} · {{ when(row.creation) }} ·
                  {{ __('{0} changes in {1} procedures').format(row.hits, row.procedures) }}
                  <template v-if="row.undone_on"> · {{ __('undone {0}').format(when(row.undone_on)) }}</template>
                </p>
              </div>
              <Badge :theme="row.status === 'Undone' ? 'gray' : 'green'" variant="subtle" size="sm">
                {{ __(row.status) }}
              </Badge>
              <Button
                v-if="row.can_undo"
                size="sm"
                :variant="confirming === row.name ? 'solid' : 'subtle'"
                :theme="confirming === row.name ? 'red' : 'gray'"
                :label="confirming === row.name ? __('Confirm undo') : __('Undo')"
                :loading="undoing.loading && confirming === row.name"
                @click="undo(row)"
              />
            </div>
          </div>
          <p v-else class="rounded-4 border border-dashed border-outline-gray-2 px-3 py-6 text-center text-sm text-ink-gray-5">
            {{ __('No replacements yet. Each one you run is listed here and can be undone.') }}
          </p>
        </template>

        <div
          v-if="mode !== 'history' && run.total"
          class="flex flex-col gap-2 rounded-4 border border-outline-gray-2 bg-surface-gray-1 px-3 py-3"
        >
          <div class="flex items-center justify-between text-sm">
            <span class="text-ink-gray-7">
              <template v-if="run.busy">{{ __('Replacing {0} of {1}').format(run.done + 1, run.total) }}</template>
              <template v-else>{{ __('Finished {0} procedures').format(run.total) }}</template>
            </span>
            <span class="font-mono text-ink-gray-5">{{ run.current }}</span>
          </div>

          <Progress :value="Math.round((run.done * 100) / run.total)" size="sm" />

          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
            <span v-if="run.changed" class="text-ink-green-3">{{ __('{0} updated').format(run.changed) }}</span>
            <span v-if="run.failed" class="text-ink-red-3">{{ __('{0} failed').format(run.failed) }}</span>
            <Button
              v-if="!run.busy && run.batch && run.changed"
              class="ml-auto"
              size="sm"
              icon-left="lucide-undo-2"
              :label="__('Undo this change')"
              @click="undoLast"
            />
          </div>

          <ul v-if="run.left.length" class="mt-1 flex flex-col gap-0.5 text-sm text-ink-gray-6">
            <li v-for="row in run.left" :key="row.name">
              <span class="font-mono text-ink-gray-5">{{ row.sop_no }}</span> — {{ __('left alone: {0}').format(row.reason) }}
            </li>
          </ul>
        </div>

        <div v-if="mode !== 'history' && rows.length && !run.busy" class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label class="flex cursor-pointer items-center gap-2 text-sm text-ink-gray-6">
              <FormControl type="checkbox" :modelValue="allPicked" @update:modelValue="toggleAll" />
              {{ __('Select all') }}
            </label>
            <span class="text-sm text-ink-gray-5">
              {{ __('{0} matches in {1} procedures').format(hits, rows.length) }}
            </span>
          </div>

          <ScrollArea viewport-class="max-h-80 p-0.5">
            <div class="flex flex-col gap-1.5">
              <div
                v-for="row in rows"
                :key="row.name"
                class="rounded-4 border"
                :class="picked.includes(row.name) ? 'border-outline-gray-3 bg-surface-gray-2' : 'border-outline-gray-2 bg-surface-gray-1'"
              >
                <div class="flex items-start gap-3 px-3 py-2.5">
                  <FormControl
                    type="checkbox"
                    class="mt-0.5"
                    :modelValue="picked.includes(row.name)"
                    @update:modelValue="() => toggle(row.name)"
                  />
                  <div class="min-w-0 flex-1 cursor-pointer" @click="expand(row.name)">
                    <div class="flex min-w-0 items-center gap-2">
                      <span class="shrink-0 font-mono text-sm text-ink-gray-5">{{ row.sop_no }}</span>
                      <span class="truncate text-base text-ink-gray-8">{{ row.title }}</span>
                      <Badge :theme="STATUS_THEME[row.status]" variant="subtle" size="sm">{{ row.status }}</Badge>
                    </div>
                    <p class="mt-0.5 text-sm text-ink-gray-5">
                      {{ __('{0} of {1} will change').format(chosenIn(row), row.hits) }}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    :icon="opened === row.name ? 'lucide-chevron-up' : 'lucide-chevron-down'"
                    :label="opened === row.name ? __('Hide matches') : __('Show matches')"
                    @click="expand(row.name)"
                  />
                  <Badge variant="subtle" size="sm">{{ row.hits }}</Badge>
                </div>

                <div v-if="opened === row.name" class="divide-y divide-outline-gray-1 border-t border-outline-gray-1">
                  <label v-for="match in row.matches" :key="match.index" class="flex cursor-pointer items-start gap-3 px-3 py-2">
                    <FormControl
                      type="checkbox"
                      class="mt-0.5"
                      :modelValue="isChosen(row, match.index)"
                      @update:modelValue="() => flipMatch(row, match.index)"
                    />
                    <span class="min-w-0 flex-1 text-sm text-ink-gray-6">
                      <Badge v-if="match.kind" variant="subtle" size="sm" class="mr-1">{{ KIND[match.kind] }}</Badge>
                      <Badge v-else-if="match.field && match.field !== 'content'" variant="subtle" size="sm" class="mr-1">
                        {{ __(match.field === 'title' ? 'Title' : 'Summary') }}
                      </Badge>
                      <span>{{ match.before }}</span>
                      <mark class="rounded-3 bg-surface-amber-2 px-0.5 text-ink-gray-8">{{ match.hit }}</mark>
                      <span>{{ match.after }}</span>
                      <span class="mt-1 block text-ink-gray-5">
                        <span class="lucide-corner-down-right mr-1 inline-block size-3" aria-hidden="true" />
                        <template v-if="resultOf(match)">
                          <span>{{ match.before }}</span>
                          <mark class="rounded-3 bg-surface-green-2 px-0.5 text-ink-gray-8">{{ resultOf(match) }}</mark>
                          <span>{{ match.after }}</span>
                        </template>
                        <template v-else-if="mode === 'record'">{{ __('No replacement picked — stays as it is') }}</template>
                        <template v-else>{{ __('Removed') }}</template>
                      </span>
                    </span>
                  </label>
                  <p v-if="row.hits > row.matches.length" class="px-3 py-2 text-sm text-ink-gray-5">
                    {{ __('{0} more not listed — they change with the rest.').format(row.hits - row.matches.length) }}
                  </p>
                </div>
              </div>
            </div>
          </ScrollArea>

          <div
            v-if="revisable.length"
            class="flex items-start gap-2.5 rounded-4 border border-outline-amber-1 bg-surface-amber-1 px-3 py-2.5 text-sm text-ink-amber-6"
          >
            <span class="lucide-triangle-alert mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <div class="min-w-0">
              <p>
                {{ __('{0} of these are in force. Editing one has to go through a revision and be approved again.').format(revisable.length) }}
              </p>
              <label class="mt-1.5 flex cursor-pointer items-center gap-2">
                <FormControl type="checkbox" v-model="startRevision" />
                {{ __('Start a revision for them') }}
              </label>
            </div>
          </div>

          <div v-if="blocked.length" class="rounded-4 border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5 text-sm text-ink-gray-6">
            <p>{{ __('{0} cannot be changed yet and will be left alone:').format(blocked.length) }}</p>
            <ul class="mt-1 flex flex-col gap-0.5">
              <li v-for="row in blocked" :key="row.name">
                <span class="font-mono text-ink-gray-5">{{ row.sop_no }}</span> {{ row.title }} — {{ row.status }}
              </li>
            </ul>
          </div>
        </div>

        <p
          v-else-if="mode !== 'history' && searched && !preview.loading && !run.busy"
          class="rounded-4 border border-dashed border-outline-gray-2 px-3 py-6 text-center text-sm text-ink-gray-5"
        >
          {{ __('Nothing matches.') }}
        </p>
      </div>
    </template>

    <template v-if="mode !== 'history'" #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          :label="actionLabel"
          :loading="run.busy"
          :disabled="!picked.length || run.busy || !ready"
          @click="start"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import {
  Badge,
  Button,
  Combobox,
  Dialog,
  ErrorMessage,
  FormControl,
  Progress,
  ScrollArea,
  Select,
  TabButtons,
  TextInput,
  createResource,
  debounce,
  toast,
} from 'frappe-ui'
import RecordPicker from '@/components/Search/RecordPicker.vue'
import { activeSpace } from '@/data/navigation'
import { reloadProcedures } from '@/data/procedures'
import { translate as __ } from '@/translation'
import { STATUS_THEME } from '@/utils/format'

const open = defineModel('open', { type: Boolean, default: false })

const OPERATORS = [
  { label: 'is', value: '=' },
  { label: 'is not', value: '!=' },
  { label: 'contains', value: 'like' },
  { label: 'starts with', value: 'starts' },
]
const KIND = { mention: 'Link', live: 'Live value', check: 'Check', when: 'Condition' }

let ruleKey = 0
const mode = ref('text')
const rules = ref([{ key: ruleKey++, find: '', replace: '' }])
const matchCase = ref(false)
const wholeWord = ref(false)
const keepCase = ref(false)
const regex = ref(false)
const lookIn = reactive({ title: true, summary: true, content: true })
const thisSpace = ref(true)
const startRevision = ref(false)
const searched = ref(false)
const picked = ref([])
const opened = ref(null)
const only = reactive({})
const confirming = ref(null)

const record = reactive({
  doctype: '',
  find: 'pick',
  names: [],
  filters: [],
  replaceBy: 'one',
  to: null,
  map: {},
})

const run = reactive({ busy: false, total: 0, done: 0, changed: 0, failed: 0, current: '', batch: null, left: [] })

const preview = createResource({
  url: 'sop.api.bulk.preview',
  onSuccess(data) {
    searched.value = true
    picked.value = data.filter((row) => row.editable).map((row) => row.name)
    for (const key of Object.keys(only)) delete only[key]
  },
})
const apply = createResource({ url: 'sop.api.bulk.apply' })
const claim = createResource({ url: 'sop.api.bulk.claim' })
const release = createResource({ url: 'sop.api.bulk.release' })
const busy = createResource({ url: 'sop.api.bulk.busy' })
const types = createResource({ url: 'sop.api.bulk.record_types' })
const fields = createResource({ url: 'sop.api.bulk.filter_fields' })
const linked = createResource({ url: 'sop.api.bulk.linked_records' })
const past = createResource({ url: 'sop.api.bulk.history' })
const undoing = createResource({ url: 'sop.api.bulk.undo' })

const rows = computed(() => preview.data || [])

const typeOptions = computed(() =>
  (types.data || []).map((row) => ({
    label: `${row.doctype} — ${__('{0} linked in {1} procedures').format(row.records, row.procedures)}`,
    value: row.doctype,
  })),
)
const fieldOptions = computed(() => (fields.data || []).map((row) => ({ label: row.label, value: row.fieldname })))
const linkedOptions = computed(() =>
  (linked.data || [])
    .filter((row) => !record.names.includes(row.value))
    .map((row) => ({ label: row.label === row.value ? row.value : `${row.label} (${row.value})`, value: row.value })),
)

const titles = createResource({ url: 'sop.api.bulk.titles' })

watch(
  () => JSON.stringify(record.map),
  () => {
    const names = Object.values(record.map).filter(Boolean)
    if (record.doctype && names.length) titles.submit({ doctype: record.doctype, names: JSON.stringify(names) })
  },
)

function titleOf(name) {
  return titles.data?.[name] || (linked.data || []).find((row) => row.value === name)?.label || name
}

function linkedLabel(name) {
  const row = (linked.data || []).find((item) => item.value === name)
  return row && row.label !== name ? `${row.label} (${name})` : name
}

const foundRecords = computed(() => {
  const seen = new Map()
  for (const row of rows.value) {
    for (const match of row.matches) {
      if (match.record && !seen.has(match.record)) seen.set(match.record, { value: match.record, label: linkedLabel(match.record) })
    }
  }
  return [...seen.values()]
})

function addRule() {
  rules.value.push({ key: ruleKey++, find: '', replace: '' })
}

function addFilter() {
  record.filters.push({ field: '', operator: '=', value: '' })
}

function ruleRows() {
  return rules.value
    .filter((rule) => rule.find)
    .map((rule) => ({
      find: rule.find,
      replace: rule.replace,
      regex: regex.value ? 1 : 0,
      match_case: matchCase.value ? 1 : 0,
      whole_word: wholeWord.value ? 1 : 0,
      keep_case: keepCase.value ? 1 : 0,
    }))
}

function recordSpec() {
  const filters = record.filters
    .filter((row) => row.field && row.value !== '')
    .map((row) =>
      row.operator === 'like'
        ? [row.field, 'like', `%${row.value}%`]
        : row.operator === 'starts'
          ? [row.field, 'like', `${row.value}%`]
          : [row.field, row.operator, row.value],
    )
  return {
    doctype: record.doctype,
    names: record.find === 'pick' ? (everyLinked.value ? (linked.data || []).map((row) => row.value) : record.names) : [],
    filters: record.find === 'filter' ? filters : [],
    to: record.replaceBy === 'one' ? record.to : null,
    map: record.replaceBy === 'map' ? Object.fromEntries(Object.entries(record.map).filter(([, value]) => value)) : {},
  }
}

const everyLinked = computed(
  () => record.find === 'pick' && record.replaceBy === 'map' && !record.names.length && !!linked.data?.length,
)

const findReady = computed(() => {
  if (mode.value === 'text') return ruleRows().length > 0
  if (!record.doctype) return false
  if (record.find === 'pick') return record.names.length > 0 || everyLinked.value
  return record.filters.some((row) => row.field && row.value !== '')
})

const ready = computed(() => {
  if (!findReady.value) return false
  if (mode.value === 'record') return record.replaceBy === 'one' ? !!record.to : Object.values(record.map).some(Boolean)
  return true
})

function params() {
  const space = thisSpace.value ? activeSpace.value : undefined
  if (mode.value === 'record') return { space, record: JSON.stringify(recordSpec()) }
  return {
    space,
    rules: JSON.stringify(ruleRows()),
    fields: JSON.stringify(Object.keys(lookIn).filter((key) => lookIn[key])),
  }
}

const look = debounce(() => {
  if (mode.value === 'history') return
  if (!findReady.value) {
    preview.reset?.()
    searched.value = false
    return
  }
  preview.submit(params())
}, 350)

watch(
  () => [
    mode.value,
    JSON.stringify(rules.value.map((rule) => [rule.find, rule.replace])),
    matchCase.value,
    wholeWord.value,
    keepCase.value,
    regex.value,
    JSON.stringify(lookIn),
    thisSpace.value,
    record.doctype,
    record.find,
    JSON.stringify(record.names),
    JSON.stringify(record.filters),
    record.replaceBy,
    record.to,
    linked.data?.length,
  ],
  look,
)

watch(
  () => record.doctype,
  (doctype) => {
    record.names = []
    record.filters = []
    record.map = {}
    record.to = null
    if (!doctype) return
    fields.submit({ doctype })
    linked.submit({ doctype })
  },
)

watch(mode, (value) => {
  if (value === 'record' && !types.data) types.fetch()
  if (value === 'history') past.reload()
  preview.reset?.()
  searched.value = false
  confirming.value = null
})

function resultOf(match) {
  if (mode.value !== 'record') return match.with
  if (record.replaceBy === 'one') return match.with
  const target = record.map[match.record]
  if (!target) return ''
  return match.by_id ? target : titleOf(target)
}

function expand(name) {
  opened.value = opened.value === name ? null : name
}

function isChosen(row, index) {
  const list = only[row.name]
  return list ? list.includes(index) : true
}

function chosenIn(row) {
  const list = only[row.name]
  return list ? list.length : row.hits
}

function flipMatch(row, index) {
  const listed = row.matches.map((match) => match.index)
  const current = only[row.name] || listed
  only[row.name] = current.includes(index) ? current.filter((value) => value !== index) : [...current, index]
  if (!picked.value.includes(row.name) && only[row.name].length) toggle(row.name)
}

const hits = computed(() => rows.value.reduce((total, row) => total + row.hits, 0))
const chosen = computed(() => rows.value.filter((row) => picked.value.includes(row.name)))
const revisable = computed(() => chosen.value.filter((row) => row.status === 'Effective'))
const blocked = computed(() => chosen.value.filter((row) => !row.editable && row.status !== 'Effective'))
const allPicked = computed(() => rows.value.length && picked.value.length === rows.value.length)

const actionLabel = computed(() => {
  if (!picked.value.length) return __('Replace')
  const total = chosen.value.reduce((sum, row) => sum + chosenIn(row), 0)
  return __('Replace {0} matches in {1} procedures').format(total, picked.value.length)
})

function toggle(name) {
  picked.value = picked.value.includes(name) ? picked.value.filter((row) => row !== name) : [...picked.value, name]
}

function toggleAll() {
  picked.value = allPicked.value ? [] : rows.value.map((row) => row.name)
}

async function start() {
  const names = [...picked.value]
  const base = params()
  Object.assign(run, { busy: true, total: names.length, done: 0, changed: 0, failed: 0, current: '', batch: null, left: [] })

  try {
    await claim.submit({})
  } catch {
    Object.assign(run, { busy: false, total: 0 })
    return
  }

  for (const name of names) {
    const row = rows.value.find((item) => item.name === name)
    run.current = row?.sop_no || name

    try {
      const result = await apply.submit({
        ...base,
        names: [name],
        start_revision: startRevision.value ? 1 : 0,
        picks: only[name] ? { [name]: only[name] } : {},
        batch: run.batch || undefined,
      })
      run.batch = result.batch
      run.changed += result.changed.length
      run.left.push(...result.skipped)
    } catch {
      run.failed += 1
    }

    run.done += 1
  }

  await release.submit({}).catch(() => {})
  run.busy = false
  run.current = ''

  toast.success(run.changed ? __('Updated {0} procedures').format(run.changed) : __('Nothing changed'))
  if (run.failed) toast.error(__('{0} could not be saved').format(run.failed))

  reloadProcedures()
  look()
}

async function undoBatch(batch) {
  const result = await undoing.submit({ batch })
  const restored = result.restored.length
  toast.success(__('Undone in {0} procedures').format(restored))
  if (result.left.length) {
    toast.warning(
      __('{0} left as they are: {1}').format(
        result.left.length,
        result.left.map((row) => `${row.sop_no} (${row.reason})`).join(', '),
      ),
    )
  }
  if (result.restored.some((row) => row.revised)) {
    toast.info(__('Revisions started by the replace are still open. Discard them from the procedure if not needed.'))
  }
  reloadProcedures()
}

async function undoLast() {
  await undoBatch(run.batch)
  run.batch = null
  look()
}

async function undo(row) {
  if (confirming.value !== row.name) {
    confirming.value = row.name
    return
  }
  await undoBatch(row.name)
  confirming.value = null
  past.reload()
}

function when(value) {
  return value ? String(value).slice(0, 16).replace('T', ' ') : ''
}

const someoneElse = computed(() => !!busy.data?.busy)

watch(open, (value) => {
  if (value) {
    busy.reload()
    return
  }

  mode.value = 'text'
  rules.value = [{ key: ruleKey++, find: '', replace: '' }]
  Object.assign(record, { doctype: '', find: 'pick', names: [], filters: [], replaceBy: 'one', to: null, map: {} })
  searched.value = false
  startRevision.value = false
  opened.value = null
  picked.value = []
  confirming.value = null
  Object.assign(run, { busy: false, total: 0, done: 0, changed: 0, failed: 0, batch: null, left: [] })
  for (const key of Object.keys(only)) delete only[key]
  preview.reset?.()
})
</script>
