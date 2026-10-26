<template>
  <section class="mb-6 rounded-4 border border-outline-gray-2 bg-surface-base" :aria-label="__('Logs')">
    <header class="flex flex-wrap items-center gap-2 border-b border-outline-gray-1 px-4 py-2.5">
      <span class="lucide-notebook-pen size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
      <h2 class="text-base font-semibold text-ink-gray-9">{{ __('Cleaning & service log') }}</h2>
      <span class="flex-1" />
      <span
        v-for="place in (places.data || []).filter((row) => row.room_status)"
        :key="place.name"
        class="rounded-2 px-1.5 py-0.5 text-xs font-medium"
        :class="statusTone(place.room_status)"
        :title="place.room_status_on"
      >
        {{ place.resource_name }}: {{ place.room_status }}
      </span>
      <Button size="sm" icon-left="lucide-plus" :label="__('Log cleaning')" @click="start('Cleaning')" />
      <Button size="sm" variant="ghost" icon-left="lucide-wrench" :label="__('Log service')" @click="start('Service')" />
    </header>

    <ul v-if="recent.data?.length" class="divide-y divide-outline-gray-1">
      <li v-for="row in recent.data" :key="row.name" class="flex flex-wrap items-baseline gap-x-2 px-4 py-2 text-sm">
        <span class="w-32 shrink-0 text-ink-gray-5">{{ when(row.logged_at) }}</span>
        <span class="font-medium text-ink-gray-8">
          {{ row.log_type === 'Cleaning' ? __('{0} cleaning').format(row.cleaning_type || '') : row.service_type || __('Service') }}
        </span>
        <span v-if="row.where" class="text-ink-gray-6">· {{ row.where }}</span>
        <span v-if="row.room_status" class="text-ink-gray-6">→ {{ row.room_status }}</span>
        <span class="text-ink-gray-5">
          · {{ row.done_by_name }}<template v-if="row.checked_by_name"> / {{ row.checked_by_name }}</template>
        </span>
        <span v-if="row.notes" class="w-full pl-32 text-ink-gray-6">{{ row.notes }}</span>
      </li>
    </ul>
    <p v-else class="px-4 py-3 text-sm text-ink-gray-5">{{ __('Nothing logged for this procedure yet.') }}</p>

    <Dialog v-model="show" :options="{ title: entry.log_type === 'Cleaning' ? __('Log cleaning') : __('Log service') }">
      <template #body-content>
        <div class="grid gap-3 sm:grid-cols-2">
          <FormControl
            v-if="(places.data || []).length"
            v-model="entry.location"
            type="select"
            :label="__('Room / machine')"
            :options="[{ label: '', value: '' }, ...places.data.map((row) => ({ label: row.resource_name, value: row.name }))]"
          />
          <FormControl v-else v-model="entry.location_text" :label="__('Room / machine')" />
          <FormControl
            v-if="entry.log_type === 'Cleaning'"
            v-model="entry.cleaning_type"
            type="select"
            :label="__('Cleaning')"
            :options="['Minor', 'Major']"
          />
          <FormControl
            v-else
            v-model="entry.service_type"
            type="select"
            :label="__('Service')"
            :options="['Inspection', 'Function test', 'Maintenance', 'Repair', 'Filter change']"
          />
          <FormControl
            v-if="entry.log_type === 'Cleaning'"
            v-model="entry.reason"
            type="select"
            :label="__('Reason')"
            :options="['SKU change', 'Last batch of the day', 'Weekly', 'Not clean on arrival', 'Other']"
          />
          <FormControl v-model="entry.product_before" :label="__('Product before (SKU / lot)')" />
          <FormControl
            v-model="entry.room_status"
            type="select"
            :label="__('Set room status to')"
            :options="['', 'Production', 'Minor cleaned', 'Major cleaned', 'Out of service']"
          />
          <FormControl v-model="entry.checked_by" :label="__('Checked by (user)')" :placeholder="__('Optional')" />
          <FormControl v-model="entry.notes" type="textarea" class="sm:col-span-2" :label="__('Notes')" />
        </div>
        <ErrorMessage class="mt-2" :message="save.error?.messages?.[0] || save.error?.message" />
      </template>
      <template #actions>
        <Button variant="solid" class="w-full" :label="__('Save log entry')" :loading="save.loading" @click="submit" />
      </template>
    </Dialog>
  </section>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl, createResource, toast } from 'frappe-ui'
import { translate as __ } from '@/translation'

const props = defineProps({ sop: { type: String, default: '' } })
const show = ref(false)
const entry = reactive({})

const places = createResource({ url: 'sop.api.logs.locations' })
const recent = createResource({ url: 'sop.api.logs.recent' })
const save = createResource({
  url: 'sop.api.logs.create',
  onSuccess(data) {
    show.value = false
    toast.success(__('Logged as {0}').format(data.name))
    load()
  },
})

function load() {
  if (!props.sop) return
  places.submit({ sop: props.sop })
  recent.submit({ sop: props.sop })
}

watch(() => props.sop, load, { immediate: true })

function start(type) {
  for (const key of Object.keys(entry)) delete entry[key]
  Object.assign(entry, {
    log_type: type,
    cleaning_type: type === 'Cleaning' ? 'Minor' : '',
    service_type: type === 'Service' ? 'Inspection' : '',
    room_status: type === 'Cleaning' ? 'Minor cleaned' : '',
  })
  show.value = true
}

function submit() {
  if (entry.room_status === 'Minor cleaned' && entry.cleaning_type === 'Major') entry.room_status = 'Major cleaned'
  save.submit({ sop: props.sop, entry: { ...entry } })
}

function when(value) {
  return value ? String(value).slice(0, 16).replace('T', ' ') : ''
}

function statusTone(status) {
  return (
    {
      Production: 'bg-surface-blue-1 text-ink-blue-3',
      'Minor cleaned': 'bg-surface-green-1 text-ink-green-3',
      'Major cleaned': 'bg-surface-green-1 text-ink-green-3',
      'Out of service': 'bg-surface-red-1 text-ink-red-4',
    }[status] || 'bg-surface-gray-2 text-ink-gray-6'
  )
}
</script>
