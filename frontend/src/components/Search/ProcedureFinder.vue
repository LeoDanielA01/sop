<template>
  <div class="flex min-w-0 flex-1 flex-col gap-2">
    <div class="flex min-w-0 items-center gap-2">
      <TextInput
        v-model="query"
        class="min-w-0 flex-1"
        type="text"
        :placeholder="__('Search all procedures by title, number, words inside or a linked record')"
        autocomplete="off"
        @keydown.enter.prevent="takeTokens(true)"
      >
        <template #prefix>
          <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
        </template>
        <template v-if="query" #suffix>
          <button
            type="button"
            class="flex text-ink-gray-5 hover:text-ink-gray-8"
            :aria-label="__('Clear search')"
            @click="query = ''"
          >
            <span class="lucide-x size-4" aria-hidden="true" />
          </button>
        </template>
      </TextInput>

      <Dropdown :options="filterMenu" align="end">
        <Button icon-left="lucide-list-filter" :label="activeCount ? __('Filter ({0})').format(activeCount) : __('Filter')" />
      </Dropdown>

      <Dropdown :options="sortMenu" align="end">
        <Button icon-left="lucide-arrow-up-down" :label="sortLabel" />
      </Dropdown>
    </div>

    <div v-if="suggestions.length" class="flex flex-wrap items-center gap-1.5">
      <span class="text-sm text-ink-gray-5">{{ __('Filter by') }}</span>
      <button
        v-for="hint in suggestions"
        :key="`${hint.field}:${hint.value}`"
        type="button"
        class="inline-flex items-center gap-1 rounded-3 border border-dashed border-outline-gray-3 px-2 py-0.5 text-sm text-ink-gray-8 hover:bg-surface-gray-2"
        @click="useHint(hint)"
      >
        <span class="lucide-plus size-3 text-ink-gray-5" aria-hidden="true" />
        <span class="text-ink-gray-5">{{ hint.title }}:</span>
        {{ hint.label }}
      </button>
    </div>

    <div v-if="chips.length || corrected" class="flex flex-wrap items-center gap-1.5">
      <button
        v-for="chip in chips"
        :key="`${chip.field}:${chip.value}`"
        type="button"
        class="inline-flex items-center gap-1 rounded-3 border border-outline-gray-2 bg-surface-gray-1 px-2 py-0.5 text-sm text-ink-gray-8 hover:bg-surface-gray-2"
        :aria-label="__('Remove filter {0}').format(chip.label)"
        @click="drop(chip.field, chip.value)"
      >
        <span class="text-ink-gray-5">{{ chip.title }}:</span>
        {{ chip.label }}
        <span class="lucide-x size-3 text-ink-gray-5" aria-hidden="true" />
      </button>
      <Button v-if="chips.length > 1" variant="ghost" size="sm" :label="__('Clear all')" @click="clearFilters" />
      <span v-if="corrected" class="text-sm text-ink-gray-5">
        {{ __('Showing results for') }}
        <span class="font-medium text-ink-gray-8">{{ corrected }}</span>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dropdown, TextInput, debounce } from 'frappe-ui'
import { facets, filters, procedures, search, sort } from '@/data/procedures'
import { spaces } from '@/data/navigation'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()

const ALIASES = { status: 'status', is: 'status', in: 'space', space: 'space', type: 'type', risk: 'risk', owner: 'owner', review: 'review', changed: 'changed' }
const SINGLE = new Set(['review', 'changed'])
const TITLES = { status: 'Status', space: 'Space', type: 'Type', risk: 'Risk', owner: 'Owner', review: 'Review', changed: 'Changed' }
const URL_KEYS = { status: 'status', space: 'in', type: 'type', risk: 'risk', owner: 'owner', review: 'review', changed: 'changed' }
const TOKEN = /(^|\s)(status|is|in|space|type|risk|owner|review|changed):("[^"]*"|\S+)(?=\s)/gi
const LAST_TOKEN = /(^|\s)(status|is|in|space|type|risk|owner|review|changed):("[^"]*"|\S+)\s*$/i
const REVIEW = [
  { value: 'overdue', label: 'Overdue' },
  { value: 'due', label: 'Due in 30 days' },
]
const CHANGED = [
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
  { value: '90', label: 'Last 90 days' },
]
const SORTS = [
  { value: '', label: 'Best match' },
  { value: 'modified', label: 'Last changed' },
  { value: 'number', label: 'Number' },
  { value: 'title', label: 'Title' },
  { value: 'review', label: 'Review date' },
]

const query = ref(search.value)

const applySearch = debounce(() => {
  takeTokens(false)
  search.value = query.value.trim()
}, 300)

watch(query, applySearch)

const options = computed(() => ({
  status: (facets.data?.statuses || []).map((value) => ({ value, label: value })),
  type: (facets.data?.types || []).map((value) => ({ value, label: value })),
  risk: (facets.data?.risks || []).map((value) => ({ value, label: value })),
  space: spaces.value.map((row) => ({ value: row.name, label: row.title, codes: [row.space_code, row.title] })),
  owner: [{ value: 'me', label: 'Me' }, ...(facets.data?.owners || [])],
  review: REVIEW,
  changed: CHANGED,
}))

function canonical(field, raw) {
  const value = String(raw).replace(/^"|"$/g, '').trim()
  const key = value.toLowerCase().replace(/[-_]/g, ' ')
  const list = options.value[field] || []
  const exact = list.find(
    (option) =>
      String(option.value).toLowerCase() === key ||
      option.label.toLowerCase() === key ||
      (option.codes || []).some((code) => String(code || '').toLowerCase() === key),
  )
  if (exact) return exact.value
  if (field === 'changed') return value.replace(/\D/g, '') || '30'
  const partial = list.find((option) => option.label.toLowerCase().includes(key))
  return partial ? partial.value : value
}

function labelOf(field, value) {
  const option = (options.value[field] || []).find((row) => String(row.value) === String(value))
  if (option) return option.label
  return field === 'changed' ? __('Last {0} days').format(value) : value
}

function add(field, value) {
  const current = filters[field] || []
  if (SINGLE.has(field)) filters[field] = [value]
  else if (!current.includes(value)) filters[field] = [...current, value]
}

function drop(field, value) {
  filters[field] = (filters[field] || []).filter((row) => row !== value)
}

function toggle(field, value) {
  ;(filters[field] || []).includes(value) ? drop(field, value) : add(field, value)
}

function clearFilters() {
  for (const field of Object.keys(filters)) filters[field] = []
}

function takeTokens(all) {
  let text = query.value
  const take = (match, lead, key, value) => {
    const field = ALIASES[key.toLowerCase()]
    add(field, canonical(field, value))
    return lead
  }
  text = text.replace(TOKEN, take)
  if (all) text = text.replace(LAST_TOKEN, take)
  if (text !== query.value) query.value = text.replace(/\s{2,}/g, ' ').trimStart()
}

const chips = computed(() =>
  Object.entries(filters).flatMap(([field, values]) =>
    (values || []).map((value) => ({ field, value, title: __(TITLES[field]), label: labelOf(field, value) })),
  ),
)

const activeCount = computed(() => chips.value.length)

const corrected = computed(() => {
  const fixes = procedures.data?.corrected
  if (!fixes) return ''
  return Object.entries(fixes).reduce(
    (text, [wrong, right]) => text.replace(new RegExp(wrong.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi'), right),
    search.value,
  )
})

const MENU = [
  { field: 'status', icon: 'lucide-circle-dot' },
  { field: 'space', icon: 'lucide-folder' },
  { field: 'owner', icon: 'lucide-user' },
  { field: 'type', icon: 'lucide-file-text' },
  { field: 'risk', icon: 'lucide-triangle-alert' },
  { field: 'review', icon: 'lucide-calendar-clock' },
  { field: 'changed', icon: 'lucide-history' },
]

const filterMenu = computed(() =>
  MENU.map(({ field, icon }) => {
    const chosen = filters[field] || []
    return {
      label: chosen.length ? `${__(TITLES[field])} (${chosen.length})` : __(TITLES[field]),
      icon,
      submenu: (options.value[field] || []).map((option) => ({
        label: __(option.label),
        selected: chosen.includes(option.value),
        onClick: () => toggle(field, option.value),
      })),
    }
  }),
)

const HINT_WORDS = {
  my: ['owner', 'me'],
  mine: ['owner', 'me'],
  overdue: ['review', 'overdue'],
}

const STOP_WORDS = new Set(['sop', 'sops', 'the', 'and', 'for', 'with', 'all', 'procedure', 'procedures'])

const words = computed(() =>
  query.value
    .toLowerCase()
    .split(/\s+/)
    .filter(
      (word) =>
        word.length >= 3 && !STOP_WORDS.has(word) && !word.includes(':') && !word.startsWith('-') && !word.startsWith('"'),
    ),
)

const suggestions = computed(() => {
  const found = []
  const seen = new Set()
  const offer = (field, option, word) => {
    const key = `${field}:${option.value}`
    if (seen.has(key) || (filters[field] || []).includes(option.value)) return
    seen.add(key)
    found.push({ field, value: option.value, label: __(option.label), title: __(TITLES[field]), word })
  }

  for (const word of words.value) {
    const fixed = HINT_WORDS[word]
    if (fixed) {
      const option = (options.value[fixed[0]] || []).find((row) => row.value === fixed[1])
      if (option) offer(fixed[0], option, word)
    }

    for (const field of ['status', 'space', 'type', 'risk', 'owner']) {
      for (const option of options.value[field] || []) {
        const names = [option.label, ...(option.codes || [])].map((name) => String(name || '').toLowerCase())
        const hit = names.some((name) => name === word || name.split(/\s+/).some((part) => part.length >= 3 && part.startsWith(word)))
        if (hit && option.value !== 'me') offer(field, option, word)
      }
    }
  }

  return found.slice(0, 6)
})

function useHint(hint) {
  add(hint.field, hint.value)
  const pattern = new RegExp(`(^|\\s)${hint.word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?=\\s|$)`, 'i')
  query.value = query.value.replace(pattern, ' ').replace(/\s{2,}/g, ' ').trim()
}

const sortMenu = computed(() =>
  SORTS.filter((option) => option.value || search.value).map((option) => ({
    label: __(option.label),
    selected: (sort.value || '') === option.value,
    onClick: () => (sort.value = option.value),
  })),
)

const sortLabel = computed(() => {
  const chosen = SORTS.find((option) => option.value === (sort.value || ''))
  return chosen && (chosen.value || search.value) ? __(chosen.label) : __('Last changed')
})

const FINDER_KEYS = ['q', 'sort', ...Object.values(URL_KEYS)]

function fromRoute() {
  const read = (key) => [].concat(route.query[key] || []).filter(Boolean)

  query.value = route.query.q || ''
  search.value = query.value.trim()
  sort.value = route.query.sort || ''
  for (const [field, key] of Object.entries(URL_KEYS)) filters[field] = read(key)
}

function toRoute() {
  const next = { ...route.query }
  for (const key of FINDER_KEYS) delete next[key]
  if (search.value) next.q = search.value
  if (sort.value) next.sort = sort.value
  for (const [field, key] of Object.entries(URL_KEYS)) if (filters[field]?.length) next[key] = filters[field]
  if (JSON.stringify(next) !== JSON.stringify(route.query)) router.replace({ query: next })
}

onMounted(() => {
  facets.fetch()
  fromRoute()
})

watch([search, sort, () => JSON.stringify(filters)], toRoute)

watch(
  () => route.query,
  (current) => {
    const finding = search.value || sort.value || activeCount.value
    if (finding && !FINDER_KEYS.some((key) => current[key])) fromRoute()
  },
)
</script>
