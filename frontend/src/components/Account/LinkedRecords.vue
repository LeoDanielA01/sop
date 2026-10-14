<template>
  <div class="pt-4">
    <ErrorMessage :message="error" class="mb-3" />

    <div class="flex flex-col gap-3">
      <div v-for="(row, index) in rows" :key="index" class="rounded-4 border border-outline-gray-2">
        <div class="flex flex-wrap items-center gap-2 border-b border-outline-gray-1 px-3 py-2.5">
          <span :class="row.icon || 'lucide-file-text'" class="size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          <Combobox
            v-if="!row.reference_doctype"
            class="w-60"
            :options="typeOptions"
            :modelValue="null"
            :loading="types.loading"
            :placeholder="__('Pick a record type')"
            @update:query="(text) => types.submit({ search: text, limit: 20 })"
            @update:modelValue="(value) => setType(row, value)"
          />
          <span v-else class="text-base font-medium text-ink-gray-8">{{ row.reference_doctype }}</span>

          <TextInput v-model="row.label" class="w-36" :placeholder="__('Label')" :aria-label="__('Label')" />
          <TextInput v-model="row.icon" class="w-44" placeholder="lucide-flask-conical" :aria-label="__('Icon')" />

          <label class="ml-auto flex items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="row.in_safety" />
            {{ __('Safety box') }}
          </label>
          <Button variant="ghost" icon="lucide-trash-2" :label="__('Remove')" @click="rows.splice(index, 1)" />
        </div>

        <div v-if="row.reference_doctype" class="px-3 py-2.5">
          <p class="mb-2 text-sm text-ink-gray-5">
            {{ __('Fields to show, in the order you pick them. None picked lets the app choose.') }}
          </p>
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="field in fieldsFor(row.reference_doctype)"
              :key="field.value"
              type="button"
              class="rounded-3 border px-2 py-0.5 text-sm"
              :class="
                row.fields_to_show.includes(field.value)
                  ? 'border-outline-gray-4 bg-surface-gray-3 text-ink-gray-9'
                  : 'border-outline-gray-2 text-ink-gray-6 hover:border-outline-gray-3'
              "
              @click="toggle(row, field.value)"
            >
              <span v-if="row.fields_to_show.includes(field.value)" class="mr-1 text-ink-gray-5">
                {{ row.fields_to_show.indexOf(field.value) + 1 }}
              </span>
              {{ field.label }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <p v-if="!rows.length" class="py-6 text-center text-base text-ink-gray-5">
      {{ __('No record types yet. Add the ones your procedures mention, like Chemical, PPE, Item or Asset.') }}
    </p>

    <div class="mt-4 flex items-center gap-2">
      <Button icon-left="lucide-plus" :label="__('Add record type')" @click="add" />
      <Button
        variant="solid"
        class="ml-auto"
        :label="__('Save')"
        :loading="saving.loading"
        :disabled="!dirty"
        @click="save"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Combobox, ErrorMessage, Switch, TextInput, call, createResource, toast } from 'frappe-ui'
import { translate as __ } from '@/translation'

const props = defineProps({
  value: { type: Array, default: () => [] },
})
const emit = defineEmits(['saved'])

const rows = ref([])
const fields = reactive({})
const failed = ref('')

const types = createResource({ url: 'sop.api.mentions.doctypes' })
const saving = createResource({
  url: 'sop.api.settings.save',
  onSuccess(data) {
    toast.success(__('Linked records saved'))
    emit('saved', data)
  },
})

const typeOptions = computed(() =>
  (types.data || [])
    .filter((name) => !rows.value.some((row) => row.reference_doctype === name))
    .map((name) => ({ label: name, value: name })),
)

const error = computed(() => failed.value || saving.error?.messages?.[0])

const snapshot = (list) =>
  JSON.stringify(list.map((row) => ({ ...row, in_safety: row.in_safety ? 1 : 0 })))

const dirty = computed(() => snapshot(rows.value) !== snapshot(normalise(props.value)))

function normalise(list) {
  return (list || []).map((row) => ({
    reference_doctype: row.reference_doctype,
    label: row.label || '',
    icon: row.icon || '',
    fields_to_show: [...(row.fields_to_show || [])],
    in_safety: !!row.in_safety,
  }))
}

function fieldsFor(doctype) {
  if (!(doctype in fields)) {
    fields[doctype] = []
    call('sop.api.settings.fields_of', { doctype })
      .then((data) => (fields[doctype] = data || []))
      .catch((err) => (failed.value = err?.messages?.[0] || err?.message))
  }
  return fields[doctype]
}

function setType(row, value) {
  if (!value) return
  row.reference_doctype = value
  row.label = row.label || value.replace(/^SOP /, '')
}

function toggle(row, fieldname) {
  const at = row.fields_to_show.indexOf(fieldname)
  if (at >= 0) row.fields_to_show.splice(at, 1)
  else row.fields_to_show.push(fieldname)
}

function add() {
  rows.value.push({ reference_doctype: '', label: '', icon: '', fields_to_show: [], in_safety: false })
  types.submit({ limit: 20 })
}

function save() {
  failed.value = ''
  saving.submit({
    values: {
      record_types: rows.value
        .filter((row) => row.reference_doctype)
        .map((row) => ({ ...row, in_safety: row.in_safety ? 1 : 0 })),
    },
  })
}

watch(
  () => props.value,
  (value) => (rows.value = normalise(value)),
  { immediate: true },
)
</script>
