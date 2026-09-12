<script setup>
/**
 * People down the side, procedures across the top. The view an auditor asks for
 * and the one that shows a manager where the gaps are, in one screen.
 */
import { computed, onMounted } from 'vue'
import { Badge, Button, PageHeader, PageHeaderTitle, Tooltip } from 'frappe-ui'
import { activeSpace } from '@/data/navigation'
import { matrix } from '@/data/training'

const procedures = computed(() => matrix.data?.procedures || [])
const people = computed(() => matrix.data?.people || [])

const MARK = {
  Completed: { icon: 'lucide-circle-check-big', tone: 'text-ink-green-3', label: 'Trained' },
  'In Progress': { icon: 'lucide-circle-dashed', tone: 'text-ink-amber-3', label: 'In progress' },
  Assigned: { icon: 'lucide-circle', tone: 'text-ink-gray-4', label: 'Assigned' },
  Overdue: { icon: 'lucide-circle-alert', tone: 'text-ink-red-3', label: 'Overdue' },
  Waived: { icon: 'lucide-circle-minus', tone: 'text-ink-gray-4', label: 'Waived' },
}

function cell(person, sop) {
  return person.cells?.[sop] || null
}

function gaps(person) {
  return procedures.value.filter((p) => {
    const c = cell(person, p.name)
    return !c || c.status !== 'Completed'
  }).length
}

onMounted(() => matrix.submit({ space: activeSpace.value }))
</script>

<template>
  <PageHeader>
    <PageHeaderTitle>Training matrix</PageHeaderTitle>
    <Button
      variant="ghost"
      icon-left="lucide-refresh-cw"
      label="Refresh"
      :loading="matrix.loading"
      @click="matrix.submit({ space: activeSpace })"
    />
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[1200px] px-3 pb-10 sm:px-5">
    <!-- Wide on purpose: the grid scrolls inside its own container so the page
         never scrolls sideways. -->
    <div class="overflow-x-auto rounded-lg border border-outline-gray-2">
      <table class="w-full border-collapse text-sm">
        <thead>
          <tr class="bg-surface-gray-1">
            <th class="sticky left-0 z-10 bg-surface-gray-1 px-3 py-2 text-left font-medium text-ink-gray-7">
              Person
            </th>
            <th
              v-for="procedure in procedures"
              :key="procedure.name"
              class="px-2 py-2 text-center font-mono text-xs font-normal text-ink-gray-5"
            >
              <Tooltip :text="procedure.title">
                <span>{{ procedure.sop_no }}</span>
              </Tooltip>
            </th>
            <th class="px-3 py-2 text-right font-medium text-ink-gray-7">Gaps</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="person in people"
            :key="person.user"
            class="border-t border-outline-gray-1"
          >
            <td class="sticky left-0 z-10 bg-surface-base px-3 py-2 text-ink-gray-8">
              {{ person.user }}
            </td>
            <td v-for="procedure in procedures" :key="procedure.name" class="px-2 py-2 text-center">
              <Tooltip
                v-if="cell(person, procedure.name)"
                :text="`${MARK[cell(person, procedure.name).status]?.label} · ${procedure.title}`"
              >
                <span
                  :class="[
                    MARK[cell(person, procedure.name).status]?.icon,
                    MARK[cell(person, procedure.name).status]?.tone,
                  ]"
                  class="inline-block size-4"
                  aria-hidden="true"
                />
              </Tooltip>
              <!-- No assignment at all is different from one not yet done, and
                   it is usually the more serious finding. -->
              <Tooltip v-else text="Not assigned">
                <span class="text-ink-gray-3">·</span>
              </Tooltip>
            </td>
            <td class="px-3 py-2 text-right">
              <Badge :theme="gaps(person) ? 'amber' : 'green'" variant="subtle" size="sm">
                {{ gaps(person) }}
              </Badge>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="!matrix.loading && !people.length" class="mt-16 text-center text-base text-ink-gray-5">
      No training assigned in this space yet. Add a training requirement and it fills in when a
      procedure is published.
    </p>
  </div>
</template>
