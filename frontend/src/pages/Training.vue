<template>
  <PageHeader>
    <AppBreadcrumbs />
    <Button
      v-if="compact"
      variant="ghost"
      icon-left="lucide-grid-3x3"
      :label="__('Training matrix')"
      @click="router.push('/training/matrix')"
    />
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[940px] px-3 pb-10 sm:px-5">
    <div class="mb-4 flex items-center justify-between">
      <TabButtons
        v-model="tab"
        :options="[
          { label: 'Open', value: 'Open' },
          { label: 'Done', value: 'Done' },
        ]"
        @update:modelValue="assignments.reload()"
      />
      <span class="text-sm text-ink-gray-5">{{ rows.length }} assigned</span>
    </div>

    <List class="-mx-3 sm:list-gap-4">
      <ListRow v-for="row in rows" :key="row.name" class="h-15" @click="open(row)">
        <ListCell>
          <div class="min-w-0 flex-1">
            <div class="truncate leading-none text-ink-gray-8">
              <span class="text-base">{{ row.title || row.sop }}</span>
            </div>
            <div class="mt-1.5 flex min-w-0 items-center gap-2 text-base text-ink-gray-5">
              <span class="shrink-0 font-mono text-sm">{{ row.sop_no }}</span>
              <span class="shrink-0">· {{ row.method }}</span>
              <Badge v-if="row.is_refresher" variant="subtle" size="sm">{{ __('Refresher') }}</Badge>
            </div>
          </div>
        </ListCell>

        <ListCell class="hidden w-40 sm:flex">
          <Progress :value="row.progress" size="sm" class="w-full" />
        </ListCell>

        <ListCell class="justify-end">
          <div class="text-right">
            <Badge :theme="TONE[row.status]" variant="subtle" size="sm">{{ row.status }}</Badge>
            <div class="mt-1.5 whitespace-nowrap text-sm text-ink-gray-5">
              Due {{ shortDate(row.due_on) }}
            </div>
          </div>
        </ListCell>
      </ListRow>
    </List>

    <ListSkeleton v-if="assignments.loading && !rows.length" :avatar="false" />

    <ErrorMessage
      v-if="assignments.error"
      class="mt-6"
      :message="assignments.error?.messages?.[0] || __('Your training could not be loaded.')"
    />

    <p
      v-else-if="!assignments.loading && !rows.length"
      class="mt-16 text-center text-base text-ink-gray-5"
    >
      {{ __('Nothing outstanding. Training lands here when a procedure you follow is published or expires.') }}
    </p>
  </div>

  <Dialog
    :open="!!detail"
    @update:open="detail = null"
    :title="detail?.title || 'Training'" size="lg"
  >
    <template #default>
      <div v-if="detail" class="flex flex-col gap-4">
        <div class="flex flex-wrap items-center gap-2 text-sm text-ink-gray-5">
          <span class="font-mono">{{ detail.sop_no }}</span>
          <span>Rev {{ detail.version }}</span>
          <span>· {{ detail.method }}</span>
          <Badge :theme="TONE[detail.status]" variant="subtle" size="sm">{{ detail.status }}</Badge>
          <Badge :theme="OUTCOME_TONE[detail.outcome]" variant="subtle" size="sm">
            {{ detail.outcome }}
          </Badge>
        </div>

        <div class="flex flex-wrap gap-2">
          <Button
            variant="subtle"
            icon-left="lucide-book-open"
            :label="__('Open the procedure')"
            @click="router.push(`/${detail.sop}`)"
          />
          <Button
            v-if="detail.status === 'Completed' && detail.outcome === 'Competent'"
            variant="subtle"
            icon-left="lucide-award"
            :label="__('Certificate')"
            @click="router.push(`/training/certificate/${detail.name}`)"
          />
        </div>

        <p v-if="detail.remarks" class="flex items-start gap-2 rounded-2 bg-surface-gray-1 px-3 py-2 text-sm text-ink-gray-6">
          <span class="lucide-info mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
          {{ detail.remarks }}
        </p>

        <div class="flex flex-col gap-1">
          <div
            v-for="task in detail.tasks"
            :key="task.idx"
            class="flex items-center gap-3 rounded-3 border border-outline-gray-1 px-3 py-2"
          >
            <span
              :class="task.completed ? 'lucide-circle-check-big text-ink-green-3' : 'lucide-circle text-ink-gray-4'"
              class="size-4 shrink-0"
              aria-hidden="true"
            />
            <div class="min-w-0 flex-1">
              <div class="truncate text-base text-ink-gray-8">{{ task.task }}</div>
              <div class="text-sm text-ink-gray-5">
                <template v-if="task.completed">
                  {{ shortDate(task.completed_on) }}
                  <template v-if="task.verified_by"> · {{ __('signed off by {0}').format(task.verified_by) }}</template>
                  <template v-if="task.note"> · {{ task.note }}</template>
                </template>
                <template v-else-if="task.task_type === 'Assessment' && detail.quiz?.available">
                  {{
                    __('{0} questions · pass mark {1}% · {2} of {3} attempts left').format(
                      detail.quiz.questions,
                      detail.quiz.pass_mark,
                      detail.quiz.attempts_left,
                      detail.quiz.attempts_allowed,
                    )
                  }}
                </template>
                <template v-else>{{ task.task_type }}</template>
              </div>
            </div>

            <template v-if="!task.completed">
              <Button
                v-if="task.task_type === 'Assessment' && detail.quiz?.available && detail.is_mine"
                variant="solid"
                icon-left="lucide-clipboard-check"
                :label="__('Take the quiz')"
                :disabled="!detail.quiz.attempts_left && !detail.quiz.open"
                @click="quizFor = detail.name"
              />
              <Button
                v-else-if="task.witnessed && detail.can_assess"
                variant="solid"
                icon-left="lucide-shield-check"
                :label="__('Sign off')"
                :loading="tick.loading"
                @click="tick.submit({ name: detail.name, idx: task.idx })"
              />
              <Tooltip v-else-if="task.witnessed" :text="__('A trainer or supervisor has to witness and sign this off.')">
                <span class="inline-flex items-center gap-1 rounded-2 bg-surface-gray-2 px-2 py-1 text-xs text-ink-gray-6">
                  <span class="lucide-shield-check size-3.5" aria-hidden="true" />
                  {{ __('Trainer signs this off') }}
                </span>
              </Tooltip>
              <Tooltip v-else-if="task.task_type === 'Read Procedure'" :text="__('This also signs the procedure as read.')">
                <Button
                  variant="subtle"
                  :label="__('Mark as read')"
                  :loading="tick.loading"
                  @click="tick.submit({ name: detail.name, idx: task.idx })"
                />
              </Tooltip>
              <Button
                v-else
                variant="subtle"
                :label="__('Done')"
                :loading="tick.loading"
                @click="tick.submit({ name: detail.name, idx: task.idx })"
              />
            </template>
          </div>
        </div>

        <div v-if="detail.quiz?.attempts?.length" class="rounded-3 border border-outline-gray-1 px-3 py-2">
          <p class="mb-1.5 text-sm font-medium text-ink-gray-7">{{ __('Quiz attempts') }}</p>
          <p
            v-for="(attempt, index) in detail.quiz.attempts"
            :key="index"
            class="flex items-center gap-2 text-sm text-ink-gray-6"
          >
            <span
              :class="attempt.passed ? 'lucide-circle-check text-ink-green-3' : 'lucide-circle-x text-ink-red-3'"
              class="size-3.5"
              aria-hidden="true"
            />
            {{ __('Attempt {0}').format(index + 1) }} · {{ attempt.score }}% ·
            {{ attempt.passed ? __('Passed') : __('Below the pass mark') }}
          </p>
        </div>

        <div
          v-if="detail.can_assess"
          class="flex items-center justify-between rounded-4 border border-outline-gray-2 px-3 py-2"
        >
          <div class="text-sm text-ink-gray-6">
            {{ __('Record the outcome') }}
            <template v-if="detail.requires_assessment">
              — pass mark {{ detail.pass_mark }}%
            </template>
          </div>
          <Button variant="solid" :label="__('Assess')" @click="outcome.open = true" />
        </div>
      </div>
    </template>
  </Dialog>

  <Dialog v-model:open="outcome.open" :title="__('Record outcome')" size="sm">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="judge.error?.messages?.[0]" />
        <FormControl
          type="select"
          :label="__('Outcome')"
          :options="['Competent', 'Needs More Practice', 'Not Competent']"
          v-model="outcome.value"
        />
        <FormControl
          v-if="detail?.requires_assessment"
          type="number"
          :label="__('Score %')"
          v-model="outcome.score"
        />
        <FormControl type="textarea" :label="__('Remarks')" v-model="outcome.remarks" />
        <p class="text-sm text-ink-gray-5">
          {{ __('Recorded against you as the assessor. Nobody can assess their own training.') }}
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="solid" :label="__('Save outcome')" :loading="judge.loading" @click="save" />
      </div>
    </template>
  </Dialog>

  <QuizDialog v-model:assignment="quizFor" @done="afterQuiz" />
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  PageHeader,
  Progress,
  TabButtons,
  Tooltip,
  createResource,
} from 'frappe-ui'
import { List, ListCell, ListRow } from 'frappe-ui/list'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import ListSkeleton from '@/components/Common/ListSkeleton.vue'
import QuizDialog from '@/components/Training/QuizDialog.vue'
import { trainingCounts } from '@/data/training'
import { shortDate } from '@/utils/format'

defineProps({ compact: { type: Boolean, default: false } })

const router = useRouter()

const tab = ref('Open')
const detail = ref(null)
const quizFor = ref(null)
const outcome = ref({ open: false, value: 'Competent', score: null, remarks: '' })

const assignments = createResource({
  url: 'sop.api.training.my_training',
  auto: true,
  makeParams: () => ({ status: tab.value === 'Done' ? 'Completed' : undefined }),
})

const one = createResource({
  url: 'sop.api.training.assignment',
  onSuccess: (data) => (detail.value = data),
})

const tick = createResource({
  url: 'sop.api.training.complete_task',
  onSuccess: () => {
    one.reload()
    assignments.reload()
    trainingCounts.reload()
  },
})

const judge = createResource({
  url: 'sop.api.training.record_outcome',
  onSuccess: () => {
    outcome.value.open = false
    one.reload()
    assignments.reload()
    trainingCounts.reload()
  },
})

const rows = computed(() => assignments.data || [])

const TONE = {
  Overdue: 'red',
  'In Progress': 'amber',
  Assigned: 'gray',
  Completed: 'green',
  Waived: 'gray',
}

const OUTCOME_TONE = {
  Competent: 'green',
  'Needs More Practice': 'amber',
  'Not Competent': 'red',
  Pending: 'gray',
}

function afterQuiz() {
  one.reload()
  assignments.reload()
  trainingCounts.reload()
}

function open(row) {
  one.submit({ name: row.name })
}

function save() {
  judge.submit({
    name: detail.value.name,
    outcome: outcome.value.value,
    score: outcome.value.score,
    remarks: outcome.value.remarks,
  })
}

onMounted(() => assignments.reload())
</script>
