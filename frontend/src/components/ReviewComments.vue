<template>
  <Teleport to="body">
    <div
      v-if="spot"
      class="fixed z-40"
      :style="{ left: `${spot.left}px`, top: `${spot.top}px` }"
    >
      <Button
        variant="solid"
        size="sm"
        icon-left="lucide-message-square-plus"
        label="Comment"
        @mousedown.prevent="startComment"
      />
    </div>
  </Teleport>

  <section v-if="rows.length || draft" class="mt-10">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-ink-gray-8">Review comments</h2>
      <TabButtons
        v-if="rows.length"
        v-model="filter"
        :options="[
          { label: 'Open', value: 'Open' },
          { label: 'All', value: '' },
        ]"
      />
    </div>

    <div
      v-if="draft"
      class="mb-3 rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-3 py-3"
    >
      <p v-if="draft.quote" class="mb-2 border-l-2 border-outline-gray-3 pl-2 text-sm text-ink-gray-6">
        “{{ draft.quote }}”
      </p>
      <FormControl
        ref="input"
        type="textarea"
        placeholder="What has to change here?"
        v-model="draft.comment"
      />
      <div class="mt-2 flex justify-end gap-2">
        <Button variant="ghost" size="sm" label="Cancel" @click="draft = null" />
        <Button
          variant="solid"
          size="sm"
          label="Comment"
          :loading="add.loading"
          :disabled="!draft.comment"
          @click="save"
        />
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <div
        v-for="row in shown"
        :key="row.name"
        class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5"
        :class="row.status === 'Resolved' ? 'opacity-60' : ''"
      >
        <div class="flex items-center gap-2">
          <Avatar :image="row.image" :label="row.author" size="sm" />
          <span class="text-base text-ink-gray-8">{{ row.author }}</span>
          <span class="text-sm text-ink-gray-5">{{ row.when }}</span>
          <Badge v-if="row.status === 'Resolved'" theme="green" variant="subtle" size="sm">
            Resolved
          </Badge>

          <div class="ml-auto flex items-center gap-1">
            <Tooltip :text="row.status === 'Resolved' ? 'Reopen' : 'Mark resolved'">
              <Button
                variant="ghost"
                size="sm"
                :icon="row.status === 'Resolved' ? 'lucide-rotate-ccw' : 'lucide-check'"
                :label="row.status === 'Resolved' ? 'Reopen' : 'Resolve'"
                @click="flip(row)"
              />
            </Tooltip>
            <Tooltip v-if="row.is_mine" text="Delete">
              <Button
                variant="ghost"
                size="sm"
                icon="lucide-trash-2"
                label="Delete"
                @click="remove.submit({ name: row.name })"
              />
            </Tooltip>
          </div>
        </div>

        <p v-if="row.quote" class="mt-2 border-l-2 border-outline-gray-3 pl-2 text-sm text-ink-gray-6">
          “{{ row.quote }}”
        </p>

        <p class="mt-1.5 text-base text-ink-gray-8">{{ row.comment }}</p>
      </div>
    </div>

    <p v-if="!shown.length && !draft" class="py-4 text-sm text-ink-gray-5">
      Nothing open. Select any words in the procedure to comment on them.
    </p>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Avatar, Badge, Button, FormControl, TabButtons, Tooltip, createResource } from 'frappe-ui'

const props = defineProps({
  sop: { type: String, default: '' },
  version: { type: Number, default: null },
  body: { type: [Object, null], default: null },
})

const emit = defineEmits(['count'])

const filter = ref('Open')
const draft = ref(null)
const spot = ref(null)
const input = ref(null)
let picked = ''

const list = createResource({
  url: 'sop.api.review.comments',
  makeParams: () => ({ sop: props.sop }),
})

const add = createResource({
  url: 'sop.api.review.add_comment',
  onSuccess() {
    draft.value = null
    list.reload()
  },
})

const resolve = createResource({
  url: 'sop.api.review.resolve_comment',
  onSuccess: () => list.reload(),
})

const remove = createResource({
  url: 'sop.api.review.delete_comment',
  onSuccess: () => list.reload(),
})

const rows = computed(() => list.data || [])

const shown = computed(() =>
  filter.value ? rows.value.filter((row) => row.status === filter.value) : rows.value,
)

watch(rows, (value) => emit('count', value.filter((row) => row.status === 'Open').length))

watch(
  () => props.sop,
  (sop) => {
    if (sop) list.submit({ sop })
  },
  { immediate: true },
)

function onSelection() {
  const selection = window.getSelection()
  const text = selection?.toString().trim()

  if (!text || !props.body || !selection.rangeCount) {
    spot.value = null
    return
  }

  const range = selection.getRangeAt(0)
  if (!props.body.contains(range.commonAncestorContainer)) {
    spot.value = null
    return
  }

  const box = range.getBoundingClientRect()
  picked = text
  spot.value = { left: box.left, top: Math.max(8, box.top - 42) }
}

function startComment() {
  draft.value = { quote: picked.slice(0, 300), comment: '' }
  spot.value = null
  window.getSelection()?.removeAllRanges()

  nextTick(() => input.value?.$el?.querySelector('textarea')?.focus())
}

function save() {
  add.submit({
    sop: props.sop,
    version: props.version,
    quote: draft.value.quote,
    comment: draft.value.comment,
  })
}

function flip(row) {
  resolve.submit({ name: row.name, status: row.status === 'Resolved' ? 'Open' : 'Resolved' })
}

onMounted(() => document.addEventListener('selectionchange', onSelection))
onBeforeUnmount(() => document.removeEventListener('selectionchange', onSelection))
</script>
