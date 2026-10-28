<template>
  <Combobox
    :options="choices"
    :modelValue="modelValue"
    :loading="lookup.loading"
    :disabled="!doctype"
    :placeholder="placeholder || __('Search {0}').format(doctype || __('records'))"
    @update:query="search"
    @update:modelValue="(value) => emit('update:modelValue', value)"
  />
</template>

<script setup>
import { computed, watch } from 'vue'
import { Combobox, createResource, debounce } from 'frappe-ui'
import { translate as __ } from '@/translation'

const props = defineProps({
  doctype: { type: String, default: '' },
  modelValue: { type: String, default: null },
  placeholder: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const lookup = createResource({ url: 'sop.api.mentions.find' })

const choices = computed(() => {
  const rows = (lookup.data || []).map((row) => ({
    label: row.label && row.label !== row.name ? `${row.label} (${row.name})` : row.name,
    value: row.name,
  }))
  if (props.modelValue && !rows.some((row) => row.value === props.modelValue)) {
    rows.unshift({ label: props.modelValue, value: props.modelValue })
  }
  return rows
})

const search = debounce((text) => {
  if (props.doctype) lookup.submit({ doctype: props.doctype, text, limit: 15 })
}, 250)

watch(
  () => props.doctype,
  (value) => value && lookup.submit({ doctype: value, text: '', limit: 15 }),
  { immediate: true },
)
</script>
