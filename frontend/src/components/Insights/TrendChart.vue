<template>
  <div ref="box" class="relative w-full">
    <table v-if="table" class="w-full text-sm">
      <thead>
        <tr class="border-b border-outline-gray-2 text-left text-ink-gray-6">
          <th class="py-1.5 pr-3 font-medium">{{ grain === 'day' ? __('Day') : __('Week of') }}</th>
          <th v-for="line in series" :key="line.key" class="py-1.5 pr-3 text-right font-medium">{{ line.label }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(label, index) in labels" :key="label" class="border-b border-outline-gray-1 last:border-0">
          <td class="py-1 pr-3 text-ink-gray-7">{{ format(label) }}</td>
          <td v-for="line in series" :key="line.key" class="py-1 pr-3 text-right tabular-nums text-ink-gray-8">
            {{ line.values[index] }}
          </td>
        </tr>
      </tbody>
    </table>

    <template v-else>
      <svg
        :width="width"
        :height="HEIGHT"
        class="block touch-none select-none outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        role="img"
        tabindex="0"
        :aria-label="summary"
        @pointermove="track"
        @pointerleave="active = null"
        @keydown="step"
        @blur="active = null"
      >
        <g v-for="tick in ticks" :key="tick">
          <line
            :x1="LEFT"
            :x2="width - RIGHT"
            :y1="y(tick)"
            :y2="y(tick)"
            :stroke="tick === 0 ? 'var(--viz-axis)' : 'var(--viz-grid)'"
            stroke-width="1"
            shape-rendering="crispEdges"
          />
          <text
            :x="LEFT - 8"
            :y="y(tick)"
            text-anchor="end"
            dominant-baseline="middle"
            fill="var(--ink-gray-5)" class="text-[11px] tabular-nums"
          >
            {{ tick.toLocaleString() }}
          </text>
        </g>

        <text
          v-for="index in xTicks"
          :key="`x${index}`"
          :x="x(index)"
          :y="HEIGHT - 8"
          :text-anchor="index === 0 ? 'start' : index === labels.length - 1 ? 'end' : 'middle'"
          fill="var(--ink-gray-5)" class="text-[11px]"
        >
          {{ format(labels[index]) }}
        </text>

        <line
          v-if="active !== null"
          :x1="x(active)"
          :x2="x(active)"
          :y1="TOP"
          :y2="TOP + plot"
          stroke="var(--viz-axis)"
          stroke-width="1"
          shape-rendering="crispEdges"
        />

        <path
          v-for="line in series"
          :key="line.key"
          :d="path(line.values)"
          fill="none"
          :stroke="line.color"
          stroke-width="2"
          stroke-linejoin="round"
          stroke-linecap="round"
        />

        <g v-for="line in series" :key="`${line.key}-end`">
          <circle
            :cx="x(active ?? labels.length - 1)"
            :cy="y(line.values[active ?? labels.length - 1] || 0)"
            r="4"
            :fill="line.color"
            stroke="var(--viz-surface)"
            stroke-width="2"
          />
        </g>

        <text
          v-for="label in endLabels"
          :key="`${label.key}-label`"
          :x="width - RIGHT + 8"
          :y="label.y"
          dominant-baseline="middle"
          fill="var(--ink-gray-7)" class="text-[11px] font-medium tabular-nums"
        >
          {{ label.value }}
        </text>
      </svg>

      <div
        v-if="active !== null"
        class="pointer-events-none absolute top-1 z-10 min-w-36 rounded-2 border border-outline-gray-2 bg-surface-base px-2.5 py-2 text-sm shadow-lg"
        :style="tooltipStyle"
        role="status"
      >
        <p class="mb-1 text-xs text-ink-gray-5">{{ grain === 'day' ? format(labels[active]) : __('Week of {0}').format(format(labels[active])) }}</p>
        <p v-for="line in series" :key="line.key" class="flex items-center gap-2">
          <span class="h-0.5 w-3 shrink-0 rounded-full" :style="{ background: line.color }" aria-hidden="true" />
          <span class="font-semibold tabular-nums text-ink-gray-9">{{ line.values[active] }}</span>
          <span class="text-ink-gray-6">{{ line.label }}</span>
        </p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { translate as __ } from '@/translation'

const HEIGHT = 220
const TOP = 12
const BOTTOM = 28
const LEFT = 36
const RIGHT = 40

const props = defineProps({
  labels: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  grain: { type: String, default: 'week' },
  table: { type: Boolean, default: false },
})

const box = ref(null)
const width = ref(640)
const active = ref(null)
let observer = null

const plot = HEIGHT - TOP - BOTTOM

const tickStep = computed(() => {
  const highest = Math.max(0, ...props.series.flatMap((line) => line.values))
  if (highest <= 4) return 1

  const rough = highest / 4
  const power = 10 ** Math.floor(Math.log10(rough))
  return [1, 2, 2.5, 5, 10].map((n) => n * power).find((n) => n >= rough && Number.isInteger(n))
})

const tickCount = computed(() => {
  const highest = Math.max(0, ...props.series.flatMap((line) => line.values))
  return Math.max(1, Math.ceil(highest / tickStep.value))
})

const top = computed(() => tickStep.value * tickCount.value)

const ticks = computed(() => Array.from({ length: tickCount.value + 1 }, (_, n) => n * tickStep.value))

const xTicks = computed(() => {
  const count = props.labels.length
  if (count <= 1) return count ? [0] : []

  const room = Math.max(2, Math.floor((width.value - LEFT - RIGHT) / 90))
  const every = Math.max(1, Math.ceil((count - 1) / (room - 1)))
  const out = []
  for (let index = 0; index < count; index += every) out.push(index)
  if (out[out.length - 1] !== count - 1) {
    if (count - 1 - out[out.length - 1] < every / 2) out.pop()
    out.push(count - 1)
  }
  return out
})

const endLabels = computed(() => {
  if (active.value !== null) return []

  const last = props.labels.length - 1
  const rows = props.series.map((line) => ({ key: line.key, value: line.values[last] ?? 0, y: y(line.values[last] || 0) }))
  if (rows.length === 2 && Math.abs(rows[0].y - rows[1].y) < 12) return []
  return rows
})

const summary = computed(() =>
  props.series
    .map((line) => `${line.label}: ${line.values.reduce((sum, value) => sum + value, 0)} ${__('in this period')}`)
    .join('. '),
)

const tooltipStyle = computed(() => {
  const left = x(active.value)
  return left > width.value / 2 ? { right: `${width.value - left + 12}px` } : { left: `${left + 12}px` }
})

function x(index) {
  const count = props.labels.length
  if (count <= 1) return LEFT
  return LEFT + (index * (width.value - LEFT - RIGHT)) / (count - 1)
}

function y(value) {
  return TOP + plot - (value / top.value) * plot
}

function path(values) {
  return values.map((value, index) => `${index ? 'L' : 'M'}${x(index).toFixed(1)},${y(value).toFixed(1)}`).join(' ')
}

function format(value) {
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

function track(event) {
  const count = props.labels.length
  if (!count) return

  const bounds = event.currentTarget.getBoundingClientRect()
  const ratio = (event.clientX - bounds.left - LEFT) / (width.value - LEFT - RIGHT)
  active.value = Math.max(0, Math.min(count - 1, Math.round(ratio * (count - 1))))
}

function step(event) {
  const count = props.labels.length
  if (!count) return

  if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
    event.preventDefault()
    const from = active.value ?? count - 1
    active.value = Math.max(0, Math.min(count - 1, from + (event.key === 'ArrowRight' ? 1 : -1)))
  } else if (event.key === 'Escape') {
    active.value = null
  }
}

onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    width.value = Math.max(280, Math.floor(entry.contentRect.width))
  })
  if (box.value) observer.observe(box.value)
})

onBeforeUnmount(() => observer?.disconnect())
</script>
