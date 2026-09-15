<template>
  <Dialog
    v-model:open="open"
    :title="mode === 'send' ? __('Send for review') : __('Reviewers')"
    size="sm"
  >
    <template #default>
      <div class="flex flex-col gap-3">
        <p class="text-base text-ink-gray-7">
          {{
            mode === 'send'
              ? __(
                  'These people review and approve it. They come from the space’s team, so nobody approves their own work.',
                )
              : __('Who reviews this revision, and where each of them stands.')
          }}
        </p>

        <p v-if="mode === 'send' && route.loading" class="text-sm text-ink-gray-5">
          {{ __('Working out who reviews it…') }}
        </p>

        <ul
          v-else-if="people.length"
          class="flex flex-col divide-y divide-outline-gray-1 rounded-4 border border-outline-gray-2"
        >
          <li v-for="row in people" :key="row.approver" class="flex items-center gap-2.5 px-3 py-2">
            <Avatar :image="row.approver_image" :label="row.approver_name" size="sm" />
            <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
              {{ row.approver_name || row.approver }}
            </span>
            <Badge variant="subtle" size="sm">{{ __(row.approval_role) }}</Badge>
            <Badge v-if="row.decision" :theme="TONE[row.decision]" variant="subtle" size="sm">
              {{ __(row.decision) }}
            </Badge>
          </li>
        </ul>

        <p v-else class="text-base text-ink-gray-7">
          {{
            __(
              'Nobody can review this yet. Add a Reviewer or Approver to this space’s team, or give someone the SOP Approver role.',
            )
          }}
        </p>

        <ErrorMessage :message="error || route.error?.messages?.[0]" />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="mode === 'send' ? __('Cancel') : __('Close')" @click="open = false" />
        <Button
          v-if="mode === 'send'"
          variant="solid"
          icon-left="lucide-send"
          :label="__('Send for review')"
          :loading="loading"
          :disabled="route.loading || !people.length"
          @click="emit('send')"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, watch } from 'vue'
import { Avatar, Badge, Button, Dialog, ErrorMessage, createResource } from 'frappe-ui'

const props = defineProps({
  mode: { type: String, default: 'view' },
  sop: { type: String, default: '' },
  current: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const open = defineModel('open', { type: Boolean, default: false })
const emit = defineEmits(['send'])

const TONE = { Pending: 'gray', Approved: 'green', Rejected: 'red' }

const route = createResource({ url: 'sop.api.lifecycle.route' })

const people = computed(() => (props.mode === 'send' ? route.data || [] : props.current))

watch(open, (value) => {
  if (value && props.mode === 'send' && props.sop) route.submit({ sop: props.sop })
})
</script>
