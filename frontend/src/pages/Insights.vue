<template>
  <PageHeader>
    <AppBreadcrumbs />
    <Button
      variant="ghost"
      icon-left="lucide-refresh-cw"
      :label="__('Refresh')"
      :loading="report.loading"
      @click="report.reload()"
    />
  </PageHeader>

  <div class="mx-auto w-full max-w-[1200px] px-3 pb-12 pt-4 sm:px-5">
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <FormControl v-model="space" type="select" :options="spaceOptions" class="w-56" :aria-label="__('Space')" />
      <TabButtons v-model="days" :options="periods" />
      <span v-if="data?.scope === 'mine'" class="flex items-center gap-1.5 text-sm text-ink-gray-5">
        <span class="lucide-user size-3.5" aria-hidden="true" />
        {{ __('Showing procedures you own') }}
      </span>
    </div>

    <ErrorMessage v-if="report.error" :message="report.error.messages?.[0] || report.error.message" class="mb-4" />

    <div v-if="!data && report.loading" class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
      <Skeleton v-for="n in 5" :key="n" class="h-32 rounded-3" />
      <Skeleton class="col-span-full h-72 rounded-3" />
    </div>

    <div v-else-if="data" class="flex flex-col gap-6 transition-opacity" :class="report.loading ? 'opacity-60' : ''">
      <section id="insights-overview" class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5" :aria-label="__('Overview')">
        <StatTile
          :label="__('In force')"
          icon="lucide-book-check"
          :value="kpis.in_force"
          :detail="__('{0} drafts · {1} in review').format(kpis.drafts, kpis.in_review)"
        />
        <StatTile
          :label="__('Read and signed')"
          icon="lucide-signature"
          :value="kpis.signed_percent"
          unit="%"
          :meter="kpis.signed_percent"
          :state="band(kpis.signed_percent)"
          :detail="__('{0} of {1} signatures').format(number(kpis.signatures), number(kpis.signatures_needed))"
        />
        <StatTile
          :label="__('Training done')"
          icon="lucide-graduation-cap"
          :value="kpis.training_percent"
          unit="%"
          :meter="kpis.training_percent"
          :state="kpis.training_overdue ? 'critical' : band(kpis.training_percent)"
          :detail="
            kpis.training_overdue
              ? __('{0} overdue').format(kpis.training_overdue)
              : __('{0} of {1} complete').format(kpis.training_done, kpis.training_total)
          "
        />
        <StatTile
          :label="__('Reviews overdue')"
          icon="lucide-calendar-clock"
          :value="kpis.reviews_overdue"
          :state="kpis.reviews_overdue ? 'critical' : 'good'"
          :detail="
            kpis.reviews_soon
              ? __('{0} more due in 30 days').format(kpis.reviews_soon)
              : __('None due in 30 days')
          "
        />
        <StatTile
          :label="__('Found it clear')"
          icon="lucide-lightbulb"
          :value="kpis.clear_percent"
          unit="%"
          :meter="kpis.clear_percent"
          :state="band(kpis.clear_percent)"
          :detail="kpis.votes ? __('From {0} reader votes').format(kpis.votes) : __('No votes in this period')"
        />
      </section>

      <section id="insights-activity" class="grid gap-3 lg:grid-cols-3" :aria-label="__('Activity')">
        <ChartCard
          v-model:table="trendTable"
          class="lg:col-span-2"
          :title="__('Activity')"
          :subtitle="data.trend.grain === 'day' ? __('Per day') : __('Per week')"
        >
          <template #legend>
            <ul class="flex shrink-0 items-center gap-3 pt-0.5 text-sm text-ink-gray-7">
              <li v-for="line in trendSeries" :key="line.key" class="flex items-center gap-1.5">
                <span class="h-0.5 w-3.5 rounded-full" :style="{ background: line.color }" aria-hidden="true" />
                {{ line.label }}
              </li>
            </ul>
          </template>

          <TrendChart
            :labels="data.trend.periods"
            :series="trendSeries"
            :grain="data.trend.grain"
            :table="trendTable"
          />
        </ChartCard>

        <ChartCard v-model:table="stageTable" :title="__('Where procedures are')" :subtitle="__('By stage, right now')">
          <BarList
            :rows="stageRows"
            :table="stageTable"
            :label-heading="__('Stage')"
            :value-heading="__('Procedures')"
          />
        </ChartCard>
      </section>

      <section id="insights-attention" :aria-label="__('Needs attention')">
        <h2 class="mb-3 text-lg font-semibold text-ink-gray-9">{{ __('Needs attention') }}</h2>

        <div class="grid gap-3 md:grid-cols-2">
          <ChartCard :title="__('Reviews coming due')" :subtitle="__('Overdue, or due in the next 30 days')" :toggle="false">
            <ul v-if="data.reviews.length" class="-mx-1 flex flex-col">
              <li v-for="row in data.reviews" :key="row.name">
                <button type="button" class="flex w-full items-center gap-3 rounded-2 px-1 py-1.5 text-left hover:bg-surface-gray-1" @click="open(row.name)">
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-base text-ink-gray-8">{{ row.title }}</span>
                    <span class="block font-mono text-xs text-ink-gray-5">{{ row.sop_no }}</span>
                  </span>
                  <span class="flex shrink-0 items-center gap-1.5 text-sm" :class="row.days < 0 ? 'text-ink-red-3' : 'text-ink-amber-6'">
                    <span :class="row.days < 0 ? 'lucide-circle-alert' : 'lucide-clock'" class="size-3.5" aria-hidden="true" />
                    {{ dueText(row.days) }}
                  </span>
                </button>
              </li>
            </ul>
            <EmptyLine v-else :text="__('Nothing due in the next 30 days')" />
          </ChartCard>

          <ChartCard :title="__('Least read')" :subtitle="__('Share of people who signed the version in force')" :toggle="false">
            <ul v-if="data.coverage.length" class="-mx-1 flex flex-col">
              <li v-for="row in data.coverage" :key="row.name">
                <button type="button" class="flex w-full items-center gap-3 rounded-2 px-1 py-1.5 text-left hover:bg-surface-gray-1" @click="open(row.name)">
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-base text-ink-gray-8">{{ row.title }}</span>
                    <span class="block text-xs text-ink-gray-5">
                      {{ __('{0} of {1} signed · Rev {2}').format(row.signed, row.audience, row.version) }}
                    </span>
                  </span>
                  <span class="flex w-28 shrink-0 items-center gap-2">
                    <span
                      class="h-1.5 flex-1 overflow-hidden rounded-full"
                      style="background: color-mix(in srgb, var(--viz-1) 18%, transparent)"
                      aria-hidden="true"
                    >
                      <span class="block h-full rounded-full" :style="{ width: `${row.percent || 0}%`, background: 'var(--viz-1)' }" />
                    </span>
                    <span class="w-9 text-right text-sm font-medium tabular-nums text-ink-gray-8">{{ row.percent ?? 0 }}%</span>
                  </span>
                </button>
              </li>
            </ul>
            <EmptyLine v-else :text="__('No procedures in force yet')" />
          </ChartCard>

          <ChartCard :title="__('Waiting for approval')" :subtitle="__('Longest wait first')" :toggle="false">
            <ul v-if="data.waiting.length" class="-mx-1 flex flex-col">
              <li v-for="row in data.waiting" :key="row.name">
                <button type="button" class="flex w-full items-center gap-3 rounded-2 px-1 py-1.5 text-left hover:bg-surface-gray-1" @click="open(row.name)">
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-base text-ink-gray-8">{{ row.title }}</span>
                    <span class="block truncate text-xs text-ink-gray-5">
                      {{ __('Waiting on {0}').format(row.waiting_on.join(', ')) }}
                    </span>
                  </span>
                  <span class="flex shrink-0 items-center gap-1.5 text-sm" :class="row.days > 7 ? 'text-ink-amber-6' : 'text-ink-gray-6'">
                    <span v-if="row.days > 7" class="lucide-hourglass size-3.5" aria-hidden="true" />
                    {{ row.days === 1 ? __('1 day') : __('{0} days').format(row.days) }}
                  </span>
                </button>
              </li>
            </ul>
            <EmptyLine v-else :text="__('Nothing is waiting for approval')" />
          </ChartCard>

          <ChartCard :title="__('Hard to follow')" :subtitle="__('Readers who marked it unclear, this period')" :toggle="false">
            <ul v-if="data.unclear.length" class="-mx-1 flex flex-col">
              <li v-for="row in data.unclear" :key="row.name">
                <button type="button" class="flex w-full items-start gap-3 rounded-2 px-1 py-1.5 text-left hover:bg-surface-gray-1" @click="open(row.name)">
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-base text-ink-gray-8">{{ row.title }}</span>
                    <span v-if="row.note" class="mt-0.5 block truncate text-sm italic text-ink-gray-6">“{{ row.note }}”</span>
                  </span>
                  <span class="shrink-0 text-sm text-ink-gray-6">
                    {{ __('{0} of {1} unclear').format(row.unclear, row.votes) }}
                  </span>
                </button>
              </li>
            </ul>
            <EmptyLine v-else :text="__('Nobody marked a procedure unclear')" />
          </ChartCard>

          <ChartCard :title="__('Training overdue')" :subtitle="__('People with the most overdue training')" :toggle="false" class="md:col-span-2">
            <ul v-if="data.behind.length" class="-mx-1 grid gap-x-6 sm:grid-cols-2">
              <li v-for="row in data.behind" :key="row.name">
                <button type="button" class="flex w-full items-center gap-3 rounded-2 px-1 py-1.5 text-left hover:bg-surface-gray-1" @click="router.push('/training/matrix')">
                  <Avatar :image="row.image" :label="row.full_name" size="md" shape="circle" />
                  <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">{{ row.full_name }}</span>
                  <span class="flex shrink-0 items-center gap-1.5 text-sm text-ink-red-3">
                    <span class="lucide-circle-alert size-3.5" aria-hidden="true" />
                    {{ __('{0} overdue').format(row.overdue) }}
                  </span>
                </button>
              </li>
            </ul>
            <EmptyLine v-else :text="__('Nobody is behind on training')" />
          </ChartCard>
        </div>
      </section>

      <section id="insights-spaces" :aria-label="__('By space')">
        <h2 class="mb-3 text-lg font-semibold text-ink-gray-9">{{ __('By space') }}</h2>

        <div class="overflow-x-auto rounded-3 border border-outline-gray-2">
          <table class="w-full min-w-[36rem] text-sm">
            <thead>
              <tr class="bg-surface-gray-1 text-left text-ink-gray-6">
                <th class="px-3 py-2 font-medium">{{ __('Space') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('In force') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Signed') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Training done') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Reviews overdue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in data.spaces"
                :key="row.space || 'none'"
                class="cursor-pointer border-t border-outline-gray-1 hover:bg-surface-gray-1"
                @click="row.space && (space = row.space)"
              >
                <td class="px-3 py-2 text-ink-gray-8">{{ row.title }}</td>
                <td class="px-3 py-2 text-right tabular-nums text-ink-gray-8">{{ row.in_force }}</td>
                <td class="px-3 py-2 text-right tabular-nums text-ink-gray-8">{{ pct(row.signed_percent) }}</td>
                <td class="px-3 py-2 text-right tabular-nums text-ink-gray-8">{{ pct(row.training_percent) }}</td>
                <td class="px-3 py-2 text-right tabular-nums">
                  <span v-if="row.reviews_overdue" class="inline-flex items-center gap-1 text-ink-red-3">
                    <span class="lucide-circle-alert size-3.5" aria-hidden="true" />
                    {{ row.reviews_overdue }}
                  </span>
                  <span v-else class="text-ink-gray-5">0</span>
                </td>
              </tr>
              <tr v-if="!data.spaces.length">
                <td colspan="5" class="px-3 py-6 text-center text-ink-gray-5">{{ __('No spaces yet') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, h, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Avatar,
  Button,
  ErrorMessage,
  FormControl,
  PageHeader,
  Skeleton,
  TabButtons,
  createResource,
} from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import BarList from '@/components/Insights/BarList.vue'
import ChartCard from '@/components/Insights/ChartCard.vue'
import StatTile from '@/components/Insights/StatTile.vue'
import TrendChart from '@/components/Insights/TrendChart.vue'
import { spaces } from '@/data/navigation'
import { translate as __ } from '@/translation'

const router = useRouter()

const space = ref('')
const days = ref(90)
const trendTable = ref(false)
const stageTable = ref(false)

const periods = [
  { label: __('30 days'), value: 30 },
  { label: __('90 days'), value: 90 },
  { label: __('12 months'), value: 365 },
]

const STAGES = {
  Draft: 'Draft',
  'In Review': 'In review',
  Approved: 'Approved',
  Effective: 'In force',
  'Under Revision': 'Being revised',
  Retired: 'Retired',
}

const report = createResource({
  url: 'sop.api.insights.overview',
  auto: true,
  makeParams: () => ({ space: space.value || undefined, days: days.value }),
})

watch([space, days], () => report.reload())

const data = computed(() => report.data || null)

const kpis = computed(() => data.value?.kpis || {})

const spaceOptions = computed(() => [
  { label: __('All spaces'), value: '' },
  ...spaces.value.map((row) => ({ label: row.title, value: row.name })),
])

const trendSeries = computed(() => [
  { key: 'signed', label: __('Signed'), color: 'var(--viz-1)', values: data.value?.trend.signed || [] },
  { key: 'trained', label: __('Training completed'), color: 'var(--viz-2)', values: data.value?.trend.trained || [] },
])

const stageRows = computed(() =>
  (data.value?.stages || []).map((row) => ({ label: __(STAGES[row.status] || row.status), value: row.count })),
)

const EmptyLine = (props) =>
  h('p', { class: 'flex items-center gap-2 py-3 text-sm text-ink-gray-5' }, [
    h('span', { class: 'lucide-circle-check size-4 text-ink-green-3', 'aria-hidden': 'true' }),
    props.text,
  ])
EmptyLine.props = ['text']

function band(value) {
  if (value === null || value === undefined) return ''
  if (value >= 90) return 'good'
  if (value >= 70) return 'warning'
  return 'critical'
}

function number(value) {
  return Number(value || 0).toLocaleString()
}

function pct(value) {
  return value === null || value === undefined ? '—' : `${value}%`
}

function dueText(days) {
  if (days < 0) return days === -1 ? __('1 day overdue') : __('{0} days overdue').format(-days)
  if (days === 0) return __('Due today')
  return days === 1 ? __('Due tomorrow') : __('In {0} days').format(days)
}

function open(name) {
  router.push(`/${name}`)
}
</script>
