<template>
  <PageHeader>
    <AppBreadcrumbs :tail="[{ label: __('Issue to employee') }]" />
  </PageHeader>

  <div class="mx-auto w-full max-w-[940px] px-3 pb-12 pt-4 sm:px-5">
    <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Issue to employee') }}</h1>
    <p class="mt-1 text-base text-ink-gray-6">
      {{ __('Consumables are issued from stock. Anything a person keeps is handed over as an asset.') }}
    </p>

    <ErrorMessage :message="error" class="mt-4" />

    <p
      v-if="choices.data && !choices.data.types.length"
      class="mt-5 max-w-[640px] rounded-4 border border-outline-gray-2 px-4 py-6 text-base text-ink-gray-6"
    >
      {{ __('No resource type can be issued yet. Tick "Can Be Issued To Employees" on a resource type to list it here.') }}
      <a href="/app/sop-resource-type" target="_blank" class="text-ink-blue-3 hover:underline">{{ __('Resource types') }}</a>
    </p>

    <div v-else class="mt-5 flex max-w-[640px] flex-col gap-4">
      <div class="grid gap-3 sm:grid-cols-[12rem_minmax(0,1fr)]">
        <FormControl
          v-model="form.type"
          type="select"
          :label="__('Type')"
          :options="typeOptions"
          :placeholder="__('All types')"
        />
        <FormControl
          v-model="form.resource"
          type="select"
          :label="__('Resource')"
          :options="resourceOptions"
          :placeholder="resourceOptions.length ? __('Pick what to issue') : __('Nothing to issue yet')"
          :disabled="!resourceOptions.length"
        />
      </div>

      <div class="flex flex-col gap-1.5">
        <FormLabel :label="__('Employee')" />
        <Combobox
          :options="employeeOptions"
          :modelValue="form.employee"
          :loading="employees.loading"
          :placeholder="__('Search employees')"
          @update:query="(text) => employees.submit({ doctype: 'Employee', text, limit: 10 })"
          @update:modelValue="(value) => (form.employee = value)"
        />
      </div>

      <template v-if="picked?.is_consumable">
        <p v-if="!picked.item" class="text-sm text-ink-amber-6">
          {{ __('Set the Stock Item on this resource in the desk before issuing it.') }}
        </p>
        <div class="grid grid-cols-2 gap-3">
          <FormControl v-model="form.qty" type="number" :label="__('Quantity')" />
          <FormControl
            v-model="form.warehouse"
            type="select"
            :label="__('From warehouse')"
            :options="choices.data?.warehouses || []"
          />
        </div>
      </template>

      <div v-else-if="picked" class="flex flex-col gap-1.5">
        <FormLabel :label="__('Asset')" />
        <Combobox
          :options="assetOptions"
          :modelValue="form.asset"
          :loading="assets.loading"
          :placeholder="__('Search assets')"
          @update:query="(text) => assets.submit({ doctype: 'Asset', text, limit: 10 })"
          @update:modelValue="(value) => (form.asset = value)"
        />
      </div>

      <div class="flex justify-end">
        <Button
          variant="solid"
          :label="__('Issue')"
          :loading="issuing.loading"
          :disabled="!form.resource || !form.employee"
          @click="issue"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { Button, Combobox, ErrorMessage, FormControl, FormLabel, PageHeader, createResource, toast } from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import { translate as __ } from '@/translation'

const form = reactive({ type: '', resource: '', employee: null, qty: 1, warehouse: '', asset: null })

const choices = createResource({ url: 'sop.integrations.issue.choices', auto: true })
const employees = createResource({ url: 'sop.api.mentions.find' })
const assets = createResource({ url: 'sop.api.mentions.find' })
const issuing = createResource({
  url: 'sop.integrations.issue.issue',
  onSuccess(data) {
    toast.success(__('Issued — {0} {1}').format(data.doctype, data.name))
    window.open(data.url, '_blank')
    Object.assign(form, { employee: null, qty: 1, asset: null })
  },
})

const resources = computed(() => choices.data?.resources || [])
const picked = computed(() => resources.value.find((row) => row.name === form.resource))

const typeOptions = computed(() => [
  { label: __('All types'), value: '' },
  ...(choices.data?.types || []).map((row) => ({ label: row.name, value: row.name })),
])

const resourceOptions = computed(() =>
  resources.value
    .filter((row) => !form.type || row.resource_type === form.type)
    .map((row) => ({
      label: `${row.name}${form.type ? '' : ` · ${row.resource_type}`}${row.is_consumable ? '' : ` · ${__('kept')}`}`,
      value: row.name,
    })),
)

watch(
  () => form.type,
  () => {
    if (picked.value && form.type && picked.value.resource_type !== form.type) form.resource = ''
  },
)

const asOptions = (resource) =>
  (resource.data || []).map((row) => ({ label: row.label, value: row.name, description: row.hint }))

const employeeOptions = computed(() => asOptions(employees))
const assetOptions = computed(() => asOptions(assets))

const error = computed(() => choices.error?.messages?.[0] || issuing.error?.messages?.[0])

function issue() {
  issuing.submit({
    resource: form.resource,
    employee: form.employee,
    qty: form.qty,
    warehouse: form.warehouse || undefined,
    asset: form.asset || undefined,
  })
}
</script>
