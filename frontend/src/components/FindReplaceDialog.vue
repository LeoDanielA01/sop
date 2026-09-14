<template>
  <Dialog v-model:open="open" title="Find and replace" size="2xl">
    <template #default>
      <div class="flex flex-col gap-4">
        <ErrorMessage
          :message="
            claim.error?.messages?.[0] || apply.error?.messages?.[0] || preview.error?.messages?.[0]
          "
        />

        <p
          v-if="someoneElse"
          class="flex items-start gap-2 rounded-4 border border-outline-amber-1 bg-surface-amber-1 px-3 py-2.5 text-sm text-ink-amber-6"
        >
          <span class="lucide-lock mt-0.5 size-4 shrink-0" aria-hidden="true" />
          {{ busy.data.holder }} is running a replace right now. Wait until it finishes.
        </p>

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

        <div
          v-if="run.total"
          class="flex flex-col gap-2 rounded-4 border border-outline-gray-2 bg-surface-gray-1 px-3 py-3"
        >
          <div class="flex items-center justify-between text-sm">
            <span class="text-ink-gray-7">
              <template v-if="run.busy">Replacing {{ run.done + 1 }} of {{ run.total }}</template>
              <template v-else>Finished {{ run.total }} procedure{{ run.total === 1 ? '' : 's' }}</template>
            </span>
            <span class="font-mono text-ink-gray-5">{{ run.current }}</span>
          </div>

          <Progress :value="Math.round((run.done * 100) / run.total)" size="sm" />

          <div class="flex flex-wrap gap-x-4 gap-y-1 text-sm">
            <span v-if="run.changed" class="text-ink-green-3">{{ run.changed }} updated</span>
            <span v-if="run.skipped" class="text-ink-gray-5">{{ run.skipped }} left alone</span>
            <span v-if="run.failed" class="text-ink-red-3">{{ run.failed }} failed</span>
          </div>
        </div>

        <div v-if="rows.length && !run.busy" class="flex flex-col gap-2">
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

          <div class="flex max-h-80 flex-col gap-1.5 overflow-y-auto p-0.5">
            <div
              v-for="row in rows"
              :key="row.name"
              class="rounded-4 border"
              :class="
                picked.includes(row.name)
                  ? 'border-outline-gray-3 bg-surface-gray-2'
                  : 'border-outline-gray-2 bg-surface-gray-1'
              "
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
                    <Badge :theme="STATUS_THEME[row.status]" variant="subtle" size="sm">
                      {{ row.status }}
                    </Badge>
                  </div>
                  <p class="mt-0.5 text-sm text-ink-gray-5">
                    {{ chosenIn(row) }} of {{ row.hits }} will change
                  </p>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  :icon="opened === row.name ? 'lucide-chevron-up' : 'lucide-chevron-down'"
                  :label="opened === row.name ? 'Hide matches' : 'Show matches'"
                  @click="expand(row.name)"
                />
                <Badge variant="subtle" size="sm">{{ row.hits }}</Badge>
              </div>

              <div
                v-if="opened === row.name"
                class="divide-y divide-outline-gray-1 border-t border-outline-gray-1"
              >
                <label
                  v-for="match in row.matches"
                  :key="match.index"
                  class="flex cursor-pointer items-start gap-3 px-3 py-2"
                >
                  <FormControl
                    type="checkbox"
                    class="mt-0.5"
                    :modelValue="isChosen(row, match.index)"
                    @update:modelValue="() => flipMatch(row, match.index)"
                  />

                  <span class="min-w-0 flex-1 text-sm text-ink-gray-6">
                    <span>{{ match.before }}</span>
                    <mark class="rounded-3 bg-surface-amber-2 px-0.5 text-ink-gray-8">
                      {{ match.hit }}
                    </mark>
                    <span>{{ match.after }}</span>

                    <span v-if="replace" class="mt-1 block text-ink-gray-5">
                      <span class="lucide-corner-down-right mr-1 inline-block size-3" aria-hidden="true" />
                      <span>{{ match.before }}</span>
                      <mark class="rounded-3 bg-surface-green-2 px-0.5 text-ink-gray-8">
                        {{ replace }}
                      </mark>
                      <span>{{ match.after }}</span>
                    </span>
                  </span>
                </label>

                <p
                  v-if="row.hits > row.matches.length"
                  class="px-3 py-2 text-sm text-ink-gray-5"
                >
                  {{ row.hits - row.matches.length }} more not listed — they change with the rest.
                </p>
              </div>
            </div>
          </div>

          <div
            v-if="revisable.length"
            class="flex items-start gap-2.5 rounded-4 border border-outline-amber-1 bg-surface-amber-1 px-3 py-2.5 text-sm text-ink-amber-6"
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
            class="rounded-4 border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5 text-sm text-ink-gray-6"
          >
            {{ blocked.length }} cannot be changed yet — {{ blockedReason }}. They will be left
            alone.
          </p>
        </div>

        <p
          v-else-if="searched && !preview.loading"
          class="rounded-4 border border-dashed border-outline-gray-2 px-3 py-6 text-center text-sm text-ink-gray-5"
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
          :loading="run.busy"
          :disabled="!picked.length || run.busy"
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
  Dialog,
  ErrorMessage,
  FormControl,
  Progress,
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

const apply = createResource({ url: 'sop.api.bulk.apply' })
const claim = createResource({ url: 'sop.api.bulk.claim' })
const release = createResource({ url: 'sop.api.bulk.release' })
const busy = createResource({ url: 'sop.api.bulk.busy' })

const run = reactive({
  busy: false,
  total: 0,
  done: 0,
  changed: 0,
  skipped: 0,
  failed: 0,
  current: '',
})

const rows = computed(() => preview.data || [])

const opened = ref(null)
const only = reactive({})

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

  only[row.name] = current.includes(index)
    ? current.filter((value) => value !== index)
    : [...current, index]

  if (!picked.value.includes(row.name) && only[row.name].length) toggle(row.name)
}

const actionLabel = computed(() => {
  const total = chosen.value.reduce((sum, row) => sum + chosenIn(row), 0)
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
    replace: replace.value,
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

async function start() {
  const names = [...picked.value]

  Object.assign(run, {
    busy: true,
    total: names.length,
    done: 0,
    changed: 0,
    skipped: 0,
    failed: 0,
    current: '',
  })

  try {
    await claim.submit({})
  } catch (error) {
    Object.assign(run, { busy: false, total: 0 })
    return
  }

  for (const name of names) {
    const row = rows.value.find((item) => item.name === name)
    run.current = row?.sop_no || name

    try {
      const result = await apply.submit({
        find: find.value,
        replace: replace.value,
        names: [name],
        match_case: matchCase.value ? 1 : 0,
        whole_word: wholeWord.value ? 1 : 0,
        start_revision: startRevision.value ? 1 : 0,
        picks: only[name] ? { [name]: only[name] } : {},
      })

      run.changed += result.changed.length
      run.skipped += result.skipped.length
    } catch (error) {
      run.failed += 1
    }

    run.done += 1
  }

  await release.submit({}).catch(() => {})

  run.busy = false
  run.current = ''

  toast.success(
    run.changed ? `Updated ${run.changed} procedure${run.changed === 1 ? '' : 's'}` : 'Nothing changed',
  )

  if (run.skipped) toast.warning(`${run.skipped} left alone`)
  if (run.failed) toast.error(`${run.failed} could not be saved`)

  reloadProcedures()
  look()
}

const someoneElse = computed(() => !!busy.data?.busy)

watch(open, (value) => {
  if (value) {
    busy.reload()
    return
  }

  find.value = ''
  replace.value = ''
  searched.value = false
  startRevision.value = false
  opened.value = null
  picked.value = []
  Object.assign(run, { busy: false, total: 0, done: 0, changed: 0, skipped: 0, failed: 0 })

  for (const key of Object.keys(only)) delete only[key]
  preview.reset?.()
})
</script>
