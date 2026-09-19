<template>
  <Dialog v-model:open="open" :title="__('Quiz questions')" size="2xl">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-sm text-ink-gray-6">
          {{
            __('Trainees assigned the “Assessment” method answer these questions. Questions and answers are shuffled for each attempt, and marking is automatic.')
          }}
        </p>

        <div v-if="list.loading && !rows.length" class="flex flex-col gap-2">
          <Skeleton v-for="n in 3" :key="n" class="h-14 w-full rounded-3" />
        </div>

        <ErrorMessage v-else-if="list.error" :message="list.error.messages?.[0] || list.error.message" />

        <template v-else>
          <div v-if="rows.length && !draft" class="flex flex-col gap-1.5">
            <div
              v-for="(row, number) in rows"
              :key="row.name"
              class="flex items-start gap-3 rounded-3 border border-outline-gray-2 px-3 py-2.5"
              :class="row.enabled ? '' : 'opacity-60'"
            >
              <span class="mt-0.5 w-5 shrink-0 text-sm tabular-nums text-ink-gray-5">{{ number + 1 }}.</span>
              <div class="min-w-0 flex-1">
                <p class="text-base text-ink-gray-9">{{ row.question }}</p>
                <p class="mt-0.5 text-xs text-ink-gray-5">
                  {{ row.kind }} · {{ __('{0} answers, {1} correct').format(row.options.length, row.options.filter((o) => o.correct).length) }}
                  <template v-if="!row.enabled"> · {{ __('not in use') }}</template>
                </p>
              </div>
              <Button variant="ghost" size="sm" icon="lucide-pencil" :label="__('Edit')" @click="edit(row)" />
              <Button
                variant="ghost"
                size="sm"
                icon="lucide-trash-2"
                :label="__('Delete')"
                :loading="removing === row.name"
                @click="remove(row)"
              />
            </div>
          </div>

          <div
            v-else-if="!draft"
            class="flex flex-col items-center rounded-3 border border-dashed border-outline-gray-3 px-6 py-8 text-center"
          >
            <span class="lucide-clipboard-list size-6 text-ink-gray-5" aria-hidden="true" />
            <p class="mt-2 text-base font-medium text-ink-gray-7">{{ __('No questions yet') }}</p>
            <p class="mt-1 text-sm text-ink-gray-5">{{ __('Five to ten short questions about the steps that matter most work well.') }}</p>
          </div>

          <div v-if="draft" class="flex flex-col gap-3 rounded-3 border border-outline-gray-2 p-4">
            <FormControl v-model="draft.question" type="textarea" :label="__('Question')" :rows="2" />

            <div class="flex flex-wrap items-center gap-2">
              <span class="text-sm text-ink-gray-6">{{ __('Readers pick') }}</span>
              <TabButtons
                v-model="draft.kind"
                :options="[
                  { label: __('One answer'), value: 'One answer' },
                  { label: __('Several answers'), value: 'Several answers' },
                ]"
                @update:model-value="tidyKind"
              />
            </div>

            <div class="flex flex-col gap-1.5">
              <p class="text-sm text-ink-gray-6">
                {{ draft.kind === 'Several answers' ? __('Answers — tick every correct one') : __('Answers — tick the correct one') }}
              </p>
              <div v-for="(option, index) in draft.options" :key="index" class="flex items-center gap-2">
                <Tooltip :text="option.correct ? __('Correct') : __('Mark as correct')">
                  <button
                    type="button"
                    class="grid size-8 shrink-0 place-content-center rounded-2 border"
                    :class="option.correct ? 'border-outline-gray-4 bg-surface-gray-2' : 'border-outline-gray-2 hover:bg-surface-gray-1'"
                    :aria-pressed="!!option.correct"
                    :aria-label="__('Answer {0} is correct').format(index + 1)"
                    @click="mark(index)"
                  >
                    <span
                      :class="option.correct ? 'lucide-check text-ink-green-3' : 'lucide-minus text-ink-gray-4'"
                      class="size-4"
                      aria-hidden="true"
                    />
                  </button>
                </Tooltip>
                <TextInput v-model="option.option" class="flex-1" type="text" :placeholder="__('Answer {0}').format(index + 1)" />
                <Button
                  variant="ghost"
                  icon="lucide-x"
                  :label="__('Remove answer')"
                  :disabled="draft.options.length <= 2"
                  @click="draft.options.splice(index, 1)"
                />
              </div>
              <div>
                <Button
                  variant="ghost"
                  size="sm"
                  icon-left="lucide-plus"
                  :label="__('Add an answer')"
                  :disabled="draft.options.length >= 6"
                  @click="draft.options.push({ option: '', correct: 0 })"
                />
              </div>
            </div>

            <FormControl
              v-model="draft.explanation"
              type="textarea"
              :rows="2"
              :label="__('Explanation (optional)')"
              :placeholder="__('Shown to people who get this wrong, e.g. which step covers it')"
            />

            <FormControl v-model="draft.enabled" type="checkbox" :label="__('In use')" />

            <ErrorMessage :message="saveError" />

            <div class="flex justify-end gap-2">
              <Button :label="__('Cancel')" @click="draft = null" />
              <Button variant="solid" :label="__('Save question')" :loading="saving" @click="save" />
            </div>
          </div>
        </template>
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <span class="text-sm text-ink-gray-5">
          {{ __('{0} questions, {1} in use').format(rows.length, rows.filter((row) => row.enabled).length) }}
        </span>
        <Button
          v-if="!draft"
          variant="solid"
          icon-left="lucide-plus"
          :label="__('Add a question')"
          @click="edit(null)"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Skeleton,
  TabButtons,
  TextInput,
  Tooltip,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { translate as __ } from '@/translation'

const props = defineProps({
  sop: { type: String, default: '' },
})

const open = defineModel('open', { type: Boolean, default: false })

const draft = ref(null)
const saving = ref(false)
const saveError = ref(null)
const removing = ref(null)

const list = createResource({
  url: 'sop.api.quiz.questions',
  makeParams: () => ({ sop: props.sop }),
})

const rows = computed(() => list.data || [])

watch(open, (value) => {
  if (!value) return
  draft.value = null
  list.reload()
})

function edit(row) {
  saveError.value = null
  draft.value = row
    ? {
        name: row.name,
        question: row.question,
        kind: row.kind,
        explanation: row.explanation || '',
        enabled: !!row.enabled,
        options: row.options.map((option) => ({ ...option })),
      }
    : {
        name: null,
        question: '',
        kind: 'One answer',
        explanation: '',
        enabled: true,
        options: [
          { option: '', correct: 1 },
          { option: '', correct: 0 },
          { option: '', correct: 0 },
        ],
      }
}

function mark(index) {
  const options = draft.value.options

  if (draft.value.kind === 'One answer') {
    options.forEach((option, position) => (option.correct = position === index ? 1 : 0))
  } else {
    options[index].correct = options[index].correct ? 0 : 1
  }
}

function tidyKind(kind) {
  if (kind !== 'One answer') return
  const first = draft.value.options.findIndex((option) => option.correct)
  draft.value.options.forEach((option, position) => (option.correct = position === Math.max(0, first) ? 1 : 0))
}

async function save() {
  saving.value = true
  saveError.value = null

  try {
    await call('sop.api.quiz.save_question', {
      sop: props.sop,
      name: draft.value.name,
      question: draft.value.question,
      kind: draft.value.kind,
      explanation: draft.value.explanation,
      enabled: draft.value.enabled ? 1 : 0,
      options: draft.value.options,
    })
    toast.success(draft.value.name ? __('Question updated') : __('Question added'))
    draft.value = null
    list.reload()
  } catch (failure) {
    saveError.value = failure.messages?.[0] || failure.message
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  removing.value = row.name
  try {
    await call('sop.api.quiz.delete_question', { name: row.name })
    toast.success(__('Question deleted'))
    list.reload()
  } catch (failure) {
    toast.error(failure.messages?.[0] || failure.message)
  } finally {
    removing.value = null
  }
}
</script>
