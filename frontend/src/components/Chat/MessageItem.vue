<template>
  <div
    v-if="message.kind === 'Call'"
    class="flex items-center justify-center gap-1.5 py-1 text-xs text-ink-gray-5"
  >
    <span
      :class="message.content === 'Completed' ? 'lucide-phone' : 'lucide-phone-missed'"
      class="size-3.5"
      aria-hidden="true"
    />
    {{ callLine }} · {{ time }}
  </div>

  <div v-else-if="message.kind === 'Email'" class="flex justify-center py-1">
    <div
      class="flex max-w-[90%] items-center gap-2 rounded-3 border border-outline-gray-1 bg-surface-gray-1 px-3 py-1.5 text-xs text-ink-gray-6"
    >
      <span class="lucide-mail size-3.5 shrink-0 text-ink-gray-5" aria-hidden="true" />
      <span class="min-w-0">
        <span class="text-ink-gray-8">{{ emailLine }}</span>
        <span class="block truncate italic">“{{ message.content }}”</span>
      </span>
      <span class="shrink-0 text-ink-gray-5">{{ time }}</span>
    </div>
  </div>

  <div v-else class="flex items-end gap-2" :class="mine ? 'justify-end' : 'justify-start'">
    <div v-if="group && !mine" class="w-7 shrink-0">
      <Avatar v-if="first" :image="sender?.image" :label="sender?.full_name" size="md" shape="circle" />
    </div>

    <div class="flex min-w-0 max-w-[80%] flex-col" :class="mine ? 'items-end' : 'items-start'">
      <p v-if="group && !mine && first" class="mb-0.5 px-1 text-xs font-medium text-ink-gray-6">
        {{ sender?.full_name || message.sender }}
      </p>

      <a
        v-if="message.kind === 'File' && message.is_image"
        :href="url"
        target="_blank"
        rel="noopener"
        class="block overflow-hidden rounded-3 border border-outline-gray-2"
      >
        <img
          :src="url"
          :alt="message.file_name"
          loading="lazy"
          class="max-h-64 w-auto max-w-full object-cover"
          @load="$emit('loaded')"
        />
      </a>

      <a
        v-else-if="message.kind === 'File'"
        :href="url"
        class="flex w-64 max-w-full items-center gap-2.5 rounded-3 border border-outline-gray-2 bg-surface-base px-3 py-2 hover:bg-surface-gray-1"
      >
        <span class="grid size-9 shrink-0 place-content-center rounded-2 bg-surface-gray-2" aria-hidden="true">
          <span class="lucide-file size-4 text-ink-gray-6" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="block truncate text-sm font-medium text-ink-gray-8">{{ message.file_name }}</span>
          <span class="block text-xs text-ink-gray-5">{{ size }}</span>
        </span>
        <span class="lucide-download size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
      </a>

      <div
        v-if="message.kind === 'Text' || (message.kind === 'File' && message.content)"
        class="rounded-3 px-3 py-1.5"
        :class="[
          mine ? 'bg-surface-gray-3 text-ink-gray-9' : 'border border-outline-gray-2 bg-surface-base text-ink-gray-9',
          message.kind === 'File' ? 'mt-1' : '',
        ]"
      >
        <p class="whitespace-pre-wrap break-words text-base">{{ message.content }}</p>
      </div>

      <p class="mt-0.5 flex items-center gap-1.5 px-1 text-xs text-ink-gray-5">
        <button
          v-if="message.sop && !group"
          type="button"
          class="truncate underline-offset-2 hover:underline"
          @click="$emit('visit', message.sop)"
        >
          {{ message.sop }}
        </button>
        <span>{{ time }}</span>
        <span
          v-if="mine && !group"
          :class="message.read ? 'lucide-check-check text-ink-green-3' : 'lucide-check'"
          class="size-3.5"
          :aria-label="message.read ? __('Seen') : __('Sent')"
        />
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Avatar } from 'frappe-ui'
import { attachmentUrl } from '@/data/chat'
import { session } from '@/data/session'
import { translate as __ } from '@/translation'

const props = defineProps({
  message: { type: Object, required: true },
  mine: { type: Boolean, default: false },
  group: { type: Boolean, default: false },
  first: { type: Boolean, default: true },
  sender: { type: Object, default: null },
})

defineEmits(['visit', 'loaded'])

const url = computed(() => attachmentUrl(props.message))

const time = computed(() =>
  new Date(props.message.creation.replace(' ', 'T')).toLocaleTimeString([], {
    hour: 'numeric',
    minute: '2-digit',
  }),
)

const size = computed(() => {
  const bytes = props.message.file_size || 0
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
})

const callLine = computed(() => {
  const { content, duration } = props.message
  const minutes = Math.floor(duration / 60)
  const length = `${minutes}:${String(duration % 60).padStart(2, '0')}`

  if (content === 'Completed') {
    return `${props.mine ? __('Outgoing call') : __('Incoming call')} · ${length}`
  }
  if (content === 'Declined') return props.mine ? __('Call declined') : __('You declined a call')
  return props.mine ? __('No answer') : __('Missed call')
})

const emailLine = computed(() => {
  const to = props.message.email_to || __('someone')
  if (props.mine) return __('You emailed {0}').format(to)
  if (props.message.recipient === session.user.name) {
    return __('{0} emailed you').format(props.sender?.full_name || props.message.sender)
  }
  return __('{0} emailed {1}').format(props.sender?.full_name || props.message.sender, to)
})
</script>
