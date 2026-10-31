<template>
  <HoverCard :hover-delay="300" :leave-delay="200" @update:open="(value) => value && load()">
    <template #trigger>
      <slot />
    </template>

    <div class="w-80 p-3">
      <div v-if="card.loading && !info" class="flex flex-col gap-2">
        <Skeleton class="h-4 w-2/3" />
        <Skeleton class="h-3 w-1/2" />
        <Skeleton class="h-3 w-3/4" />
      </div>
      <p v-else-if="!info || info.missing" class="text-sm text-ink-gray-5">{{ __('This record no longer exists.') }}</p>
      <p v-else-if="info.blocked" class="text-sm text-ink-gray-5">{{ __('You are not allowed to see this record.') }}</p>
      <RecordCardBody v-else :info="info" />
    </div>
  </HoverCard>
</template>

<script setup>
import { computed, watch } from 'vue'
import { HoverCard, Skeleton, createResource } from 'frappe-ui'
import RecordCardBody from './RecordCardBody.vue'
import { translate as __ } from '@/translation'

const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, required: true },
})

const card = createResource({
  url: 'sop.api.mentions.card',
  makeParams: () => ({ doctype: props.doctype, name: props.name }),
})

const info = computed(() => card.data || null)

function load() {
  if (!card.data && !card.loading) card.fetch()
}

watch(
  () => [props.doctype, props.name],
  () => card.reset(),
)
</script>
