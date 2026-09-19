<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-150"
      leave-active-class="transition-opacity duration-150"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div v-if="chat.open" class="fixed inset-0 z-[19] bg-black/10" @click="chat.open = false" />
    </Transition>

    <div class="pointer-events-none fixed inset-0 z-20 overflow-hidden">
      <Transition
        enter-active-class="transition-transform duration-200 ease-out"
        leave-active-class="transition-transform duration-150 ease-in"
        enter-from-class="translate-x-full"
        leave-to-class="translate-x-full"
      >
        <aside
          v-if="chat.open"
          class="pointer-events-auto absolute inset-y-0 right-0 flex w-full flex-col border-l border-outline-gray-2 bg-surface-base shadow-2xl sm:w-[26rem]"
        >
          <div class="flex items-center gap-2 border-b border-outline-gray-1 px-3 py-2.5">
            <template v-if="chat.person">
              <Button variant="ghost" icon="lucide-arrow-left" :label="__('All messages')" @click="showInbox" />
              <Avatar :image="chat.person.image" :label="chat.person.full_name" size="lg" shape="circle" />
              <p class="min-w-0 flex-1 truncate text-base font-semibold text-ink-gray-9">
                {{ chat.person.full_name }}
              </p>

              <Tooltip :text="__('Call')">
                <Button
                  variant="ghost"
                  icon="lucide-phone"
                  :label="__('Call')"
                  @click="startCall(chat.person, chat.sop)"
                />
              </Tooltip>
              <Tooltip :text="__('Email')">
                <Button
                  variant="ghost"
                  icon="lucide-mail"
                  :label="__('Email')"
                  @click="openMail(chat.person, chat.sop)"
                />
              </Tooltip>
            </template>

            <template v-else>
              <span class="flex-1 px-1 text-lg font-semibold text-ink-gray-9">{{ __('Messages') }}</span>
            </template>

            <Tooltip :text="__('Close')">
              <Button variant="ghost" icon="lucide-x" :label="__('Close')" @click="chat.open = false" />
            </Tooltip>
          </div>

          <template v-if="!chat.person">
            <div class="px-3 pt-3">
              <TextInput v-model="query" type="text" :placeholder="__('Find someone')" autocomplete="off">
                <template #prefix>
                  <span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
                </template>
              </TextInput>
            </div>

            <div class="min-h-0 flex-1 overflow-y-auto py-2">
              <template v-if="query.trim()">
                <button
                  v-for="row in people.data || []"
                  :key="row.name"
                  type="button"
                  class="flex w-full items-center gap-2.5 px-4 py-2 text-left hover:bg-surface-gray-2"
                  @click="pick(row)"
                >
                  <Avatar :image="row.image" :label="row.full_name" size="lg" shape="circle" />
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-base text-ink-gray-9">{{ row.full_name }}</span>
                    <span class="block truncate text-sm text-ink-gray-5">{{ row.name }}</span>
                  </span>
                </button>

                <p
                  v-if="!people.loading && !(people.data || []).length"
                  class="px-4 py-6 text-center text-sm text-ink-gray-5"
                >
                  {{ __('Nobody matches that.') }}
                </p>
              </template>

              <template v-else-if="(threads.data || []).length">
                <button
                  v-for="row in threads.data"
                  :key="row.person.name"
                  type="button"
                  class="flex w-full items-center gap-2.5 px-4 py-2.5 text-left hover:bg-surface-gray-2"
                  @click="pick(row.person)"
                >
                  <Avatar :image="row.person.image" :label="row.person.full_name" size="lg" shape="circle" />
                  <span class="min-w-0 flex-1">
                    <span class="flex items-center gap-2">
                      <span
                        class="min-w-0 flex-1 truncate text-base"
                        :class="row.unread ? 'font-semibold text-ink-gray-9' : 'text-ink-gray-8'"
                      >
                        {{ row.person.full_name }}
                      </span>
                      <span class="shrink-0 text-xs text-ink-gray-5">{{ when(row.last.creation) }}</span>
                    </span>
                    <span class="mt-0.5 flex items-center gap-2">
                      <span
                        class="min-w-0 flex-1 truncate text-sm"
                        :class="row.unread ? 'text-ink-gray-8' : 'text-ink-gray-5'"
                      >
                        {{ preview(row.last) }}
                      </span>
                      <Badge v-if="row.unread" theme="red" variant="subtle" size="sm">{{ row.unread }}</Badge>
                    </span>
                  </span>
                </button>
              </template>

              <div v-else-if="!threads.loading" class="flex flex-col items-center px-8 pb-10 pt-20 text-center">
                <span class="grid size-10 place-content-center rounded-full bg-surface-gray-2" aria-hidden="true">
                  <span class="lucide-message-square size-5 text-ink-gray-5" />
                </span>
                <p class="mt-3 text-base font-medium text-ink-gray-7">{{ __('No conversations yet') }}</p>
                <p class="mt-1 text-sm text-ink-gray-5">{{ __('Find someone above to start one.') }}</p>
              </div>
            </div>
          </template>

          <template v-else>
            <div ref="scroller" class="min-h-0 flex-1 overflow-y-auto px-4 py-3">
              <div v-if="chat.loading" class="flex flex-col gap-3">
                <Skeleton class="h-8 w-2/3 rounded-3" />
                <Skeleton class="ml-auto h-8 w-1/2 rounded-3" />
                <Skeleton class="h-8 w-3/5 rounded-3" />
              </div>

              <template v-else>
                <div v-if="more" class="mb-3 flex justify-center">
                  <Button variant="ghost" size="sm" :label="__('Show earlier')" :loading="earlier" @click="showEarlier" />
                </div>

                <p
                  v-if="!chat.messages.length"
                  class="px-6 pt-16 text-center text-sm text-ink-gray-5"
                >
                  {{ __('Say hello to {0}.').format(chat.person.full_name) }}
                </p>

                <section v-for="group in groups" :key="group.label">
                  <p class="my-3 text-center text-xs font-medium text-ink-gray-5">{{ group.label }}</p>

                  <div v-for="row in group.rows" :key="row.name" class="mb-1.5">
                    <div
                      v-if="row.kind === 'Call'"
                      class="flex items-center justify-center gap-1.5 py-1 text-xs text-ink-gray-5"
                    >
                      <span
                        :class="row.content === 'Completed' ? 'lucide-phone' : 'lucide-phone-missed'"
                        class="size-3.5"
                        aria-hidden="true"
                      />
                      {{ callLine(row) }} · {{ time(row.creation) }}
                    </div>

                    <div v-else class="flex" :class="mine(row) ? 'justify-end' : 'justify-start'">
                      <div
                        class="max-w-[80%] rounded-3 px-3 py-1.5"
                        :class="
                          mine(row)
                            ? 'bg-surface-gray-3 text-ink-gray-9'
                            : 'border border-outline-gray-2 bg-surface-base text-ink-gray-9'
                        "
                      >
                        <p class="whitespace-pre-wrap break-words text-base">{{ row.content }}</p>
                        <p class="mt-0.5 flex items-center justify-end gap-1.5 text-xs text-ink-gray-5">
                          <button
                            v-if="row.sop"
                            type="button"
                            class="truncate underline-offset-2 hover:underline"
                            @click="visit(row.sop)"
                          >
                            {{ row.sop }}
                          </button>
                          <span>{{ time(row.creation) }}</span>
                          <span
                            v-if="mine(row)"
                            :class="row.read ? 'lucide-check-check text-ink-green-3' : 'lucide-check'"
                            class="size-3.5"
                            :aria-label="row.read ? __('Seen') : __('Sent')"
                          />
                        </p>
                      </div>
                    </div>
                  </div>
                </section>
              </template>
            </div>

            <div class="border-t border-outline-gray-1 p-3">
              <ErrorMessage :message="chat.error" class="mb-2" />

              <p v-if="chat.sop" class="mb-1.5 flex items-center gap-1.5 text-xs text-ink-gray-5">
                <span class="lucide-file-text size-3.5" aria-hidden="true" />
                {{ __('About {0}').format(chat.sop) }}
                <button type="button" class="hover:text-ink-gray-8" :aria-label="__('Remove')" @click="chat.sop = null">
                  <span class="lucide-x size-3" aria-hidden="true" />
                </button>
              </p>

              <div class="flex items-end gap-2">
                <textarea
                  ref="box"
                  v-model="draft"
                  rows="1"
                  :placeholder="__('Write a message')"
                  class="max-h-32 min-h-[2.25rem] flex-1 resize-none rounded-2 border border-outline-gray-2 bg-surface-gray-1 px-2.5 py-1.5 text-base text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:ring-0"
                  @keydown.enter.exact.prevent="send"
                  @input="grow"
                />
                <Button
                  variant="solid"
                  icon="lucide-send-horizontal"
                  :label="__('Send')"
                  :loading="chat.sending"
                  :disabled="!draft.trim()"
                  @click="send"
                />
              </div>
            </div>
          </template>
        </aside>
      </Transition>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Badge,
  Button,
  ErrorMessage,
  Skeleton,
  TextInput,
  Tooltip,
  createResource,
  debounce,
} from 'frappe-ui'
import { startCall } from '@/data/call'
import { chat, loadEarlier, openChat, openMail, sendMessage, showInbox, threads } from '@/data/chat'
import { session } from '@/data/session'
import { translate as __ } from '@/translation'
import { dayLabel, shortDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const query = ref('')
const draft = ref('')
const scroller = ref(null)
const box = ref(null)
const earlier = ref(false)
const more = ref(false)

const people = createResource({ url: 'sop.api.chat.people' })

const search = debounce((value) => people.submit({ query: value }), 250)

watch(query, (value) => {
  if (value.trim()) search(value.trim())
})

watch(
  () => route.fullPath,
  () => (chat.open = false),
)

watch(
  () => chat.open,
  (open) => {
    if (open && !chat.person) threads.reload()
    if (!open) query.value = ''
  },
)

watch(
  () => chat.person?.name,
  () => {
    draft.value = ''
    more.value = false
  },
)

watch(
  () => chat.loading,
  (loading) => {
    if (!loading) more.value = chat.messages.length >= 50
  },
)

watch(
  () => chat.messages.length,
  () => {
    if (!earlier.value) nextTick(toBottom)
  },
)

const groups = computed(() => {
  const out = []

  for (const row of chat.messages) {
    const label = dayLabel(row.creation)
    const last = out[out.length - 1]

    if (last && last.label === label) last.rows.push(row)
    else out.push({ label, rows: [row] })
  }

  return out
})

function toBottom() {
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
}

function grow() {
  const el = box.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}

function mine(row) {
  return row.sender === session.user.name
}

function time(value) {
  return new Date(value.replace(' ', 'T')).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function when(value) {
  return dayLabel(value) === __('Today') ? time(value) : shortDate(value)
}

function duration(seconds) {
  const minutes = Math.floor(seconds / 60)
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
}

function callLine(row) {
  const outgoing = mine(row)

  if (row.content === 'Completed') {
    return `${outgoing ? __('Outgoing call') : __('Incoming call')} · ${duration(row.duration)}`
  }
  if (row.content === 'Declined') return outgoing ? __('Call declined') : __('You declined a call')
  return outgoing ? __('No answer') : __('Missed call')
}

function preview(row) {
  if (row.kind === 'Call') return callLine(row)
  return mine(row) ? `${__('You')}: ${row.content}` : row.content
}

function pick(person) {
  query.value = ''
  openChat(person)
}

async function send() {
  const text = draft.value
  if (!text.trim() || chat.sending) return

  draft.value = ''
  nextTick(grow)

  if (!(await sendMessage(text))) draft.value = text
}

async function showEarlier() {
  const el = scroller.value
  const height = el?.scrollHeight || 0

  earlier.value = true
  try {
    const count = await loadEarlier()
    more.value = count >= 50
    await nextTick()
    if (el) el.scrollTop = el.scrollHeight - height
  } finally {
    earlier.value = false
  }
}

function visit(sop) {
  chat.open = false
  router.push(`/${sop}`)
}
</script>
