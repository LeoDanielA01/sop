<template>
  <PageHeader>
    <AppBreadcrumbs :tail="[{ label: __('Issue PPE') }]" />
  </PageHeader>

  <div class="mx-auto w-full max-w-[640px] px-3 pb-12 pt-4 sm:px-5">
    <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Issue PPE') }}</h1>
    <p class="mt-1 text-base text-ink-gray-6">
      {{ __('Consumable PPE is issued from stock. PPE a person keeps, like a respirator, is handed over as an asset.') }}
    </p>

    <ErrorMessage :message="error" class="mt-4" />

    <div class="mt-5 flex flex-col gap-4">
      <FormControl
        v-model="form.ppe"
        type="select"
        :label="__('PPE')"
        :options="ppeOptions"
        :placeholder="__('Pick the PPE')"
      />

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
          {{ __('Set the Stock Item on this PPE in the desk before issuing it.') }}
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
          :disabled="!form.ppe || !form.employee"
          @click="issue"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { Button, Combobox, ErrorMessage, FormControl, FormLabel, PageHeader, createResource, toast } from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import { translate as __ } from '@/translation'

const form = reactive({ ppe: '', employee: null, qty: 1, warehouse: '', asset: null })

const choices = createResource({ url: 'sop.integrations.ppe.choices', auto: true })
const employees = createResource({ url: 'sop.api.mentions.find' })
const assets = createResource({ url: 'sop.api.mentions.find' })
const issuing = createResource({
  url: 'sop.integrations.ppe.issue',
  onSuccess(data) {
    toast.success(__('Issued — {0} {1}').format(data.doctype, data.name))
    window.open(data.url, '_blank')
    Object.assign(form, { employee: null, qty: 1, asset: null })
  },
})

const picked = computed(() => (choices.data?.ppe || []).find((row) => row.name === form.ppe))

const ppeOptions = computed(() =>
  (choices.data?.ppe || []).map((row) => ({
    label: `${row.name}${row.standard ? ` · ${row.standard}` : ''}${row.is_consumable ? '' : ` · ${__('kept')}`}`,
    value: row.name,
  })),
)

const asOptions = (resource) =>
  (resource.data || []).map((row) => ({ label: row.label, value: row.name, description: row.hint }))

const employeeOptions = computed(() => asOptions(employees))
const assetOptions = computed(() => asOptions(assets))

const error = computed(() => choices.error?.messages?.[0] || issuing.error?.messages?.[0])

function issue() {
  issuing.submit({
    ppe: form.ppe,
    employee: form.employee,
    qty: form.qty,
    warehouse: form.warehouse || undefined,
    asset: form.asset || undefined,
  })
}
</script>
