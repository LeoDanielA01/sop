<template>
  <section class="mt-6 flex flex-wrap items-center gap-x-3 gap-y-1.5 rounded-3 border border-outline-gray-2 px-3 py-1.5">

    <span class="text-xs text-ink-gray-5 shrink-0">{{ __('Was this clear?') }}</span>

    <div class="flex items-center gap-1 shrink-0">
      <button type="button" class="vote-btn" :class="mine?.clear ? 'vote-btn--yes' : ''" :disabled="send.loading" @click="choose(1)">
        <span class="lucide-thumbs-up" aria-hidden="true" />{{ __('Yes') }}
      </button>
      <button type="button" class="vote-btn" :class="mine && !mine.clear ? 'vote-btn--no' : ''" :disabled="send.loading" @click="choose(0)">
        <span class="lucide-thumbs-down" aria-hidden="true" />{{ __('No') }}
      </button>
    </div>

    <div v-if="asking" class="flex flex-1 items-center gap-1.5 min-w-40">
      <input
        v-model="note"
        type="text"
        class="note-input"
        :placeholder="__('What was unclear?')"
        @keydown.enter="submit"
        @keydown.esc="asking = false"
        autofocus
      />
      <button type="button" class="action-btn action-btn--send" :disabled="!note.trim() || send.loading" @click="submit">
        {{ __('Send') }}
      </button>
      <button type="button" class="action-btn" @click="asking = false">
        {{ __('Skip') }}
      </button>
    </div>

    <span v-else-if="mine" class="text-xs text-ink-gray-4">
      {{ mine.clear ? '✓' : __('Noted') }}
    </span>

    <span v-if="info?.can_see_notes && info.total" class="ml-auto text-xs text-ink-gray-4 tabular-nums shrink-0">
      {{ info.percent }}% · {{ info.total }}v
    </span>

    <div v-if="info?.notes?.length" class="w-full border-t border-outline-gray-1 mt-1 pt-1.5 space-y-1">
      <div v-for="(row, i) in info.notes" :key="i" class="flex items-baseline gap-2">
        <span class="text-xs text-ink-gray-7 flex-1 truncate">{{ row.note }}</span>
        <span class="text-xs text-ink-gray-4 shrink-0">{{ row.who }} · {{ row.when }}</span>
      </div>
    </div>

  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
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
  if (!note.value.trim()) return
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
  gap: 0.25rem;
  font-size: 0.7rem;
  font-weight: 500;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--outline-gray-2, #e5e7eb);
  background: transparent;
  color: var(--ink-gray-5, #6b7280);
  cursor: pointer;
  transition: background 0.1s, border-color 0.1s, color 0.1s;
  white-space: nowrap;
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
.vote-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.note-input {
  flex: 1;
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--outline-gray-2, #e5e7eb);
  background: var(--surface-base, transparent);
  color: var(--ink-gray-8, #1f2937);
  outline: none;
  min-width: 0;
}
.note-input:focus {
  border-color: var(--outline-gray-4, #9ca3af);
}
.action-btn {
  font-size: 0.7rem;
  font-weight: 500;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  color: var(--ink-gray-5, #6b7280);
  white-space: nowrap;
  transition: color 0.1s, background 0.1s;
}
.action-btn--send {
  background: var(--surface-gray-2, #f3f4f6);
  color: var(--ink-gray-8, #1f2937);
  border-color: var(--outline-gray-2, #e5e7eb);
}
.action-btn--send:disabled { opacity: 0.4; cursor: not-allowed; }
.action-btn:not(:disabled):hover { color: var(--ink-gray-8, #1f2937); }
</style>
