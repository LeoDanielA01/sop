<template>
  <PageHeader>
    <AppBreadcrumbs :tail="[{ label: 'Sessions' }]" />
    <Button
      variant="solid"
      icon-left="lucide-plus"
      :label="__('Plan a session')"
      @click="plan(null)"
    />
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[940px] px-3 pb-10 sm:px-5">
    <div class="mb-4 flex items-center justify-between">
      <TabButtons
        v-model="status"
        :options="[
          { label: 'Planned', value: 'Planned' },
          { label: 'Held', value: 'Held' },
          { label: 'All', value: '' },
        ]"
        @update:modelValue="sessions.reload()"
      />
      <span class="text-sm text-ink-gray-5">{{ rows.length }} session{{ rows.length === 1 ? '' : 's' }}</span>
    </div>

    <List class="-mx-3 sm:list-gap-4">
      <ListRow v-for="row in rows" :key="row.name" class="h-15" @click="openSession(row)">
        <ListCell>
          <div class="min-w-0 flex-1">
            <div class="truncate leading-none text-ink-gray-8">
              <span class="text-base">{{ row.title || 'Untitled session' }}</span>
            </div>
            <div class="mt-1.5 flex min-w-0 items-center gap-2 text-base text-ink-gray-5">
              <span class="shrink-0">{{ row.method }}</span>
              <span v-if="row.location" class="truncate">· {{ row.location }}</span>
              <span class="shrink-0">· {{ row.procedures }} procedure{{ row.procedures === 1 ? '' : 's' }}</span>
            </div>
          </div>
        </ListCell>

        <ListCell class="hidden w-40 sm:flex">
          <Avatar :image="row.trainer_image" :label="row.trainer_name" size="sm" />
          <span class="ml-2 truncate text-base text-ink-gray-6">{{ row.trainer_name }}</span>
        </ListCell>

        <ListCell class="justify-end">
          <div class="text-right">
            <Badge :theme="TONE[row.status]" variant="subtle" size="sm">{{ row.status }}</Badge>
            <div class="mt-1.5 whitespace-nowrap text-sm text-ink-gray-5">
              <template v-if="row.status === 'Held'">
                {{ row.attended }} of {{ row.attendees }} attended
              </template>
              <template v-else>{{ shortDate(row.scheduled_on) }}</template>
            </div>
          </div>
        </ListCell>
      </ListRow>
    </List>

    <ListSkeleton v-if="sessions.loading && !rows.length" />

    <div
      v-if="!sessions.loading && !rows.length"
      class="mt-10 flex flex-col items-center gap-2 rounded-4 border border-dashed border-outline-gray-2 px-4 py-10 text-center"
    >
      <span class="lucide-users size-6 text-ink-gray-4" aria-hidden="true" />
      <p class="text-base text-ink-gray-7">No sessions {{ status ? `marked ${status.toLowerCase()}` : 'yet' }}</p>
      <p class="max-w-[24rem] text-sm text-ink-gray-5">
        {{ __('A session is classroom or on-the-job training for a group. Marking who attended closes their assignments for the procedures it covers.') }}
      </p>
      <Button variant="subtle" icon-left="lucide-plus" :label="__('Plan a session')" @click="plan(null)" />
    </div>
  </div>

  <Dialog
    :open="!!detail"
    @update:open="detail = null"
    :title="detail?.title || 'Session'"
    size="lg"
  >
    <template #default>
      <div v-if="detail" class="flex flex-col gap-4">
        <div class="flex flex-wrap items-center gap-2 text-sm text-ink-gray-5">
          <Badge :theme="TONE[detail.status]" variant="subtle" size="sm">{{ detail.status }}</Badge>
          <span>{{ detail.method }}</span>
          <span v-if="detail.scheduled_on">· {{ shortDate(detail.scheduled_on) }}</span>
          <span v-if="detail.location">· {{ detail.location }}</span>
        </div>

        <div v-if="detail.procedures.length" class="flex flex-wrap gap-1.5">
          <Badge v-for="row in detail.procedures" :key="row.sop" variant="subtle" size="sm">
            {{ row.title }}
          </Badge>
        </div>

        <div class="divide-y divide-outline-gray-1 rounded-4 border border-outline-gray-2 bg-surface-gray-1">
          <div
            v-for="person in detail.attendees"
            :key="person.user"
            class="flex items-center gap-2.5 px-2.5 py-2"
          >
            <Avatar :image="person.image" :label="person.full_name" size="md" />
            <div class="min-w-0 flex-1">
              <div class="truncate text-base text-ink-gray-8">{{ person.full_name }}</div>
              <div class="truncate text-sm text-ink-gray-5">{{ person.user }}</div>
            </div>

            <Switch
              :model-value="!!person.attended"
              :disabled="!detail.can_run"
              @update:model-value="(value) => (person.attended = value ? 1 : 0)"
            />

            <Select
              v-model="person.outcome"
              :options="OUTCOMES"
              size="sm"
              class="w-40"
              :disabled="!detail.can_run || !person.attended"
            />
          </div>

          <p
            v-if="!detail.attendees.length"
            class="px-3 py-6 text-center text-sm text-ink-gray-5"
          >
            {{ __('Nobody is on the list yet. Edit the session to add people.') }}
          </p>
        </div>

        <p class="flex items-start gap-2 text-sm text-ink-gray-5">
          <span class="lucide-info mt-0.5 size-4 shrink-0" aria-hidden="true" />
          {{ __('Saving attendance closes the open assignments of everyone marked competent, for every procedure this session covers.') }}
        </p>

        <ErrorMessage :message="attendance.error?.messages?.[0]" />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          v-if="detail?.can_run && detail?.status !== 'Cancelled'"
          variant="ghost"
          :label="__('Cancel session')"
          :loading="cancel.loading"
          @click="cancel.submit({ name: detail.name })"
        />
        <Button
          v-if="detail?.can_run"
          variant="subtle"
          icon-left="lucide-pencil"
          :label="__('Edit')"
          @click="plan(detail)"
        />
        <Button
          v-if="detail?.can_run"
          variant="solid"
          :label="__('Save attendance')"
          :loading="attendance.loading"
          :disabled="!detail?.attendees.length"
          @click="record"
        />
      </div>
    </template>
  </Dialog>

  <SessionDialog v-model:open="editing" :session="editable" @saved="refresh" />
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  Avatar,
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  PageHeader,
  Select,
  Switch,
  TabButtons,
  createResource,
} from 'frappe-ui'
import { List, ListCell, ListRow } from 'frappe-ui/list'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import ListSkeleton from '@/components/Common/ListSkeleton.vue'
import SessionDialog from '@/components/Training/SessionDialog.vue'
import { trainingCounts } from '@/data/training'
import { shortDate } from '@/utils/format'
import { useUI } from '@/stores/ui'

const TONE = { Planned: 'blue', Held: 'green', Cancelled: 'gray' }
const OUTCOMES = ['Pending', 'Competent', 'Needs More Practice', 'Not Competent']

const ui = useUI()

const status = ref('Planned')
const detail = ref(null)
const editing = ref(false)
const editable = ref(null)

const sessions = createResource({
  url: 'sop.api.sessions.sessions',
  auto: true,
  makeParams: () => ({ status: status.value || undefined }),
})

const one = createResource({
  url: 'sop.api.sessions.session',
  onSuccess: (data) => (detail.value = data),
})

const attendance = createResource({
  url: 'sop.api.sessions.record_attendance',
  onSuccess() {
    detail.value = null
    sessions.reload()
    trainingCounts.reload()
  },
})

const cancel = createResource({
  url: 'sop.api.sessions.cancel_session',
  onSuccess() {
    detail.value = null
    sessions.reload()
  },
})

const rows = computed(() => sessions.data || [])

function openSession(row) {
  one.submit({ name: row.name })
}

function plan(session) {
  editable.value = session
  detail.value = null
  editing.value = true
}

function record() {
  attendance.submit({
    name: detail.value.name,
    rows: detail.value.attendees.map((person) => ({
      user: person.user,
      attended: person.attended ? 1 : 0,
      outcome: person.outcome,
      score: person.score,
      remarks: person.remarks,
    })),
  })
}

function refresh() {
  editable.value = null
  sessions.reload()
}

watch(
  () => ui.sessionDialog,
  (open) => {
    if (!open) return

    plan(null)
    ui.sessionDialog = false
  },
  { immediate: true },
)

onMounted(() => sessions.reload())
</script>
