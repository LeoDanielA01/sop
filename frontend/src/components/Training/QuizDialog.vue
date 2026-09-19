<template>
  <Dialog v-model:open="open" :title="__('Quiz')" size="2xl" :disable-outside-click-to-close="stage === 'answering'">
    <template #default>
      <div v-if="loading" class="flex flex-col gap-3">
        <Skeleton class="h-5 w-2/3" />
        <Skeleton class="h-24 w-full rounded-3" />
        <Skeleton class="h-24 w-full rounded-3" />
      </div>

      <ErrorMessage v-else-if="error" :message="error" />

      <div v-else-if="stage === 'answering' && paper" class="flex flex-col gap-4">
        <div class="flex items-center justify-between gap-3 text-sm text-ink-gray-6">
          <span>
            {{ __('Attempt {0} of {1} · pass mark {2}%').format(paper.attempt_number, paper.attempts_allowed, paper.pass_mark) }}
          </span>
          <span class="tabular-nums">{{ __('{0} of {1} answered').format(answered, paper.questions.length) }}</span>
        </div>

        <div class="h-1 w-full overflow-hidden rounded-full bg-surface-gray-2" aria-hidden="true">
          <div
            class="h-full rounded-full bg-surface-gray-7 transition-all"
            :style="{ width: `${(answered / Math.max(1, paper.questions.length)) * 100}%` }"
          />
        </div>

        <fieldset
          v-for="(item, number) in paper.questions"
          :key="item.key"
          class="rounded-3 border border-outline-gray-2 px-4 py-3"
        >
          <legend class="sr-only">{{ __('Question {0}').format(number + 1) }}</legend>
          <p class="text-base font-medium text-ink-gray-9">
            <span class="mr-1.5 text-ink-gray-5">{{ number + 1 }}.</span>{{ item.question }}
          </p>
          <p class="mt-0.5 text-xs text-ink-gray-5">
            {{ item.kind === 'Several answers' ? __('Pick every answer that applies') : __('Pick one answer') }}
          </p>

          <div class="mt-2.5 flex flex-col gap-1.5">
            <label
              v-for="(option, index) in item.options"
              :key="index"
              class="flex cursor-pointer items-center gap-3 rounded-2 border px-3 py-2 transition-colors"
              :class="
                picked(item.key, index)
                  ? 'border-outline-gray-4 bg-surface-gray-2'
                  : 'border-outline-gray-1 hover:bg-surface-gray-1'
              "
            >
              <input
                :type="item.kind === 'Several answers' ? 'checkbox' : 'radio'"
                :name="`question-${item.key}`"
                :checked="picked(item.key, index)"
                class="shrink-0"
                @change="choose(item, index)"
              />
              <span class="text-base text-ink-gray-8">{{ option }}</span>
            </label>
          </div>
        </fieldset>
      </div>

      <div v-else-if="stage === 'result' && result" class="flex flex-col gap-4">
        <div class="flex items-center gap-4 rounded-3 border px-4 py-4" :class="result.passed ? 'border-outline-gray-2' : 'border-outline-red-2 bg-surface-red-1'">
          <span
            :class="result.passed ? 'lucide-badge-check text-ink-green-3' : 'lucide-circle-x text-ink-red-3'"
            class="size-10 shrink-0"
            aria-hidden="true"
          />
          <div class="min-w-0">
            <p class="text-3xl font-semibold text-ink-gray-9">{{ result.score }}%</p>
            <p class="text-sm text-ink-gray-7">
              <template v-if="result.passed">{{ __('Passed — the pass mark was {0}%.').format(result.pass_mark) }}</template>
              <template v-else-if="result.retraining">
                {{ __('Below the pass mark of {0}%, and no attempts are left. Retraining has been assigned.').format(result.pass_mark) }}
              </template>
              <template v-else>
                {{ __('Below the pass mark of {0}%. You have {1} more attempts.').format(result.pass_mark, result.attempts_left) }}
              </template>
            </p>
          </div>
        </div>

        <div class="flex flex-col gap-2">
          <div
            v-for="(row, number) in result.review"
            :key="row.key"
            class="rounded-3 border border-outline-gray-1 px-4 py-3"
          >
            <p class="flex items-start gap-2 text-base text-ink-gray-9">
              <span
                :class="row.ok ? 'lucide-circle-check text-ink-green-3' : 'lucide-circle-x text-ink-red-3'"
                class="mt-0.5 size-4 shrink-0"
                aria-hidden="true"
              />
              <span>
                <span class="mr-1 text-ink-gray-5">{{ number + 1 }}.</span>{{ row.question }}
                <span class="sr-only">{{ row.ok ? __('Correct') : __('Wrong') }}</span>
              </span>
            </p>

            <ul v-if="options(row.key).length" class="mt-2 flex flex-col gap-1 pl-6">
              <li
                v-for="(option, index) in options(row.key)"
                :key="index"
                class="flex items-center gap-2 text-sm"
                :class="row.correct?.includes(index) ? 'font-medium text-ink-gray-9' : 'text-ink-gray-6'"
              >
                <span
                  :class="row.chosen.includes(index) ? 'lucide-circle-dot' : 'lucide-circle'"
                  class="size-3.5 shrink-0 text-ink-gray-5"
                  aria-hidden="true"
                />
                {{ option }}
                <span v-if="row.chosen.includes(index)" class="text-xs text-ink-gray-5">({{ __('your answer') }})</span>
                <span v-if="row.correct?.includes(index)" class="text-xs text-ink-green-3">· {{ __('correct') }}</span>
              </li>
            </ul>

            <p v-if="!row.ok && row.explanation" class="mt-2 rounded-2 bg-surface-gray-1 px-3 py-2 text-sm text-ink-gray-7">
              {{ row.explanation }}
            </p>
          </div>
        </div>

        <p v-if="!result.passed && result.attempts_left" class="text-sm text-ink-gray-5">
          {{ __('Correct answers stay hidden until you pass or run out of attempts. Re-read the procedure before trying again.') }}
        </p>
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <template v-if="stage === 'answering'">
          <span v-if="confirming" class="mr-auto text-sm text-ink-amber-6">
            {{ __('{0} questions are unanswered and will count as wrong.').format(paper.questions.length - answered) }}
          </span>
          <Button :label="__('Finish later')" @click="open = false" />
          <Button
            variant="solid"
            :label="confirming ? __('Submit anyway') : __('Submit answers')"
            :loading="submitting"
            @click="submit"
          />
        </template>

        <template v-else-if="stage === 'result'">
          <Button
            v-if="!result.passed && result.attempts_left"
            variant="subtle"
            icon-left="lucide-rotate-ccw"
            :label="__('Try again')"
            @click="begin"
          />
          <Button variant="solid" :label="__('Close')" @click="open = false" />
        </template>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, Skeleton, call } from 'frappe-ui'
import { translate as __ } from '@/translation'

const assignment = defineModel('assignment', { type: String, default: null })
const emit = defineEmits(['done'])

const stage = ref('answering')
const paper = ref(null)
const answers = ref({})
const result = ref(null)
const loading = ref(false)
const submitting = ref(false)
const confirming = ref(false)
const error = ref(null)

const open = computed({
  get: () => !!assignment.value,
  set: (value) => {
    if (value) return
    const finished = stage.value === 'result'
    assignment.value = null
    if (finished) emit('done')
  },
})

const answered = computed(() => Object.values(answers.value).filter((picks) => picks.length).length)

watch(assignment, (name) => {
  if (name) begin()
})

async function begin() {
  stage.value = 'answering'
  answers.value = {}
  result.value = null
  confirming.value = false
  error.value = null
  loading.value = true

  try {
    paper.value = await call('sop.api.quiz.start', { assignment: assignment.value })
  } catch (failure) {
    error.value = failure.messages?.[0] || failure.message
  } finally {
    loading.value = false
  }
}

function picked(key, index) {
  return (answers.value[key] || []).includes(index)
}

function choose(item, index) {
  const current = answers.value[item.key] || []
  confirming.value = false

  if (item.kind === 'Several answers') {
    answers.value = {
      ...answers.value,
      [item.key]: current.includes(index) ? current.filter((value) => value !== index) : [...current, index],
    }
  } else {
    answers.value = { ...answers.value, [item.key]: [index] }
  }
}

function options(key) {
  return paper.value?.questions.find((item) => item.key === key)?.options || []
}

async function submit() {
  if (answered.value < paper.value.questions.length && !confirming.value) {
    confirming.value = true
    return
  }

  submitting.value = true
  error.value = null

  try {
    result.value = await call('sop.api.quiz.submit', { attempt: paper.value.attempt, answers: answers.value })
    stage.value = 'result'
  } catch (failure) {
    error.value = failure.messages?.[0] || failure.message
  } finally {
    submitting.value = false
    confirming.value = false
  }
}
</script>
