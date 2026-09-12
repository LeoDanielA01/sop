<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Badge,
  Button,
  Dialog,
  FormControl,
  PageHeader,
  PageHeaderTitle,
  ProgressBar,
  TabButtons,
  Tooltip,
  createResource,
} from 'frappe-ui'
import { List, ListCell, ListRow } from 'frappe-ui/list'
import { shortDate } from '@/utils/format'

const router = useRouter()

const tab = ref('Open')
const detail = ref(null)
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
  },
})

const judge = createResource({
  url: 'sop.api.training.record_outcome',
  onSuccess: () => {
    outcome.value.open = false
    one.reload()
    assignments.reload()
  },
})

const rows = computed(() => assignments.data || [])

const TONE = { Overdue: 'red', 'In Progress': 'amber', Assigned: 'gray', Completed: 'green', Waived: 'gray' }
const OUTCOME_TONE = {
  Competent: 'green',
  'Needs More Practice': 'amber',
  'Not Competent': 'red',
  Pending: 'gray',
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

<template>
  <PageHeader>
    <PageHeaderTitle>My training</PageHeaderTitle>
    <Button
      variant="ghost"
      icon-left="lucide-grid-3x3"
      label="Training matrix"
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
              <Badge v-if="row.is_refresher" variant="subtle" size="sm">Refresher</Badge>
            </div>
          </div>
        </ListCell>

        <ListCell class="hidden w-40 sm:flex">
          <!-- Progress is tasks ticked, not time elapsed. -->
          <ProgressBar :value="row.progress" size="sm" class="w-full" />
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

    <p v-if="!assignments.loading && !rows.length" class="mt-16 text-center text-base text-ink-gray-5">
      Nothing outstanding. Training lands here when a procedure you follow is published or expires.
    </p>
  </div>

  <Dialog
    :modelValue="!!detail"
    @update:modelValue="detail = null"
    :options="{ title: detail?.title || 'Training', size: 'lg' }"
  >
    <template #body-content>
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

        <Button
          variant="subtle"
          icon-left="lucide-book-open"
          label="Open the procedure"
          @click="router.push(`/${detail.sop}`)"
        />

        <div class="flex flex-col gap-1">
          <div
            v-for="task in detail.tasks"
            :key="task.idx"
            class="flex items-center gap-3 rounded-md border border-outline-gray-1 px-3 py-2"
          >
            <span
              :class="task.completed ? 'lucide-circle-check-big text-ink-green-3' : 'lucide-circle'"
              class="size-4 shrink-0 text-ink-gray-4"
              aria-hidden="true"
            />
            <div class="min-w-0 flex-1">
              <div class="truncate text-base text-ink-gray-8">{{ task.task }}</div>
              <div class="text-sm text-ink-gray-5">
                {{ task.task_type }}
                <template v-if="task.verified_by"> · signed off by {{ task.verified_by }}</template>
                <template v-else-if="task.completed_on">
                  · {{ shortDate(task.completed_on) }}
                </template>
              </div>
            </div>
            <Tooltip v-if="task.verified_by" text="Someone else has to witness this one">
              <span class="lucide-shield-check size-4 text-ink-gray-4" aria-hidden="true" />
            </Tooltip>
            <Button
              v-if="!task.completed"
              variant="subtle"
              label="Done"
              :loading="tick.loading"
              @click="tick.submit({ name: detail.name, idx: task.idx })"
            />
          </div>
        </div>

        <div
          v-if="detail.can_assess"
          class="flex items-center justify-between rounded-md border border-outline-gray-2 px-3 py-2"
        >
          <div class="text-sm text-ink-gray-6">
            Record the outcome
            <template v-if="detail.requires_assessment">
              — pass mark {{ detail.pass_mark }}%
            </template>
          </div>
          <Button variant="solid" label="Assess" @click="outcome.open = true" />
        </div>
      </div>
    </template>
  </Dialog>

  <Dialog v-model="outcome.open" :options="{ title: 'Record outcome', size: 'sm' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl
          type="select"
          label="Outcome"
          :options="['Competent', 'Needs More Practice', 'Not Competent']"
          v-model="outcome.value"
        />
        <FormControl
          v-if="detail?.requires_assessment"
          type="number"
          label="Score %"
          v-model="outcome.score"
        />
        <FormControl type="textarea" label="Remarks" v-model="outcome.remarks" />
        <p class="text-sm text-ink-gray-5">
          Recorded against you as the assessor. Nobody can assess their own training.
        </p>
      </div>
    </template>
    <template #actions>
      <Button variant="solid" label="Save outcome" :loading="judge.loading" @click="save" />
    </template>
  </Dialog>
</template>
