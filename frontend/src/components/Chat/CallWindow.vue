<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-150 ease-out"
      leave-active-class="transition duration-150 ease-in"
      enter-from-class="translate-y-2 opacity-0"
      leave-to-class="translate-y-2 opacity-0"
    >
      <div
        v-if="phone.state !== 'idle'"
        class="fixed bottom-4 right-4 z-50 w-[calc(100%-2rem)] rounded-3 border border-outline-gray-2 bg-surface-base p-4 shadow-2xl sm:w-80"
        role="dialog"
        :aria-label="__('Call')"
      >
        <div class="flex items-center gap-3">
          <span class="relative">
            <Avatar
              :image="phone.person?.image"
              :label="phone.person?.full_name"
              size="2xl"
              shape="circle"
            />
            <span
              v-if="phone.state === 'ringing' || phone.state === 'calling'"
              class="absolute inset-0 animate-ping rounded-full border-2 border-outline-green-2"
              aria-hidden="true"
            />
          </span>

          <div class="min-w-0 flex-1">
            <p class="truncate text-base font-semibold text-ink-gray-9">
              {{ phone.person?.full_name }}
            </p>
            <p class="mt-0.5 text-sm tabular-nums" :class="toneClass">{{ status }}</p>
          </div>
        </div>

        <div class="mt-4 flex items-center justify-end gap-2">
          <template v-if="phone.state === 'ringing'">
            <Button
              variant="subtle"
              theme="red"
              icon-left="lucide-phone-off"
              :label="__('Decline')"
              @click="decline"
            />
            <Button
              variant="solid"
              theme="green"
              icon-left="lucide-phone"
              :label="__('Answer')"
              @click="answer"
            />
          </template>

          <template v-else-if="phone.state !== 'ended'">
            <Button
              variant="subtle"
              :icon="phone.muted ? 'lucide-mic-off' : 'lucide-mic'"
              :label="phone.muted ? __('Unmute') : __('Mute')"
              :disabled="phone.state === 'calling'"
              @click="toggleMute"
            />
            <Button
              variant="subtle"
              icon="lucide-message-square"
              :label="__('Open chat')"
              @click="openChat(phone.person, phone.sop)"
            />
            <Button
              variant="solid"
              theme="red"
              icon-left="lucide-phone-off"
              :label="phone.state === 'calling' ? __('Cancel') : __('Hang up')"
              @click="hangUp()"
            />
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Avatar, Button } from 'frappe-ui'
import { answer, decline, hangUp, phone, toggleMute } from '@/data/call'
import { openChat } from '@/data/chat'
import { translate as __ } from '@/translation'

const now = ref(Date.now())
let timer = null

watch(
  () => phone.state,
  (state) => {
    clearInterval(timer)
    if (state === 'live') timer = setInterval(() => (now.value = Date.now()), 1000)
  },
)

onBeforeUnmount(() => clearInterval(timer))

function clock(ms) {
  const total = Math.max(0, Math.floor(ms / 1000))
  const minutes = Math.floor(total / 60)
  const seconds = String(total % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}

const status = computed(() => {
  if (phone.state === 'ringing') return __('Incoming call…')
  if (phone.state === 'calling') return __('Ringing…')
  if (phone.state === 'connecting') return __('Connecting…')
  if (phone.state === 'live') return clock(now.value - phone.startedAt)
  return phone.note
})

const toneClass = computed(() => {
  if (phone.state === 'live') return 'text-ink-green-3'
  if (phone.state === 'ended') return 'text-ink-gray-5'
  return 'text-ink-gray-6'
})
</script>
