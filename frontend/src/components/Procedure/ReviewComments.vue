<template>
  <Teleport to="body">
    <div v-if="spot" class="fixed z-40" :style="{ left: `${spot.left}px`, top: `${spot.top}px` }">
      <Button
        variant="solid"
        size="sm"
        icon-left="lucide-message-square-plus"
        :label="__('Comment')"
        @mousedown.prevent="startComment"
      />
    </div>
  </Teleport>

  <Teleport v-for="pin in pins" :key="pin.name" :to="pin.el">
    <button
      type="button"
      class="sop-review-pin"
      :class="pin.status === 'Resolved' ? 'is-done' : ''"
      :aria-label="`Comment by ${pin.author}`"
      @click.stop="open(pin.name)"
    >
      <span class="lucide-message-square size-3" aria-hidden="true" />
      <span v-if="pin.count > 1">{{ pin.count }}</span>
    </button>
  </Teleport>

  <Teleport to="body">
    <div
      v-if="card"
      ref="cardEl"
      class="fixed z-40 w-[22rem] max-w-[calc(100vw-2rem)] overflow-hidden rounded-4 border border-outline-gray-2 bg-surface-base shadow-2xl"
      :style="{ left: `${card.left}px`, top: `${card.top}px` }"
    >
      <template v-if="draft">
        <p v-if="draft.quote" class="border-b border-outline-gray-1 bg-surface-gray-1 px-3 py-2">
          <span class="border-l-2 border-outline-amber-2 pl-2 text-sm text-ink-gray-6">
            {{ draft.quote }}
          </span>
        </p>

        <div class="px-3 py-2.5">
          <FormControl
            ref="input"
            type="textarea"
            :placeholder="__('What has to change here?')"
            v-model="draft.comment"
          />
          <ErrorMessage class="mt-2" :message="add.error?.messages?.[0]" />
          <div class="mt-2 flex justify-end gap-2">
            <Button variant="ghost" size="sm" :label="__('Cancel')" @click="close" />
            <Button
              variant="solid"
              size="sm"
              :label="__('Comment')"
              :loading="add.loading"
              :disabled="!draft.comment"
              @click="save()"
            />
          </div>
        </div>
      </template>

      <template v-else-if="thread">
        <div class="flex items-center gap-2 border-b border-outline-gray-1 px-3 py-2">
          <Badge
            :theme="thread.status === 'Resolved' ? 'green' : 'orange'"
            variant="subtle"
            size="sm"
          >
            {{ thread.status }}
          </Badge>

          <div class="ml-auto flex items-center">
            <Tooltip :text="thread.status === 'Resolved' ? 'Reopen' : 'Mark resolved'">
              <Button
                variant="ghost"
                size="sm"
                :icon="thread.status === 'Resolved' ? 'lucide-rotate-ccw' : 'lucide-check'"
                :label="thread.status === 'Resolved' ? 'Reopen' : 'Mark resolved'"
                :loading="resolve.loading"
                @click="flip(thread)"
              />
            </Tooltip>
            <Tooltip v-if="thread.is_mine" :text="__('Delete')">
              <Button
                variant="ghost"
                size="sm"
                icon="lucide-trash-2"
                :label="__('Delete')"
                @click="remove.submit({ name: thread.name })"
              />
            </Tooltip>
            <Tooltip :text="__('Close')">
              <Button variant="ghost" size="sm" icon="lucide-x" :label="__('Close')" @click="close" />
            </Tooltip>
          </div>
        </div>

        <ScrollArea viewport-class="max-h-72">
          <div class="divide-y divide-outline-gray-1">
            <div v-for="row in [thread, ...thread.replies]" :key="row.name" class="px-3 py-2.5">
              <div class="flex items-center gap-2">
                <Avatar :image="row.image" :label="row.author" size="sm" />
                <span class="min-w-0 truncate text-base text-ink-gray-8">{{ row.author }}</span>
                <span class="shrink-0 text-sm text-ink-gray-5">{{ row.when }}</span>
  
                <Tooltip v-if="row.is_mine && row.name !== thread.name" :text="__('Delete')">
                  <Button
                    class="ml-auto"
                    variant="ghost"
                    size="sm"
                    icon="lucide-trash-2"
                    :label="__('Delete')"
                    @click="remove.submit({ name: row.name })"
                  />
                </Tooltip>
              </div>
  
              <p class="mt-1.5 whitespace-pre-line text-base text-ink-gray-8">{{ row.comment }}</p>
            </div>
          </div>
        </ScrollArea>

        <div v-if="thread.status !== 'Resolved'" class="border-t border-outline-gray-1 px-3 py-2">
          <FormControl
            type="text"
            :placeholder="`Reply to ${thread.author.split(' ')[0]}`"
            :modelValue="replies[thread.name] || ''"
            @update:modelValue="(value) => (replies[thread.name] = value)"
            @keyup.enter="save(thread)"
          />
        </div>
      </template>
    </div>
  </Teleport>

  <section v-if="loose.length" class="mt-10 border-t border-outline-gray-1 pt-5">
    <div class="mb-3 flex items-center gap-2">
      <span class="lucide-message-square-dashed size-4 text-ink-gray-5" aria-hidden="true" />
      <h2 class="text-base font-medium text-ink-gray-8">{{ __('Comments without a passage') }}</h2>
      <Badge variant="subtle" size="sm">{{ loose.length }}</Badge>
    </div>

    <div class="flex flex-col gap-2">
      <button
        v-for="row in loose"
        :key="row.name"
        type="button"
        class="flex items-start gap-2.5 rounded-4 border border-outline-gray-2 px-3 py-2.5 text-left hover:border-outline-gray-3"
        @click.stop="openLoose(row.name, $event)"
      >
        <Avatar :image="row.image" :label="row.author" size="sm" class="mt-0.5 shrink-0" />
        <span class="min-w-0 flex-1">
          <span class="block text-sm text-ink-gray-5">{{ row.author }} · {{ row.when }}</span>
          <span class="block truncate text-base text-ink-gray-8">{{ row.comment }}</span>
        </span>
        <Badge
          :theme="row.status === 'Resolved' ? 'green' : 'orange'"
          variant="subtle"
          size="sm"
          class="mt-0.5 shrink-0"
        >
          {{ row.status }}
        </Badge>
      </button>
    </div>
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
  ScrollArea,
  Tooltip,
  createResource,
} from 'frappe-ui'

const props = defineProps({
  sop: { type: String, default: '' },
  version: { type: Number, default: null },
  body: { type: [Object, null], default: null },
})

const emit = defineEmits(['count'])

const draft = ref(null)
const spot = ref(null)
const card = ref(null)
const active = ref(null)
const pins = ref([])
const placed = ref([])
const input = ref(null)
const cardEl = ref(null)
const replies = reactive({})
let picked = ''
let anchor = null

const list = createResource({
  url: 'sop.api.review.comments',
  makeParams: () => ({ sop: props.sop }),
  onSuccess: () => nextTick(decorate),
})

const add = createResource({
  url: 'sop.api.review.add_comment',
  onSuccess() {
    draft.value = null
    card.value = null
    list.reload()
  },
})

const resolve = createResource({
  url: 'sop.api.review.resolve_comment',
  onSuccess: () => list.reload(),
})

const remove = createResource({
  url: 'sop.api.review.delete_comment',
  onSuccess() {
    close()
    list.reload()
  },
})

const threads = computed(() => list.data || [])

const thread = computed(() => threads.value.find((row) => row.name === active.value) || null)

const loose = computed(() => threads.value.filter((row) => !placed.value.includes(row.name)))

const openCount = computed(() => threads.value.filter((row) => row.status === 'Open').length)

watch(openCount, (value) => emit('count', value))

watch(
  () => props.sop,
  (sop) => {
    close()
    if (sop) list.submit({ sop })
  },
  { immediate: true },
)

watch(
  () => [props.body, props.version],
  () => nextTick(decorate),
)

function clean() {
  const root = props.body
  if (!root) return

  for (const holder of root.querySelectorAll('[data-review-pin]')) holder.remove()

  for (const mark of root.querySelectorAll('mark[data-review]')) {
    const parent = mark.parentNode
    while (mark.firstChild) parent.insertBefore(mark.firstChild, mark)
    parent.removeChild(mark)
    parent.normalize()
  }
}

function measure(root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  let text = ''
  const map = []

  while (walker.nextNode()) {
    const node = walker.currentNode
    if (node.parentElement?.closest('[data-review-pin]')) continue

    const value = node.nodeValue || ''

    for (let index = 0; index < value.length; index += 1) {
      if (/\s/.test(value[index])) {
        if (!text || text.endsWith(' ')) continue
        text += ' '
      } else {
        text += value[index]
      }

      map.push({ node, offset: index })
    }
  }

  return { text, map }
}

function occurrences(text, needle) {
  const found = []
  let at = text.indexOf(needle)

  while (at >= 0) {
    found.push(at)
    at = text.indexOf(needle, at + 1)
  }

  return found
}

function sharedEnd(left, right) {
  let count = 0

  while (
    count < left.length &&
    count < right.length &&
    left[left.length - 1 - count] === right[right.length - 1 - count]
  ) {
    count += 1
  }

  return count
}

function sharedStart(left, right) {
  let count = 0

  while (count < left.length && count < right.length && left[count] === right[count]) count += 1

  return count
}

function bestMatch(text, needle, before, after) {
  let hits = occurrences(text, needle)
  if (!hits.length) hits = occurrences(text.toLowerCase(), needle.toLowerCase())
  if (!hits.length) return -1

  let best = hits[0]
  let top = -1

  for (const at of hits) {
    const score =
      sharedEnd(text.slice(0, at), before || '') +
      sharedStart(text.slice(at + needle.length), after || '')

    if (score > top) {
      top = score
      best = at
    }
  }

  return best
}

function contextOf(range) {
  const quote = range.toString().replace(/\s+/g, ' ').trim().slice(0, 300)
  const empty = { quote, before: '', after: '' }
  if (!props.body || !quote) return empty

  const { text, map } = measure(props.body)
  const start = map.findIndex(({ node, offset }) => range.isPointInRange(node, offset))
  const hits = occurrences(text, quote)
  if (start < 0 || !hits.length) return empty

  const at = hits.reduce(
    (best, index) => (Math.abs(index - start) < Math.abs(best - start) ? index : best),
    hits[0],
  )

  return {
    quote,
    before: text.slice(Math.max(0, at - 40), at),
    after: text.slice(at + quote.length, at + quote.length + 40),
  }
}

function rangeFor(root, row) {
  const needle = (row.quote || '').replace(/\s+/g, ' ').trim()
  if (!needle) return null

  const { text, map } = measure(root)
  const at = bestMatch(text, needle, row.quote_before, row.quote_after)
  if (at < 0) return null

  const first = map[at]
  const last = map[at + needle.length - 1]
  if (!first || !last) return null

  const range = document.createRange()
  range.setStart(first.node, first.offset)
  range.setEnd(last.node, last.offset + 1)

  return range
}

function decorate() {
  const root = props.body
  if (!root) return

  clean()

  const found = []
  const made = []

  for (const row of threads.value) {
    const range = rangeFor(root, row)
    if (!range) continue

    const mark = document.createElement('mark')
    mark.dataset.review = row.name
    mark.className = row.status === 'Resolved' ? 'sop-review-mark is-done' : 'sop-review-mark'

    try {
      mark.appendChild(range.extractContents())
      range.insertNode(mark)
    } catch {
      continue
    }

    const holder = document.createElement('span')
    holder.dataset.reviewPin = row.name
    mark.after(holder)

    found.push(row.name)
    made.push({
      name: row.name,
      el: holder,
      status: row.status,
      author: row.author,
      count: 1 + (row.replies?.length || 0),
    })
  }

  placed.value = found
  pins.value = made
}

function place(element) {
  if (!element) return null

  const box = element.getBoundingClientRect()
  const width = Math.min(352, window.innerWidth - 32)

  return {
    left: Math.max(16, Math.min(box.left, window.innerWidth - width - 16)),
    top: Math.min(box.bottom + 8, Math.max(16, window.innerHeight - 260)),
  }
}

function open(name) {
  draft.value = null
  active.value = name
  anchor = props.body?.querySelector(`mark[data-review="${name}"]`) || null
  card.value = place(anchor)
}

function openLoose(name, event) {
  draft.value = null
  active.value = name
  anchor = event.currentTarget
  card.value = place(anchor)
}

function close() {
  active.value = null
  draft.value = null
  card.value = null
  anchor = null
}

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
  const selection = window.getSelection()
  const range = selection?.rangeCount ? selection.getRangeAt(0) : null
  const box = range ? range.getBoundingClientRect() : null
  const width = Math.min(352, window.innerWidth - 32)
  const context = range ? contextOf(range) : { quote: picked.slice(0, 300), before: '', after: '' }

  active.value = null
  anchor = null
  spot.value = null
  draft.value = { ...context, comment: '' }
  card.value = box
    ? {
        left: Math.max(16, Math.min(box.left, window.innerWidth - width - 16)),
        top: Math.min(box.bottom + 8, Math.max(16, window.innerHeight - 260)),
      }
    : { left: 24, top: 120 }

  selection?.removeAllRanges()

  nextTick(() => input.value?.$el?.querySelector('textarea')?.focus())
}

function save(row) {
  const comment = row ? replies[row.name] : draft.value?.comment
  if (!comment) return

  add.submit({
    sop: props.sop,
    version: props.version,
    quote: row ? null : draft.value.quote,
    before: row ? null : draft.value.before,
    after: row ? null : draft.value.after,
    parent: row?.name || null,
    comment,
  })

  if (row) replies[row.name] = ''
}

function flip(row) {
  resolve.submit({
    name: row.name,
    status: row.status === 'Resolved' ? 'Open' : 'Resolved',
  })
}

function reposition() {
  if (!card.value || !anchor) return

  card.value = place(anchor)
}

function onDocumentClick(event) {
  if (!card.value) return
  if (cardEl.value?.contains(event.target)) return
  if (event.target.closest?.('.sop-review-pin')) return

  close()
}

function onEscape(event) {
  if (event.key === 'Escape') close()
}

onMounted(() => {
  document.addEventListener('selectionchange', onSelection)
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onEscape)
  window.addEventListener('scroll', reposition, true)
  window.addEventListener('resize', reposition)
})

onBeforeUnmount(() => {
  document.removeEventListener('selectionchange', onSelection)
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onEscape)
  window.removeEventListener('scroll', reposition, true)
  window.removeEventListener('resize', reposition)
  clean()
})
</script>

<style>
.sop-review-mark {
  background: var(--surface-amber-1);
  box-shadow: inset 0 -2px 0 0 var(--outline-amber-3);
  color: inherit;
  border-radius: var(--radius-1);
  padding: 0 1px;
}

.sop-review-mark.is-done {
  background: transparent;
  box-shadow: inset 0 -1px 0 0 var(--outline-gray-3);
}

.sop-review-pin {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  vertical-align: text-top;
  margin-left: 2px;
  padding: 1px 4px;
  border: 1px solid var(--outline-amber-2);
  border-radius: var(--radius-9);
  background: var(--surface-amber-2);
  color: var(--ink-amber-3);
  font-size: 11px;
  line-height: 1.4;
  cursor: pointer;
}

.sop-review-pin:hover {
  background: var(--surface-amber-3);
}

.sop-review-pin.is-done {
  border-color: var(--outline-gray-2);
  background: var(--surface-gray-2);
  color: var(--ink-gray-5);
}
</style>
