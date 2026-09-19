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
          @dragover.prevent="dragging = inThread"
          @dragleave.self="dragging = false"
          @drop.prevent="drop"
        >
          <div class="flex items-center gap-2 border-b border-outline-gray-1 px-3 py-2.5">
            <template v-if="chat.room">
              <Button variant="ghost" icon="lucide-arrow-left" :label="__('All messages')" @click="showInbox" />
              <span class="grid size-8 shrink-0 place-content-center rounded-2 bg-surface-gray-2" aria-hidden="true">
                <span class="lucide-file-text size-4 text-ink-gray-6" />
              </span>
              <div class="min-w-0 flex-1">
                <p class="truncate text-base font-semibold text-ink-gray-9">{{ chat.room.sop_no }}</p>
                <button
                  type="button"
                  class="block max-w-full truncate text-xs text-ink-gray-5 hover:text-ink-gray-8"
                  @click="showMembers = !showMembers"
                >
                  {{ chat.room.title }} · {{ __('{0} members').format(chat.room.members.length) }}
                </button>
              </div>

              <Tooltip :text="__('Open the procedure')">
                <Button
                  variant="ghost"
                  icon="lucide-arrow-up-right"
                  :label="__('Open the procedure')"
                  @click="visit(chat.room.sop)"
                />
              </Tooltip>
            </template>

            <template v-else-if="chat.person">
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
                <Button variant="ghost" icon="lucide-mail" :label="__('Email')" @click="openMail(chat.person, chat.sop)" />
              </Tooltip>
            </template>

            <template v-else>
              <span class="flex flex-1 items-center gap-2 px-1">
                <span class="text-lg font-semibold text-ink-gray-9">{{ __('Messages') }}</span>
                <Tooltip :text="realtime.connected ? __('Live') : __('Live updates are offline')">
                  <span
                    class="size-2 rounded-full"
                    :class="realtime.connected ? 'bg-[color:var(--ink-green-3)]' : 'bg-surface-gray-4'"
                  />
                </Tooltip>
              </span>

              <Tooltip :text="sounds.on ? __('Mute sounds') : __('Turn sounds on')">
                <Button
                  variant="ghost"
                  :icon="sounds.on ? 'lucide-volume-2' : 'lucide-volume-x'"
                  :label="sounds.on ? __('Mute sounds') : __('Turn sounds on')"
                  @click="sounds.on = !sounds.on"
                />
              </Tooltip>
            </template>

            <Tooltip :text="__('Close')">
              <Button variant="ghost" icon="lucide-x" :label="__('Close')" @click="chat.open = false" />
            </Tooltip>
          </div>

          <div
            v-if="!realtime.connected && realtime.error"
            class="flex items-start gap-2 border-b border-outline-gray-1 bg-surface-gray-1 px-4 py-2 text-sm text-ink-gray-6"
          >
            <span class="lucide-wifi-off mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
            <span class="min-w-0">
              {{ __('Live updates are offline, so new messages and calls will not arrive until the connection is back.') }}
              <span class="mt-1 block break-all font-mono text-xs text-ink-gray-5">
                {{ realtime.error }} · {{ realtime.address }}
              </span>
            </span>
          </div>

          <div
            v-if="chat.room && showMembers"
            class="max-h-56 overflow-y-auto border-b border-outline-gray-1 bg-surface-gray-1 py-1.5"
          >
            <button
              v-for="member in chat.room.members"
              :key="member.name"
              type="button"
              class="flex w-full items-center gap-2.5 px-4 py-1.5 text-left hover:bg-surface-gray-2 disabled:cursor-default disabled:hover:bg-transparent"
              :disabled="member.name === session.user.name"
              @click="openChat(member, chat.room.sop)"
            >
              <Avatar :image="member.image" :label="member.full_name" size="md" shape="circle" />
              <span class="min-w-0 flex-1 truncate text-sm text-ink-gray-8">
                {{ member.full_name }}
                <span v-if="member.name === session.user.name" class="text-ink-gray-5">({{ __('you') }})</span>
              </span>
              <span
                v-if="member.name !== session.user.name"
                class="lucide-message-square size-3.5 text-ink-gray-5"
                aria-hidden="true"
              />
            </button>
          </div>

          <template v-if="!inThread">
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
                  :key="row.room ? `sop:${row.room.sop}` : row.person.name"
                  type="button"
                  class="flex w-full items-center gap-2.5 px-4 py-2.5 text-left hover:bg-surface-gray-2"
                  @click="row.room ? openRoom(row.room.sop) : pick(row.person)"
                >
                  <span
                    v-if="row.room"
                    class="grid size-8 shrink-0 place-content-center rounded-2 bg-surface-gray-2"
                    aria-hidden="true"
                  >
                    <span class="lucide-file-text size-4 text-ink-gray-6" />
                  </span>
                  <Avatar v-else :image="row.person.image" :label="row.person.full_name" size="lg" shape="circle" />

                  <span class="min-w-0 flex-1">
                    <span class="flex items-center gap-2">
                      <span
                        class="min-w-0 flex-1 truncate text-base"
                        :class="row.unread ? 'font-semibold text-ink-gray-9' : 'text-ink-gray-8'"
                      >
                        <template v-if="row.room">
                          {{ row.room.sop_no }}
                          <span class="font-normal text-ink-gray-5">· {{ row.room.title }}</span>
                        </template>
                        <template v-else>{{ row.person.full_name }}</template>
                      </span>
                      <span class="shrink-0 text-xs text-ink-gray-5">{{ when(row.last.creation) }}</span>
                    </span>
                    <span class="mt-0.5 flex items-center gap-2">
                      <span
                        class="min-w-0 flex-1 truncate text-sm"
                        :class="row.unread ? 'text-ink-gray-8' : 'text-ink-gray-5'"
                      >
                        {{ preview(row) }}
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
                <p class="mt-1 text-sm text-ink-gray-5">
                  {{ __('Find someone above, or open Discussion on a procedure.') }}
                </p>
              </div>
            </div>
          </template>

          <template v-else>
            <div ref="scroller" class="relative min-h-0 flex-1 overflow-y-auto px-4 py-3">
              <div v-if="chat.loading" class="flex flex-col gap-3">
                <Skeleton class="h-8 w-2/3 rounded-3" />
                <Skeleton class="ml-auto h-8 w-1/2 rounded-3" />
                <Skeleton class="h-8 w-3/5 rounded-3" />
              </div>

              <template v-else>
                <div v-if="more" class="mb-3 flex justify-center">
                  <Button variant="ghost" size="sm" :label="__('Show earlier')" :loading="earlier" @click="showEarlier" />
                </div>

                <p v-if="!chat.messages.length" class="px-6 pt-16 text-center text-sm text-ink-gray-5">
                  {{
                    chat.room
                      ? __('Start the discussion about {0}. Everyone involved in it will see this.').format(
                          chat.room.sop_no,
                        )
                      : __('Say hello to {0}.').format(chat.person.full_name)
                  }}
                </p>

                <section v-for="group in groups" :key="group.label">
                  <p class="my-3 text-center text-xs font-medium text-ink-gray-5">{{ group.label }}</p>

                  <MessageItem
                    v-for="row in group.rows"
                    :key="row.message.name"
                    class="mb-1.5"
                    :message="row.message"
                    :mine="row.message.sender === session.user.name"
                    :group="!!chat.room"
                    :first="row.first"
                    :sender="senderOf(row.message)"
                    @visit="visit"
                    @loaded="settle"
                  />
                </section>
              </template>

              <div
                v-if="dragging"
                class="pointer-events-none absolute inset-2 grid place-content-center rounded-3 border-2 border-dashed border-outline-gray-3 bg-surface-base text-center"
              >
                <span class="lucide-upload mx-auto size-6 text-ink-gray-5" aria-hidden="true" />
                <p class="mt-2 text-sm text-ink-gray-7">{{ __('Drop files to share them') }}</p>
              </div>
            </div>

            <div class="border-t border-outline-gray-1 px-3 pb-3 pt-2">
              <p class="mb-1 flex h-4 items-center gap-1.5 text-xs text-ink-gray-5" aria-live="polite">
                <template v-if="typers">
                  <span class="flex gap-0.5" aria-hidden="true">
                    <span class="size-1 animate-bounce rounded-full bg-surface-gray-4 [animation-delay:-0.3s]" />
                    <span class="size-1 animate-bounce rounded-full bg-surface-gray-4 [animation-delay:-0.15s]" />
                    <span class="size-1 animate-bounce rounded-full bg-surface-gray-4" />
                  </span>
                  {{ typers }}
                </template>
              </p>

              <ErrorMessage :message="chat.error" class="mb-2" />

              <p v-if="chat.person && chat.sop" class="mb-1.5 flex items-center gap-1.5 text-xs text-ink-gray-5">
                <span class="lucide-file-text size-3.5" aria-hidden="true" />
                {{ __('About {0}').format(chat.sop) }}
                <button type="button" class="hover:text-ink-gray-8" :aria-label="__('Remove')" @click="chat.sop = null">
                  <span class="lucide-x size-3" aria-hidden="true" />
                </button>
              </p>

              <div v-if="uploads.length" class="mb-2 flex flex-wrap gap-1.5">
                <span
                  v-for="name in uploads"
                  :key="name"
                  class="inline-flex max-w-full items-center gap-1.5 rounded-2 bg-surface-gray-2 px-2 py-1 text-xs text-ink-gray-7"
                >
                  <span class="lucide-loader-circle size-3.5 shrink-0 animate-spin" aria-hidden="true" />
                  <span class="truncate">{{ name }}</span>
                </span>
              </div>

              <div class="flex items-end gap-2">
                <Tooltip :text="__('Share a file or image')">
                  <Button
                    variant="ghost"
                    icon="lucide-paperclip"
                    :label="__('Share a file or image')"
                    @click="picker?.click()"
                  />
                </Tooltip>

                <textarea
                  ref="box"
                  v-model="draft"
                  rows="1"
                  :placeholder="chat.room ? __('Message everyone on {0}').format(chat.room.sop_no) : __('Write a message')"
                  class="max-h-32 min-h-[2.25rem] flex-1 resize-none rounded-2 border border-outline-gray-2 bg-surface-gray-1 px-2.5 py-1.5 text-base text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:ring-0"
                  @keydown.enter.exact.prevent="send"
                  @input="typed"
                  @paste="paste"
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

              <input ref="picker" type="file" multiple class="hidden" @change="choose" />
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
  useFileUpload,
} from 'frappe-ui'
import MessageItem from '@/components/Chat/MessageItem.vue'
import { startCall } from '@/data/call'
import {
  announceTyping,
  chat,
  currentKey,
  loadEarlier,
  openChat,
  openMail,
  openRoom,
  sendMessage,
  showInbox,
  threads,
  typing,
} from '@/data/chat'
import { session } from '@/data/session'
import { realtime } from '@/data/socket'
import { sounds } from '@/data/sound'
import { translate as __ } from '@/translation'
import { dayLabel, shortDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const fileUpload = useFileUpload()

const query = ref('')
const draft = ref('')
const scroller = ref(null)
const box = ref(null)
const picker = ref(null)
const earlier = ref(false)
const more = ref(false)
const showMembers = ref(false)
const dragging = ref(false)
const uploads = ref([])

const people = createResource({ url: 'sop.api.chat.people' })

const search = debounce((value) => people.submit({ query: value }), 250)

const inThread = computed(() => !!(chat.room || chat.person))

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
    if (open && !inThread.value) threads.reload()
    if (!open) query.value = ''
  },
)

watch(currentKey, () => {
  draft.value = ''
  more.value = false
  showMembers.value = false
  dragging.value = false
})

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

const members = computed(() => {
  const out = {}
  for (const member of chat.room?.members || []) out[member.name] = member
  return out
})

const groups = computed(() => {
  const out = []
  let previous = null

  for (const message of chat.messages) {
    const label = dayLabel(message.creation)
    let last = out[out.length - 1]

    if (!last || last.label !== label) {
      last = { label, rows: [] }
      out.push(last)
      previous = null
    }

    const first = !previous || previous.sender !== message.sender || previous.kind === 'Email' || previous.kind === 'Call'
    last.rows.push({ message, first })
    previous = message
  }

  return out
})

const typers = computed(() => {
  const names = Object.values(typing[currentKey()] || {})
  if (!names.length) return ''
  if (names.length === 1) return __('{0} is typing…').format(names[0])
  if (names.length === 2) return __('{0} and {1} are typing…').format(names[0], names[1])
  return __('Several people are typing…')
})

function senderOf(message) {
  if (message.sender === session.user.name) return session.user
  if (chat.room) return members.value[message.sender] || { full_name: message.sender_name || message.sender }
  return chat.person
}

function toBottom() {
  if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
}

function settle() {
  const el = scroller.value
  if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 400) toBottom()
}

function grow() {
  const el = box.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}

function typed() {
  grow()
  if (draft.value.trim()) announceTyping()
}

function when(value) {
  const time = new Date(value.replace(' ', 'T')).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
  return dayLabel(value) === __('Today') ? time : shortDate(value)
}

function describe(message) {
  if (message.kind === 'Call') return message.content === 'Completed' ? __('Call') : __('Missed call')
  if (message.kind === 'Email') return __('Email: {0}').format(message.content)
  if (message.kind === 'File') return message.content || (message.is_image ? __('Photo') : message.file_name)
  return message.content
}

function preview(row) {
  const message = row.last
  const mine = message.sender === session.user.name
  const text = describe(message)

  if (mine) return `${__('You')}: ${text}`
  if (row.room) return `${message.sender_name || message.sender}: ${text}`
  return text
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

async function share(files) {
  for (const file of files) {
    uploads.value = [...uploads.value, file.name]

    try {
      const saved = await fileUpload.upload(file, { private: true, folder: 'Home/Attachments' })
      await sendMessage('', saved.name)
    } catch (failure) {
      chat.error = failure.messages?.[0] || failure.message || __('Could not share {0}').format(file.name)
    } finally {
      uploads.value = uploads.value.filter((name) => name !== file.name)
    }
  }
}

function choose(event) {
  const files = Array.from(event.target.files || [])
  event.target.value = ''
  if (files.length) share(files)
}

function paste(event) {
  const files = Array.from(event.clipboardData?.files || [])
  if (!files.length) return
  event.preventDefault()
  share(files)
}

function drop(event) {
  dragging.value = false
  if (!inThread.value) return
  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length) share(files)
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
