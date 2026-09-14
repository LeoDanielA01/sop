<template>
  <Dialog v-model:open="open" title="Find and replace" size="2xl">
    <template #default>
      <div class="flex flex-col gap-4">
        <ErrorMessage :message="apply.error?.messages?.[0] || preview.error?.messages?.[0]" />

        <div class="grid gap-3 sm:grid-cols-2">
          <FormControl
            type="text"
            label="Find"
            placeholder="Mixer A"
            v-model="find"
            @keyup.enter="look"
          />
          <FormControl type="text" label="Replace with" placeholder="Mixer B" v-model="replace" />
        </div>

        <div class="flex flex-wrap items-center gap-4">
          <FormControl type="checkbox" label="Match case" v-model="matchCase" />
          <FormControl type="checkbox" label="Whole word only" v-model="wholeWord" />
          <FormControl type="checkbox" label="This space only" v-model="thisSpace" />

          <span v-if="preview.loading" class="ml-auto text-sm text-ink-gray-5">Searching…</span>
        </div>

        <div v-if="rows.length" class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <label class="flex cursor-pointer items-center gap-2 text-sm text-ink-gray-6">
              <FormControl
                type="checkbox"
                :modelValue="allPicked"
                @update:modelValue="toggleAll"
              />
              Select all
            </label>
            <span class="text-sm text-ink-gray-5">
              {{ hits }} match{{ hits === 1 ? '' : 'es' }} in {{ rows.length }} procedure{{
                rows.length === 1 ? '' : 's'
              }}
            </span>
          </div>

          <div class="flex max-h-72 flex-col gap-1.5 overflow-y-auto p-0.5">
            <label
              v-for="row in rows"
              :key="row.name"
              class="flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2.5"
              :class="
                picked.includes(row.name)
                  ? 'border-outline-gray-3 bg-surface-gray-2'
                  : 'border-outline-gray-2 bg-surface-gray-1 hover:border-outline-gray-3'
              "
            >
              <FormControl
                type="checkbox"
                class="mt-0.5"
                :modelValue="picked.includes(row.name)"
                @update:modelValue="() => toggle(row.name)"
              />

              <div class="min-w-0 flex-1">
                <div class="flex min-w-0 items-center gap-2">
                  <span class="shrink-0 font-mono text-sm text-ink-gray-5">{{ row.sop_no }}</span>
                  <span class="truncate text-base text-ink-gray-8">{{ row.title }}</span>
                  <Badge :theme="STATUS_THEME[row.status]" variant="subtle" size="sm">
                    {{ row.status }}
                  </Badge>
                </div>
                <p v-if="row.snippet" class="mt-1 truncate text-sm text-ink-gray-5">
                  <template v-for="(part, index) in parts(row.snippet)" :key="index">
                    <mark
                      v-if="part.hit"
                      class="rounded-md bg-surface-amber-2 px-0.5 text-ink-gray-8"
                    >
                      {{ part.text }}
                    </mark>
                    <template v-else>{{ part.text }}</template>
                  </template>
                </p>

                <p v-if="row.snippet && replace" class="mt-1 truncate text-sm text-ink-gray-5">
                  <span class="lucide-corner-down-right mr-1 inline-block size-3" aria-hidden="true" />
                  <template v-for="(part, index) in parts(row.snippet, true)" :key="index">
                    <mark
                      v-if="part.hit"
                      class="rounded-md bg-surface-green-2 px-0.5 text-ink-gray-8"
                    >
                      {{ part.text }}
                    </mark>
                    <template v-else>{{ part.text }}</template>
                  </template>
                </p>
              </div>

              <Badge variant="subtle" size="sm">{{ row.hits }}</Badge>
            </label>
          </div>

          <div
            v-if="revisable.length"
            class="flex items-start gap-2.5 rounded-lg border border-outline-amber-1 bg-surface-amber-1 px-3 py-2.5 text-sm text-ink-amber-6"
          >
            <span class="lucide-triangle-alert mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <div class="min-w-0">
              <p>
                {{ revisable.length }} of these {{ revisable.length === 1 ? 'is' : 'are' }} in force.
                Editing one has to go through a revision and be approved again.
              </p>
              <label class="mt-1.5 flex cursor-pointer items-center gap-2">
                <FormControl type="checkbox" v-model="startRevision" />
                Start a revision for {{ revisable.length === 1 ? 'it' : 'them' }}
              </label>
            </div>
          </div>

          <p
            v-if="blocked.length"
            class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5 text-sm text-ink-gray-6"
          >
            {{ blocked.length }} cannot be changed yet — {{ blockedReason }}. They will be left
            alone.
          </p>
        </div>

        <p
          v-else-if="searched && !preview.loading"
          class="rounded-lg border border-dashed border-outline-gray-2 px-3 py-6 text-center text-sm text-ink-gray-5"
        >
          Nothing contains “{{ find }}”.
        </p>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          :label="actionLabel"
          :loading="apply.loading"
          :disabled="!picked.length"
          @click="run"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  createResource,
  debounce,
  toast,
} from 'frappe-ui'
import { activeSpace } from '@/data/navigation'
import { reloadProcedures } from '@/data/procedures'
import { STATUS_THEME } from '@/utils/format'

const open = defineModel('open', { type: Boolean, default: false })

const find = ref('')
const replace = ref('')
const matchCase = ref(false)
const wholeWord = ref(false)
const thisSpace = ref(true)
const startRevision = ref(false)
const searched = ref(false)
const picked = ref([])

const preview = createResource({
  url: 'sop.api.bulk.preview',
  onSuccess(data) {
    searched.value = true
    picked.value = data.filter((row) => row.editable).map((row) => row.name)
  },
})

const apply = createResource({
  url: 'sop.api.bulk.apply',
  onSuccess(data) {
    const count = data.changed.length
    toast.success(count ? `Updated ${count} procedure${count === 1 ? '' : 's'}` : 'Nothing changed')

    if (data.skipped.length) {
      const reasons = [...new Set(data.skipped.map((row) => row.status.toLowerCase()))].join(', ')
      toast.warning(`${data.skipped.length} left alone — ${reasons}`)
    }

    open.value = false
    reloadProcedures()
  },
})

const rows = computed(() => preview.data || [])

const matcher = computed(() => {
  if (!find.value) return null

  const escaped = find.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const body = wholeWord.value ? `\\b${escaped}\\b` : escaped

  return new RegExp(`(${body})`, matchCase.value ? 'g' : 'gi')
})

function parts(text, replaced = false) {
  if (!matcher.value) return [{ text, hit: false }]

  return text
    .split(matcher.value)
    .filter((piece) => piece !== '')
    .map((piece, index) => {
      const hit = matcher.value.test(piece)
      matcher.value.lastIndex = 0

      return { text: hit && replaced ? replace.value : piece, hit }
    })
    .filter((piece) => piece.text !== '')
}

const actionLabel = computed(() => {
  const total = chosen.value.reduce((sum, row) => sum + row.hits, 0)
  if (!picked.value.length) return 'Replace'

  const what = replace.value ? 'Replace' : 'Remove'
  return `${what} ${total} match${total === 1 ? '' : 'es'} in ${picked.value.length} procedure${
    picked.value.length === 1 ? '' : 's'
  }`
})
const hits = computed(() => rows.value.reduce((total, row) => total + row.hits, 0))
const chosen = computed(() => rows.value.filter((row) => picked.value.includes(row.name)))

const revisable = computed(() => chosen.value.filter((row) => row.status === 'Effective'))

const blocked = computed(() =>
  chosen.value.filter((row) => !row.editable && row.status !== 'Effective'),
)

const blockedReason = computed(() =>
  [...new Set(blocked.value.map((row) => row.status.toLowerCase()))].join(' or '),
)
const allPicked = computed(() => rows.value.length && picked.value.length === rows.value.length)

const look = debounce(() => {
  if (!find.value) {
    preview.reset?.()
    searched.value = false
    return
  }

  preview.submit({
    find: find.value,
    space: thisSpace.value ? activeSpace.value : undefined,
    match_case: matchCase.value ? 1 : 0,
    whole_word: wholeWord.value ? 1 : 0,
  })
}, 300)

watch([find, matchCase, wholeWord, thisSpace], look)

function toggle(name) {
  picked.value = picked.value.includes(name)
    ? picked.value.filter((row) => row !== name)
    : [...picked.value, name]
}

function toggleAll() {
  picked.value = allPicked.value ? [] : rows.value.map((row) => row.name)
}

function run() {
  apply.submit({
    find: find.value,
    replace: replace.value,
    names: picked.value,
    match_case: matchCase.value ? 1 : 0,
    whole_word: wholeWord.value ? 1 : 0,
    start_revision: startRevision.value ? 1 : 0,
  })
}

watch(open, (value) => {
  if (value) return

  find.value = ''
  replace.value = ''
  searched.value = false
  startRevision.value = false
  picked.value = []
  preview.reset?.()
})
</script>
