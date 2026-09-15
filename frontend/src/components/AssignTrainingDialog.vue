<template>
  <Dialog v-model:open="open" :title="__('Assign training')" size="md">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="assign.error?.messages?.[0]" />

        <FormControl type="select" :label="__('Procedure')" :options="procedureOptions" v-model="sop" />

        <div class="grid gap-3 sm:grid-cols-2">
          <FormControl type="select" :label="__('How they train')" :options="METHODS" v-model="method" />
          <FormControl type="number" :label="__('Due in (days)')" v-model="dueDays" />
        </div>

        <div v-if="chosen.length" class="flex flex-wrap gap-1.5">
          <Button
            v-for="(person, index) in chosen"
            :key="person.name"
            variant="subtle"
            icon-right="lucide-x"
            :label="person.full_name"
            @click="chosen.splice(index, 1)"
          />
        </div>

        <Combobox
          :options="candidates"
          :modelValue="null"
          :loading="people.loading"
          :placeholder="__('Search people by name or email')"
          @update:modelValue="add"
          @update:query="lookup"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          :label="__('Assign')"
          :loading="assign.loading"
          :disabled="!sop || !chosen.length"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  Button,
  Combobox,
  Dialog,
  ErrorMessage,
  FormControl,
  createResource,
} from 'frappe-ui'

const open = defineModel('open', { type: Boolean, default: false })

const props = defineProps({
  procedures: { type: Array, default: () => [] },
})

const emit = defineEmits(['assigned'])

const METHODS = ['Read & Understand', 'Classroom', 'On the Job', 'Assessment']

const sop = ref(null)
const method = ref('Read & Understand')
const dueDays = ref(14)
const chosen = ref([])

const procedureOptions = computed(() =>
  props.procedures.map((row) => ({ label: `${row.sop_no} · ${row.title}`, value: row.name })),
)

const people = createResource({ url: 'sop.api.procedures.people' })

const candidates = computed(() => {
  const taken = new Set(chosen.value.map((row) => row.name))
  return (people.data || [])
    .filter((person) => !taken.has(person.name))
    .map((person) => ({
      label: person.full_name || person.name,
      value: person.name,
      description: person.name,
    }))
})

const assign = createResource({
  url: 'sop.api.training.assign',
  onSuccess() {
    open.value = false
    emit('assigned')
  },
})

function lookup(text) {
  people.submit({ search: text || '' })
}

function add(value) {
  const person = (people.data || []).find((row) => row.name === value)
  if (person) chosen.value.push(person)
}

function submit() {
  assign.submit({
    sop: sop.value,
    trainees: chosen.value.map((person) => person.name),
    method: method.value,
    due_days: dueDays.value,
  })
}

watch(open, (value) => {
  if (!value) return

  sop.value = props.procedures[0]?.name || null
  method.value = 'Read & Understand'
  dueDays.value = 14
  chosen.value = []
  people.submit({ search: '' })
})
</script>
