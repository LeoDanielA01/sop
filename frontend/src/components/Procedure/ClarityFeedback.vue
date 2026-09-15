<template>
  <section class="mt-10 rounded-4 border border-outline-gray-2 px-4 py-3">
    <div class="flex flex-wrap items-center gap-3">
      <p class="text-base font-medium text-ink-gray-8">{{ __('Was this procedure clear?') }}</p>

      <div class="flex items-center gap-1.5">
        <Button
          :variant="mine && mine.clear ? 'solid' : 'subtle'"
          icon-left="lucide-thumbs-up"
          :label="__('Clear')"
          :disabled="send.loading"
          @click="choose(1)"
        />
        <Button
          :variant="mine && !mine.clear ? 'solid' : 'subtle'"
          icon-left="lucide-thumbs-down"
          :label="__('Not really')"
          :disabled="send.loading"
          @click="choose(0)"
        />
      </div>

      <span v-if="mine && !asking" class="text-sm text-ink-gray-5">
        {{ mine.clear ? __('Thanks, noted.') : __('Thanks. The author will see your note.') }}
      </span>

      <span v-if="info?.can_see_notes && info.total" class="ml-auto text-sm text-ink-gray-5">
        {{ __('{0}% clear · {1} votes').format(info.percent, info.total) }}
      </span>
    </div>

    <div v-if="asking" class="mt-3 flex flex-col gap-2">
      <FormControl
        type="textarea"
        :placeholder="__('What was unclear? A step, a word, a missing detail…')"
        v-model="note"
      />
      <div class="flex justify-end gap-2">
        <Button variant="ghost" :label="__('Skip')" @click="asking = false" />
        <Button
          variant="solid"
          :label="__('Send')"
          :loading="send.loading"
          :disabled="!note.trim()"
          @click="submit"
        />
      </div>
    </div>

    <div v-if="info?.notes?.length" class="mt-4 border-t border-outline-gray-1 pt-3">
      <p class="mb-2 text-sm text-ink-gray-5">{{ __('What readers found unclear') }}</p>
      <ul class="flex flex-col gap-2">
        <li
          v-for="(row, index) in info.notes"
          :key="index"
          class="rounded-4 bg-surface-gray-1 px-3 py-2"
        >
          <p class="whitespace-pre-line text-base text-ink-gray-8">{{ row.note }}</p>
          <p class="mt-0.5 text-sm text-ink-gray-5">{{ row.who }} · {{ row.when }}</p>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, FormControl, createResource } from 'frappe-ui'

const props = defineProps({
  sop: { type: String, required: true },
  version: { type: Number, default: null },
})

const emit = defineEmits(['summary'])

const info = ref(null)
const note = ref('')
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
