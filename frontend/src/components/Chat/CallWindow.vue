<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-150 ease-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="phone.state === 'ringing'"
        class="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4 backdrop-blur-sm"
        role="alertdialog"
        :aria-label="__('Incoming call from {0}').format(phone.person?.full_name)"
      >
        <div class="w-full max-w-xs rounded-3 bg-surface-base px-6 pb-6 pt-5 text-center shadow-2xl">
          <p class="flex items-center justify-center gap-1.5 text-sm font-medium text-ink-gray-5">
            <span class="size-2 animate-pulse rounded-full bg-[color:var(--ink-green-3)]" />
            {{ __('Incoming voice call') }}
          </p>

          <div class="relative mx-auto mt-6 grid size-24 place-items-center">
            <span class="absolute inset-0 animate-ping rounded-full bg-surface-gray-2" aria-hidden="true" />
            <span class="absolute -inset-2 rounded-full border border-outline-gray-2" aria-hidden="true" />
            <Avatar
              :image="phone.person?.image"
              :label="phone.person?.full_name"
              size="3xl"
              shape="circle"
              class="relative !size-24"
            />
          </div>

          <p class="mt-5 truncate text-xl font-semibold text-ink-gray-9">{{ phone.person?.full_name }}</p>
          <p class="mt-1 truncate text-sm text-ink-gray-5">
            {{ phone.sop ? __('About {0}').format(phone.sop) : phone.person?.name }}
          </p>

          <div class="mt-8 flex items-start justify-center gap-12">
            <div class="flex flex-col items-center gap-2">
              <Button
                size="2xl"
                variant="solid"
                theme="red"
                icon="lucide-phone-off"
                :label="__('Decline')"
                class="!size-14 !rounded-full"
                @click="decline"
              />
              <span class="text-sm text-ink-gray-6">{{ __('Decline') }}</span>
            </div>

            <div class="flex flex-col items-center gap-2">
              <Button
                size="2xl"
                variant="solid"
                theme="green"
                icon="lucide-phone"
                :label="__('Accept')"
                class="!size-14 !rounded-full"
                @click="answer"
              />
              <span class="text-sm text-ink-gray-6">{{ __('Accept') }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <Transition
      enter-active-class="transition duration-200 ease-out"
      leave-active-class="transition duration-150 ease-in"
      enter-from-class="translate-y-3 opacity-0"
      leave-to-class="translate-y-3 opacity-0"
    >
      <div
        v-if="docked"
        class="fixed bottom-4 right-4 z-50 w-[calc(100%-2rem)] overflow-hidden rounded-3 border border-outline-gray-2 bg-surface-base shadow-2xl sm:w-[19rem]"
        role="dialog"
        :aria-label="__('Call with {0}').format(phone.person?.full_name)"
      >
        <div class="flex items-center gap-3 px-3.5 pb-3 pt-3.5">
          <span class="relative shrink-0">
            <Avatar :image="phone.person?.image" :label="phone.person?.full_name" size="xl" shape="circle" />
            <span
              class="absolute -bottom-0.5 -right-0.5 size-3 rounded-full border-2 border-[color:var(--surface-base,var(--surface-white))]"
              :class="phone.state === 'live' ? 'bg-[color:var(--ink-green-3)]' : 'bg-surface-gray-4'"
              aria-hidden="true"
            />
          </span>

          <div class="min-w-0 flex-1">
            <p class="truncate text-base font-semibold text-ink-gray-9">{{ phone.person?.full_name }}</p>
            <p class="mt-0.5 flex items-center gap-1.5 text-sm tabular-nums" :class="toneClass">
              <span
                v-if="phone.state === 'calling' || phone.state === 'connecting'"
                class="lucide-loader-circle size-3.5 animate-spin"
                aria-hidden="true"
              />
              <span v-else-if="phone.muted" class="lucide-mic-off size-3.5" aria-hidden="true" />
              {{ status }}
            </p>
          </div>
        </div>

        <div
          v-if="phone.state !== 'ended'"
          class="flex items-center justify-between gap-2 border-t border-outline-gray-1 bg-surface-gray-1 px-3.5 py-2.5"
        >
          <div class="flex items-center gap-1.5">
            <Tooltip :text="phone.muted ? __('Unmute') : __('Mute')">
              <Button
                :variant="phone.muted ? 'solid' : 'subtle'"
                :icon="phone.muted ? 'lucide-mic-off' : 'lucide-mic'"
                :label="phone.muted ? __('Unmute') : __('Mute')"
                :disabled="phone.state !== 'live'"
                class="!rounded-full"
                @click="toggleMute"
              />
            </Tooltip>
            <Tooltip :text="__('Open chat')">
              <Button
                variant="subtle"
                icon="lucide-message-square"
                :label="__('Open chat')"
                class="!rounded-full"
                @click="openChat(phone.person, phone.sop)"
              />
            </Tooltip>
          </div>

          <Button
            variant="solid"
            theme="red"
            icon-left="lucide-phone-off"
            :label="phone.state === 'calling' ? __('Cancel') : __('End call')"
            class="!rounded-full"
            @click="hangUp()"
          />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Avatar, Button, Tooltip } from 'frappe-ui'
import { answer, decline, hangUp, phone, toggleMute } from '@/data/call'
import { openChat } from '@/data/chat'
import { translate as __ } from '@/translation'

const now = ref(Date.now())
let timer = null

const docked = computed(() => phone.state !== 'idle' && phone.state !== 'ringing')

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
  if (phone.state === 'calling') return __('Ringing…')
  if (phone.state === 'connecting') return __('Connecting…')
  if (phone.state === 'live') return clock(now.value - phone.startedAt)
  return phone.note
})

const toneClass = computed(() => {
  if (phone.state === 'live') return 'text-ink-green-3'
  if (phone.state === 'ended') return 'text-ink-red-3'
  return 'text-ink-gray-5'
})
</script>
