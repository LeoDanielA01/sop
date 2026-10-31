<template>
  <section
    v-for="assessment in assessments.data || []"
    :key="assessment.name"
    class="mb-6 rounded-4 border border-outline-gray-2 bg-surface-base"
    :aria-label="__('Risk assessment')"
  >
    <header class="flex flex-wrap items-center gap-2 border-b border-outline-gray-1 px-4 py-2.5">
      <span class="lucide-shield-alert size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
      <h2 class="text-base font-semibold text-ink-gray-9">{{ __('Risk assessment') }}</h2>
      <router-link :to="recordPath('SOP Risk Assessment', assessment.name)" class="text-sm text-ink-gray-6 hover:underline">
        {{ assessment.name }} · v{{ assessment.version }}
      </router-link>
      <span class="flex-1" />
      <span v-if="assessment.open_actions" class="text-sm text-ink-amber-6">
        {{ __('{0} open actions').format(assessment.open_actions) }}
      </span>
      <Badge v-if="assessment.status !== 'Approved'" :label="assessment.status" theme="gray" />
    </header>

    <ul class="divide-y divide-outline-gray-1">
      <li v-for="hazard in shown(assessment)" :key="hazard.row" class="flex items-start gap-3 px-4 py-2.5">
        <span class="mt-0.5 w-20 shrink-0 rounded-2 px-1.5 py-0.5 text-center text-xs font-semibold" :class="tone(hazard.level)">
          {{ hazard.score }} {{ hazard.level }}
        </span>
        <div class="min-w-0 flex-1">
          <p class="text-base text-ink-gray-9">
            <span class="font-medium">{{ hazard.hazard }}</span>
            <span v-if="hazard.task" class="text-ink-gray-5"> · {{ hazard.task }}</span>
          </p>
          <p v-if="hazard.controls" class="text-sm text-ink-gray-6">{{ hazard.controls }}</p>
          <p v-if="hazard.action" class="text-sm text-ink-amber-6">⚠ {{ hazard.action }}</p>
          <p v-if="hazard.check" class="flex flex-wrap items-center gap-2 text-sm" :class="hazard.check_due ? 'text-ink-red-4' : 'text-ink-gray-6'">
            <span class="lucide-repeat size-3.5" aria-hidden="true" />
            {{ hazard.check_every }} · {{ hazard.check }}
            <span v-if="hazard.next_check">· {{ hazard.check_due ? __('due now') : __('next {0}').format(hazard.next_check) }}</span>
            <Button
              v-if="hazard.check_due"
              size="sm"
              :label="__('Mark done')"
              :loading="done.loading && done.params?.row === hazard.row"
              @click="done.submit({ assessment: assessment.name, row: hazard.row, sop })"
            />
          </p>
        </div>
        <span v-if="hazard.residual_score" class="mt-0.5 shrink-0 text-xs text-ink-gray-5" :title="__('Residual risk after actions')">
          → {{ hazard.residual_score }}
        </span>
      </li>
    </ul>

    <button
      v-if="assessment.hazards.length > LIMIT"
      type="button"
      class="w-full border-t border-outline-gray-1 px-4 py-2 text-left text-sm text-ink-gray-6 hover:text-ink-gray-8"
      @click="toggle(assessment.name)"
    >
      {{ open[assessment.name] ? __('Show fewer') : __('Show all {0} hazards').format(assessment.hazards.length) }}
    </button>
  </section>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { Badge, Button, createResource, toast } from 'frappe-ui'
import { recordPath } from '@/utils/records'
import { translate as __ } from '@/translation'

const props = defineProps({ sop: { type: String, default: '' } })
const LIMIT = 4
const open = reactive({})

const assessments = createResource({ url: 'sop.api.risks.for_sop' })
const done = createResource({
  url: 'sop.api.risks.complete_check',
  onSuccess(data) {
    toast.success(__('Check logged as {0}').format(data.log))
    assessments.reload()
  },
})

watch(
  () => props.sop,
  (sop) => sop && assessments.submit({ sop }),
  { immediate: true },
)

function shown(assessment) {
  if (open[assessment.name]) return assessment.hazards
  const due = assessment.hazards.filter((row) => row.check_due)
  const top = assessment.hazards.filter((row) => !row.check_due).slice(0, LIMIT)
  return [...due, ...top]
}

function toggle(name) {
  open[name] = !open[name]
}

function tone(level) {
  return (
    {
      'Very High': 'bg-surface-red-2 text-ink-red-4',
      High: 'bg-surface-red-1 text-ink-red-4',
      Medium: 'bg-surface-amber-1 text-ink-amber-6',
      Low: 'bg-surface-green-1 text-ink-green-3',
    }[level] || 'bg-surface-gray-2 text-ink-gray-6'
  )
}
</script>
