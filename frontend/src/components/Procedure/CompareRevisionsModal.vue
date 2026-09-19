<template>
  <Dialog v-model="show" :options="{ size: '4xl', title: __('Compare Revisions') }">
    <template #body-content>
      <div class="space-y-4 py-2">
        <div class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-gray-2 p-3 text-sm">
          <div class="flex items-center gap-2">
            <span class="font-medium text-ink-gray-7">{{ __('Comparing:') }}</span>
            <select
              v-model="selectedV1"
              class="rounded-md border border-outline-gray-2 bg-surface-white px-2 py-1 text-sm font-semibold text-ink-gray-9 shadow-xs"
              @change="fetchDiff"
            >
              <option :value="null">{{ __('Original / Initial') }}</option>
              <option v-for="rev in revisionsList" :key="`v1-${rev.version}`" :value="rev.version">
                Rev {{ rev.version }}
              </option>
            </select>
            <span class="text-ink-gray-4">➔</span>
            <select
              v-model="selectedV2"
              class="rounded-md border border-outline-gray-2 bg-surface-white px-2 py-1 text-sm font-semibold text-ink-gray-9 shadow-xs"
              @change="fetchDiff"
            >
              <option v-for="rev in revisionsList" :key="`v2-${rev.version}`" :value="rev.version">
                Rev {{ rev.version }}
              </option>
            </select>
          </div>

          <div class="flex items-center gap-1 rounded-md bg-surface-white p-1 border border-outline-gray-2">
            <button
              class="px-2.5 py-1 text-xs font-medium rounded transition-colors"
              :class="viewMode === 'inline' ? 'bg-ink-gray-9 text-surface-white' : 'text-ink-gray-7 hover:bg-surface-gray-2'"
              @click="viewMode = 'inline'"
            >
              {{ __('Inline View') }}
            </button>
            <button
              class="px-2.5 py-1 text-xs font-medium rounded transition-colors"
              :class="viewMode === 'sideBySide' ? 'bg-ink-gray-9 text-surface-white' : 'text-ink-gray-7 hover:bg-surface-gray-2'"
              @click="viewMode = 'sideBySide'"
            >
              {{ __('Side by Side') }}
            </button>
          </div>
        </div>

        <div v-if="v2Info" class="rounded-md border border-emerald-200 bg-emerald-50/50 p-3 text-xs text-emerald-950">
          <span class="font-semibold">{{ __('Change Summary (Rev ' + selectedV2 + '):') }}</span>
          {{ v2Info.change_summary || __('No summary recorded.') }}
        </div>

        <div v-if="loading" class="py-12 text-center text-sm text-ink-gray-5">
          {{ __('Loading revision comparison...') }}
        </div>

        <div v-else-if="viewMode === 'inline'" class="max-h-[60vh] overflow-y-auto space-y-2 rounded-md border border-outline-gray-2 p-4 text-sm font-sans bg-surface-white">
          <div
            v-for="(chunk, idx) in diffs"
            :key="idx"
            class="rounded px-3 py-1.5 transition-colors"
            :class="{
              'bg-emerald-50 text-emerald-900 border-l-4 border-emerald-500 font-medium': chunk.type === 'inserted',
              'bg-rose-50 text-rose-900 border-l-4 border-rose-500 line-through opacity-80': chunk.type === 'deleted',
              'text-ink-gray-8': chunk.type === 'unchanged'
            }"
          >
            <div class="flex items-center justify-between text-[11px] font-mono uppercase tracking-wider mb-1" v-if="chunk.type !== 'unchanged'">
              <span v-if="chunk.type === 'inserted'" class="text-emerald-700 font-semibold">+ {{ __('Added in Rev') }} {{ selectedV2 }}</span>
              <span v-if="chunk.type === 'deleted'" class="text-rose-700 font-semibold">- {{ __('Removed from Rev') }} {{ selectedV1 || 'Base' }}</span>
            </div>
            <div v-html="chunk.text" />
          </div>
        </div>

        <div v-else-if="viewMode === 'sideBySide'" class="grid grid-cols-2 gap-4 max-h-[60vh] overflow-y-auto rounded-md border border-outline-gray-2 p-4 text-sm bg-surface-white">
          <div class="space-y-2 border-r border-outline-gray-1 pr-3">
            <div class="text-xs font-semibold text-ink-gray-6 uppercase tracking-wider pb-2 border-b border-outline-gray-2">
              Rev {{ selectedV1 || 'Base' }}
            </div>
            <template v-for="(chunk, idx) in diffs" :key="`left-${idx}`">
              <div
                v-if="chunk.type !== 'inserted'"
                class="rounded p-2"
                :class="chunk.type === 'deleted' ? 'bg-rose-50 text-rose-900 border-l-3 border-rose-500' : 'text-ink-gray-8'"
                v-html="chunk.text"
              />
            </template>
          </div>

          <div class="space-y-2 pl-1">
            <div class="text-xs font-semibold text-ink-gray-6 uppercase tracking-wider pb-2 border-b border-outline-gray-2">
              Rev {{ selectedV2 }}
            </div>
            <template v-for="(chunk, idx) in diffs" :key="`right-${idx}`">
              <div
                v-if="chunk.type !== 'deleted'"
                class="rounded p-2"
                :class="chunk.type === 'inserted' ? 'bg-emerald-50 text-emerald-900 border-l-3 border-emerald-500' : 'text-ink-gray-8'"
                v-html="chunk.text"
              />
            </template>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Dialog, createResource } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  sopName: { type: String, required: true },
  initialV1: { type: [Number, String], default: null },
  initialV2: { type: [Number, String], default: null },
})

const emit = defineEmits(['update:modelValue'])

const show = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const selectedV1 = ref(props.initialV1)
const selectedV2 = ref(props.initialV2)
const viewMode = ref('inline')
const diffs = ref([])
const v1Info = ref(null)
const v2Info = ref(null)
const revisionsList = ref([])

const compareResource = createResource({
  url: 'sop.api.procedures.compare_revisions',
  makeParams: () => ({
    sop: props.sopName,
    v1: selectedV1.value,
    v2: selectedV2.value,
  }),
  onSuccess: (data) => {
    diffs.value = data.diffs || []
    v1Info.value = data.v1
    v2Info.value = data.v2
    revisionsList.value = data.revisions_list || []
    if (data.v1 && !selectedV1.value) selectedV1.value = data.v1.version
    if (data.v2 && !selectedV2.value) selectedV2.value = data.v2.version
  },
})

const loading = computed(() => compareResource.loading)

const fetchDiff = () => {
  if (props.sopName) {
    compareResource.fetch()
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      selectedV1.value = props.initialV1
      selectedV2.value = props.initialV2
      fetchDiff()
    }
  },
)
</script>
