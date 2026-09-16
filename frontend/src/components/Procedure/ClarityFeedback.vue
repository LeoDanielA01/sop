<template>
  <section class="mt-6 rounded-3 border border-outline-gray-2 px-3 py-2">
    <div class="flex flex-wrap items-center gap-2">
      <p class="text-sm text-ink-gray-6 mr-1">{{ __('Was this clear?') }}</p>

      <button
        type="button"
        class="vote-btn"
        :class="mine && mine.clear ? 'vote-btn--yes' : ''"
        :disabled="send.loading"
        @click="choose(1)"
      >
        <span class="lucide-thumbs-up" aria-hidden="true" />
        {{ __('Yes') }}
      </button>

      <button
        type="button"
        class="vote-btn"
        :class="mine && !mine.clear ? 'vote-btn--no' : ''"
        :disabled="send.loading"
        @click="choose(0)"
      >
        <span class="lucide-thumbs-down" aria-hidden="true" />
        {{ __('No') }}
      </button>

      <span v-if="mine && !asking" class="text-xs text-ink-gray-4">
        {{ mine.clear ? __('Noted ✓') : __('Thanks, author notified.') }}
      </span>

      <span v-if="info?.can_see_notes && info.total" class="ml-auto text-xs text-ink-gray-4 tabular-nums">
        {{ info.percent }}% clear · {{ info.total }} votes
      </span>
    </div>

    <div v-if="asking" class="mt-2 flex items-end gap-2">
      <FormControl
        type="textarea"
        :placeholder="__('What was unclear?')"
        v-model="note"
        class="flex-1 text-sm"
        :rows="2"
      />
      <div class="flex flex-col gap-1.5 shrink-0">
        <Button variant="solid" size="sm" :label="__('Send')" :loading="send.loading" :disabled="!note.trim()" @click="submit" />
        <Button variant="ghost" size="sm" :label="__('Skip')" @click="asking = false" />
      </div>
    </div>

    <div v-if="info?.notes?.length" class="mt-2 border-t border-outline-gray-1 pt-2 space-y-1.5">
      <p class="text-xs text-ink-gray-4 mb-1">{{ __('Reader notes') }}</p>
      <div
        v-for="(row, i) in info.notes"
        :key="i"
        class="rounded-3 bg-surface-gray-1 px-2.5 py-1.5"
      >
        <p class="text-sm text-ink-gray-8 whitespace-pre-line">{{ row.note }}</p>
        <p class="mt-0.5 text-xs text-ink-gray-4">{{ row.who }} · {{ row.when }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, FormControl, createResource } from 'frappe-ui'
import { translate as __ } from '@/translation'

const props = defineProps({
  sop:     { type: String, required: true },
  version: { type: Number, default: null },
})

const emit = defineEmits(['summary'])

const info   = ref(null)
const note   = ref('')
const asking = ref(false)

const mine = computed(() => info.value?.mine || null)

function keep(data) {
  info.value = data
  emit('summary', data)
}

const load = createResource({
  url: 'sop.api.clarity.summary',
  makeParams: () => ({ sop: props.sop }),
  onSuccess: keep,
})

const send = createResource({ url: 'sop.api.clarity.vote', onSuccess: keep })

function choose(clear) {
  send.submit({ sop: props.sop, clear })
  asking.value = !clear
  note.value = clear ? '' : mine.value?.note || ''
}

function submit() {
  send.submit({ sop: props.sop, clear: 0, note: note.value })
  asking.value = false
}

watch(
  () => [props.sop, props.version],
  () => {
    asking.value = false
    load.submit({ sop: props.sop })
  },
  { immediate: true },
)
</script>

<style scoped>
.vote-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  border: 1px solid var(--outline-gray-2, #e5e7eb);
  background: transparent;
  color: var(--ink-gray-6, #4b5563);
  cursor: pointer;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.vote-btn:hover:not(:disabled) {
  background: var(--surface-gray-1, #f9fafb);
  border-color: var(--outline-gray-3, #d1d5db);
}
.vote-btn--yes {
  background: var(--surface-green-1, #f0fdf4);
  border-color: var(--outline-green-2, #86efac);
  color: var(--ink-green-3, #166534);
}
.vote-btn--no {
  background: var(--surface-red-1, #fff1f2);
  border-color: var(--outline-red-2, #fca5a5);
  color: var(--ink-red-3, #991b1b);
}
.vote-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
