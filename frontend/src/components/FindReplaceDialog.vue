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

          <Button
            class="ml-auto"
            variant="subtle"
            icon-left="lucide-search"
            label="Find"
            :loading="preview.loading"
            :disabled="!find"
            @click="look"
          />
        </div>

        <div v-if="rows.length" class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <span class="text-sm text-ink-gray-5">
              {{ hits }} in {{ rows.length }} procedure{{ rows.length === 1 ? '' : 's' }}
            </span>
            <Button
              variant="ghost"
              size="sm"
              :label="allPicked ? 'Clear all' : 'Select all'"
              @click="toggleAll"
            />
          </div>

          <div
            class="max-h-72 divide-y divide-outline-gray-1 overflow-y-auto rounded-lg border border-outline-gray-2 bg-surface-gray-1"
          >
            <label
              v-for="row in rows"
              :key="row.name"
              class="flex cursor-pointer items-start gap-3 px-3 py-2.5"
            >
              <FormControl
                type="checkbox"
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
                <p v-if="row.snippet" class="mt-0.5 truncate text-sm text-ink-gray-5">
                  {{ row.snippet }}
                </p>
              </div>

              <Badge variant="subtle" size="sm">{{ row.hits }}</Badge>
            </label>
          </div>

          <div
            v-if="locked.length"
            class="flex items-start gap-2 rounded-lg border border-outline-amber-1 bg-surface-amber-1 px-3 py-2.5 text-sm text-ink-amber-6"
          >
            <span class="lucide-triangle-alert mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <div class="min-w-0">
              <p>
                {{ locked.length }} of these are in force. Editing one has to go through a revision
                and be approved again.
              </p>
              <FormControl
                class="mt-1.5"
                type="checkbox"
                label="Start a revision for those too"
                v-model="startRevision"
              />
            </div>
          </div>
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
          :label="`Replace in ${picked.length} procedure${picked.length === 1 ? '' : 's'}`"
          :loading="apply.loading"
          :disabled="!picked.length || !replace"
          @click="run"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Badge, Button, Dialog, ErrorMessage, FormControl, createResource, toast } from 'frappe-ui'
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
      toast.warning(`${data.skipped.length} left alone — in force`)
    }

    open.value = false
    reloadProcedures()
  },
})

const rows = computed(() => preview.data || [])
const hits = computed(() => rows.value.reduce((total, row) => total + row.hits, 0))
const locked = computed(() => rows.value.filter((row) => !row.editable && picked.value.includes(row.name)))
const allPicked = computed(() => rows.value.length && picked.value.length === rows.value.length)

function look() {
  if (!find.value) return

  preview.submit({
    find: find.value,
    space: thisSpace.value ? activeSpace.value : undefined,
    match_case: matchCase.value ? 1 : 0,
    whole_word: wholeWord.value ? 1 : 0,
  })
}

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
