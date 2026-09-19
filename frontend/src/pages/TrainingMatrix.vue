<template>
  <PageHeader>
    <AppBreadcrumbs :tail="[{ label: 'Matrix' }]" />
    <div class="flex items-center gap-2">
    <Button
      v-if="session.user.is_manager"
      variant="ghost"
      icon-left="lucide-download"
      :label="__('Export records')"
      @click="exportRecords"
    />
    <Button
      variant="solid"
      icon-left="lucide-user-plus"
      :label="__('Assign training')"
      :disabled="!procedures.length"
      @click="showAssign = true"
    />
    </div>
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[1200px] px-3 pb-10 sm:px-5">
    <div v-if="people.length" class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
      <div
        v-for="tile in tiles"
        :key="tile.label"
        class="rounded-4 border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5"
      >
        <div class="flex items-center gap-1.5 text-sm text-ink-gray-5">
          <span :class="tile.icon" class="size-3.5 shrink-0" aria-hidden="true" />
          {{ tile.label }}
        </div>
        <div class="mt-1 text-xl font-semibold" :class="tile.tone || 'text-ink-gray-8'">
          {{ tile.value }}
        </div>
      </div>
    </div>

    <div v-if="people.length" class="mb-3 flex flex-wrap items-center justify-between gap-2">
      <TabButtons
        v-model="scope"
        :options="[
          { label: 'Everyone', value: 'all' },
          { label: 'With gaps', value: 'gaps' },
          { label: 'Overdue', value: 'overdue' },
        ]"
      />
      <span class="text-sm text-ink-gray-5">
        Showing {{ rows.length }} of {{ people.length }}
      </span>
    </div>

    <div
      v-if="matrix.loading && !people.length"
      class="rounded-4 border border-outline-gray-2 px-3 py-2"
    >
      <ListSkeleton :rows="4" />
    </div>

    <ScrollArea v-else-if="rows.length" orientation="horizontal" class="rounded-4 border border-outline-gray-2">
      <table class="w-full border-collapse text-sm">
        <thead>
          <tr class="bg-surface-gray-1">
            <th
              class="sticky left-0 z-10 min-w-[13rem] bg-surface-gray-1 px-3 py-2.5 text-left font-medium text-ink-gray-7"
            >
              {{ __('Person') }}
            </th>
            <th class="hidden w-32 px-3 py-2.5 text-left font-medium text-ink-gray-7 sm:table-cell">
              {{ __('Trained') }}
            </th>
            <th
              v-for="procedure in procedures"
              :key="procedure.name"
              class="px-2 py-2.5 text-center font-normal"
            >
              <Tooltip :text="procedure.title">
                <span class="font-mono text-xs text-ink-gray-5">{{ procedure.sop_no }}</span>
              </Tooltip>
            </th>
            <th class="px-3 py-2.5 text-right font-medium text-ink-gray-7">{{ __('Gaps') }}</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="person in rows"
            :key="person.user"
            class="border-t border-outline-gray-1 hover:bg-surface-gray-1"
          >
            <td class="sticky left-0 z-10 bg-surface-base px-3 py-2.5">
              <div class="flex items-center gap-2.5">
                <Avatar :image="person.user_image" :label="person.full_name" size="md" />
                <div class="min-w-0">
                  <div class="truncate text-base text-ink-gray-8">{{ person.full_name }}</div>
                  <div class="truncate text-sm text-ink-gray-5">{{ person.user }}</div>
                </div>
              </div>
            </td>

            <td class="hidden px-3 py-2.5 sm:table-cell">
              <Progress :value="done(person)" size="sm" />
              <div class="mt-1 text-xs text-ink-gray-5">{{ done(person) }}%</div>
            </td>

            <td
              v-for="procedure in procedures"
              :key="procedure.name"
              class="px-2 py-2.5 text-center"
            >
              <Tooltip :text="`${mark(person, procedure.name).label} · ${procedure.title}`">
                <span
                  class="inline-block size-4"
                  :class="[mark(person, procedure.name).icon, mark(person, procedure.name).tone]"
                  aria-hidden="true"
                />
              </Tooltip>
            </td>

            <td class="px-3 py-2.5 text-right">
              <Badge :theme="gapTone(person)" variant="subtle" size="sm">{{ gaps(person) }}</Badge>
            </td>
          </tr>
        </tbody>
      </table>
    </ScrollArea>

    <div v-if="people.length" class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5">
      <span
        v-for="entry in legend"
        :key="entry.label"
        class="flex items-center gap-1.5 text-sm text-ink-gray-5"
      >
        <span :class="[entry.icon, entry.tone]" class="size-3.5" aria-hidden="true" />
        {{ entry.label }}
      </span>
    </div>

    <div
      v-if="!matrix.loading && !rows.length"
      class="mt-10 flex flex-col items-center gap-2 rounded-4 border border-dashed border-outline-gray-2 px-4 py-12 text-center"
    >
      <span class="lucide-grid-3x3 size-6 text-ink-gray-4" aria-hidden="true" />
      <p class="text-base text-ink-gray-7">{{ emptyTitle }}</p>
      <p class="max-w-[28rem] text-sm text-ink-gray-5">{{ emptyLine }}</p>
      <Button
        v-if="procedures.length && scope === 'all'"
        variant="subtle"
        icon-left="lucide-user-plus"
        :label="__('Assign training')"
        @click="showAssign = true"
      />
      <Button
        v-else-if="scope !== 'all'"
        variant="subtle"
        :label="__('Show everyone')"
        @click="scope = 'all'"
      />
    </div>
  </div>

  <AssignTrainingDialog v-model:open="showAssign" :procedures="procedures" @assigned="reload" />
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Avatar, Badge, Button, PageHeader, Progress, ScrollArea, TabButtons, Tooltip } from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import ListSkeleton from '@/components/Common/ListSkeleton.vue'
import AssignTrainingDialog from '@/components/Training/AssignTrainingDialog.vue'
import { activeSpace } from '@/data/navigation'
import { session } from '@/data/session'
import { matrix, trainingCounts } from '@/data/training'
import { translate as __ } from '@/translation'

const MARK = {
  Completed: { icon: 'lucide-circle-check-big', tone: 'text-ink-green-3', label: 'Trained' },
  'In Progress': { icon: 'lucide-circle-dashed', tone: 'text-ink-amber-3', label: 'In progress' },
  Assigned: { icon: 'lucide-circle', tone: 'text-ink-gray-4', label: 'Assigned' },
  Overdue: { icon: 'lucide-circle-alert', tone: 'text-ink-red-3', label: 'Overdue' },
  Waived: { icon: 'lucide-circle-minus', tone: 'text-ink-gray-4', label: 'Waived' },
}

const MISSING = { icon: 'lucide-minus', tone: 'text-ink-gray-3', label: 'Not assigned' }

const showAssign = ref(false)
const scope = ref('all')

const procedures = computed(() => matrix.data?.procedures || [])
const people = computed(() => matrix.data?.people || [])

const legend = [MARK.Completed, MARK['In Progress'], MARK.Assigned, MARK.Overdue, MISSING]

const rows = computed(() => {
  if (scope.value === 'gaps') return people.value.filter((person) => gaps(person))
  if (scope.value === 'overdue') return people.value.filter((person) => overdue(person))

  return people.value
})

const tiles = computed(() => {
  const trained = people.value.filter((person) => !gaps(person)).length
  const late = people.value.filter((person) => overdue(person)).length
  const missing = people.value.reduce((total, person) => total + gaps(person), 0)

  return [
    { label: __('People'), value: people.value.length, icon: 'lucide-users' },
    { label: __('Fully trained'), value: trained, icon: 'lucide-circle-check-big' },
    { label: __('Gaps'), value: missing, icon: 'lucide-triangle-alert' },
    {
      label: __('Overdue'),
      value: late,
      icon: 'lucide-calendar-clock',
      tone: late ? 'text-ink-red-3' : null,
    },
  ]
})

const emptyTitle = computed(() => {
  if (!procedures.value.length) return 'Nothing in force yet'
  if (scope.value !== 'all') return 'Nobody in this view'

  return 'Nobody is training on these yet'
})

const emptyLine = computed(() => {
  if (!procedures.value.length) {
    return 'The matrix fills in once a procedure in this space comes into force.'
  }

  if (scope.value === 'gaps') return 'Everyone shown is trained on every procedure in force.'
  if (scope.value === 'overdue') return 'Nothing has run past its due date.'

  return 'Assign someone, or write a rule so it happens on its own when a procedure comes into force.'
})

function cell(person, sop) {
  return person.cells?.[sop] || null
}

function mark(person, sop) {
  const row = cell(person, sop)
  return (row && MARK[row.status]) || MISSING
}

function gaps(person) {
  return procedures.value.filter((row) => cell(person, row.name)?.status !== 'Completed').length
}

function overdue(person) {
  return procedures.value.some((row) => cell(person, row.name)?.status === 'Overdue')
}

function done(person) {
  if (!procedures.value.length) return 0

  const trained = procedures.value.length - gaps(person)
  return Math.round((trained * 100) / procedures.value.length)
}

function gapTone(person) {
  if (overdue(person)) return 'red'

  return gaps(person) ? 'amber' : 'green'
}

function reload() {
  matrix.submit({ space: activeSpace.value })
  trainingCounts.reload()
}

watch(activeSpace, reload)

function exportRecords() {
  const query = activeSpace.value ? `?space=${encodeURIComponent(activeSpace.value)}` : ''
  window.open(`/api/method/sop.api.training.export_records${query}`, '_blank')
}
onMounted(reload)
</script>
