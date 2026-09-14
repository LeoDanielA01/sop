<template>
  <Teleport to="body">
    <div v-if="spot" class="fixed z-40" :style="{ left: `${spot.left}px`, top: `${spot.top}px` }">
      <Button
        variant="solid"
        size="sm"
        icon-left="lucide-message-square-plus"
        label="Comment"
        @mousedown.prevent="startComment"
      />
    </div>
  </Teleport>

  <section v-if="threads.length || draft" class="mt-10">
    <div class="mb-3 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <h2 class="text-lg font-semibold text-ink-gray-8">Review</h2>
        <Badge v-if="openCount" variant="subtle" theme="orange" size="sm">
          {{ openCount }} open
        </Badge>
      </div>

      <TabButtons
        v-if="threads.length"
        v-model="filter"
        :options="[
          { label: 'Open', value: 'Open' },
          { label: 'All', value: '' },
        ]"
      />
    </div>

    <ErrorMessage class="mb-3" :message="add.error?.messages?.[0] || remove.error?.messages?.[0]" />

    <div
      v-if="draft"
      class="mb-3 overflow-hidden rounded-4 border border-outline-gray-2 bg-surface-base"
    >
      <p v-if="draft.quote" class="border-b border-outline-gray-1 bg-surface-gray-1 px-3 py-2">
        <span class="border-l-2 border-outline-amber-2 pl-2 text-sm text-ink-gray-6">
          {{ draft.quote }}
        </span>
      </p>

      <div class="px-3 py-2.5">
        <FormControl
          ref="input"
          type="textarea"
          placeholder="Leave a comment on this passage"
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
            @click="save()"
          />
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <div
        v-for="thread in shown"
        :key="thread.name"
        class="overflow-hidden rounded-4 border border-outline-gray-2 bg-surface-base"
        :class="thread.status === 'Resolved' ? 'opacity-70' : ''"
      >
        <div
          v-if="thread.quote"
          class="border-b border-outline-gray-1 bg-surface-gray-1 px-3 py-2"
        >
          <span class="border-l-2 border-outline-amber-2 pl-2 text-sm text-ink-gray-6">
            {{ thread.quote }}
          </span>
        </div>

        <div class="divide-y divide-outline-gray-1">
          <div v-for="row in [thread, ...thread.replies]" :key="row.name" class="px-3 py-2.5">
            <div class="flex items-center gap-2">
              <Avatar :image="row.image" :label="row.author" size="sm" />
              <span class="text-base text-ink-gray-8">{{ row.author }}</span>
              <span class="text-sm text-ink-gray-5">{{ row.when }}</span>

              <Badge
                v-if="row.name === thread.name && thread.status === 'Resolved'"
                theme="green"
                variant="subtle"
                size="sm"
              >
                Resolved
              </Badge>

              <div class="ml-auto flex items-center gap-1">
                <Tooltip
                  v-if="row.name === thread.name"
                  :text="thread.status === 'Resolved' ? 'Reopen' : 'Mark resolved'"
                >
                  <Button
                    variant="ghost"
                    size="sm"
                    :icon="thread.status === 'Resolved' ? 'lucide-rotate-ccw' : 'lucide-check'"
                    :label="thread.status === 'Resolved' ? 'Reopen' : 'Resolve'"
                    @click="flip(thread)"
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

            <p class="mt-1.5 whitespace-pre-line text-base text-ink-gray-8">{{ row.comment }}</p>
          </div>
        </div>

        <div v-if="thread.status !== 'Resolved'" class="border-t border-outline-gray-1 px-3 py-2">
          <FormControl
            type="text"
            :placeholder="`Reply to ${thread.author.split(' ')[0]}`"
            :modelValue="replies[thread.name] || ''"
            @update:modelValue="(value) => (replies[thread.name] = value)"
            @keyup.enter="save(thread)"
          />
        </div>
      </div>
    </div>

    <p v-if="!shown.length && !draft" class="py-4 text-sm text-ink-gray-5">
      Nothing open. Select any words in the procedure to comment on them.
    </p>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import {
  Avatar,
  Badge,
  Button,
  ErrorMessage,
  FormControl,
  TabButtons,
  Tooltip,
  createResource,
} from 'frappe-ui'

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
const replies = reactive({})
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

const threads = computed(() => list.data || [])

const shown = computed(() =>
  filter.value ? threads.value.filter((row) => row.status === filter.value) : threads.value,
)

const openCount = computed(() => threads.value.filter((row) => row.status === 'Open').length)

watch(openCount, (value) => emit('count', value))

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

function save(thread) {
  const comment = thread ? replies[thread.name] : draft.value.comment
  if (!comment) return

  add.submit({
    sop: props.sop,
    version: props.version,
    quote: thread ? null : draft.value.quote,
    parent: thread?.name || null,
    comment,
  })

  if (thread) replies[thread.name] = ''
}

function flip(thread) {
  resolve.submit({
    name: thread.name,
    status: thread.status === 'Resolved' ? 'Open' : 'Resolved',
  })
}

onMounted(() => document.addEventListener('selectionchange', onSelection))
onBeforeUnmount(() => document.removeEventListener('selectionchange', onSelection))
</script>
