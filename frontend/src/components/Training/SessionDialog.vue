<template>
  <Dialog v-model:open="open" :title="draft.name ? 'Edit session' : 'Plan a session'" size="lg">
    <template #default>
      <div class="flex flex-col gap-4">
        <ErrorMessage :message="save.error?.messages?.[0]" />

        <FormControl
          type="text"
          :label="__('What it covers')"
          :placeholder="__('Line clearance, morning shift')"
          v-model="draft.title"
        />

        <div class="grid gap-3 sm:grid-cols-2">
          <div class="flex flex-col gap-1.5">
            <FormLabel :label="__('Date')" />
            <DatePicker v-model="draft.date" :placeholder="__('Pick a day')" />
          </div>

          <div class="flex flex-col gap-1.5">
            <FormLabel :label="__('Time')" />
            <TimePicker v-model="draft.time" :placeholder="__('Pick a time')" />
          </div>

          <FormControl type="select" :label="__('How it runs')" :options="METHODS" v-model="draft.method" />
          <FormControl type="text" :label="__('Where')" :placeholder="__('Line 2')" v-model="draft.location" />
        </div>

        <div class="flex flex-col gap-1.5">
          <FormLabel :label="__('Procedures covered')" />

          <Combobox
            :options="procedureChoices"
            :modelValue="null"
            :loading="options.loading"
            :placeholder="__('Search procedures')"
            @update:modelValue="addProcedure"
          />

          <div v-if="draft.procedures.length" class="flex flex-wrap gap-1.5 pt-1">
            <Button
              v-for="(row, index) in draft.procedures"
              :key="row.sop"
              variant="subtle"
              size="sm"
              icon-right="lucide-x"
              :label="row.title"
              @click="draft.procedures.splice(index, 1)"
            />
          </div>
        </div>

        <div class="flex flex-col gap-1.5">
          <FormLabel :label="__('Who attends')" />

          <Combobox
            :options="peopleChoices"
            :modelValue="null"
            :loading="people.loading"
            :placeholder="__('Search people by name or email')"
            @update:modelValue="addPerson"
            @update:query="lookup"
          />

          <div v-if="draft.attendees.length" class="flex flex-wrap gap-1.5 pt-1">
            <Button
              v-for="(person, index) in draft.attendees"
              :key="person.user"
              variant="subtle"
              size="sm"
              icon-right="lucide-x"
              :label="person.full_name"
              @click="draft.attendees.splice(index, 1)"
            />
          </div>
        </div>

        <FormControl
          type="textarea"
          :label="__('Notes')"
          :placeholder="__('What the trainer should cover')"
          v-model="draft.notes"
        />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          :label="draft.name ? 'Save session' : 'Plan it'"
          :loading="save.loading"
          :disabled="!draft.title"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import {
  Button,
  Combobox,
  DatePicker,
  Dialog,
  ErrorMessage,
  FormControl,
  FormLabel,
  TimePicker,
  createResource,
} from 'frappe-ui'

const open = defineModel('open', { type: Boolean, default: false })

const props = defineProps({
  session: { type: Object, default: null },
})

const emit = defineEmits(['saved'])

const METHODS = ['Classroom', 'On the Job', 'Assessment']

const draft = reactive({
  name: null,
  title: '',
  date: '',
  time: '',
  method: 'Classroom',
  location: '',
  notes: '',
  procedures: [],
  attendees: [],
})

const options = createResource({ url: 'sop.api.sessions.procedure_options', auto: true })

const people = createResource({
  url: 'sop.api.procedures.people',
  auto: true,
})

const save = createResource({
  url: 'sop.api.sessions.save_session',
  onSuccess(data) {
    open.value = false
    emit('saved', data.name)
  },
})

const procedureChoices = computed(() => {
  const taken = new Set(draft.procedures.map((row) => row.sop))
  return (options.data || []).filter((row) => !taken.has(row.value))
})

const peopleChoices = computed(() => {
  const taken = new Set(draft.attendees.map((row) => row.user))
  return (people.data || [])
    .filter((person) => !taken.has(person.name))
    .map((person) => ({
      label: person.full_name || person.name,
      value: person.name,
      description: person.name,
    }))
})

function lookup(query) {
  people.submit({ search: query || '' })
}

function addProcedure(value) {
  const row = (options.data || []).find((option) => option.value === value)
  if (row) draft.procedures.push({ sop: row.value, title: row.label })
}

function addPerson(value) {
  const person = (people.data || []).find((row) => row.name === value)
  if (person) {
    draft.attendees.push({ user: person.name, full_name: person.full_name || person.name })
  }
}

function scheduledOn() {
  if (!draft.date) return null

  const time = draft.time ? (draft.time.length === 5 ? `${draft.time}:00` : draft.time) : '00:00:00'
  return `${draft.date} ${time}`
}

function submit() {
  save.submit({
    name: draft.name,
    title: draft.title,
    scheduled_on: scheduledOn(),
    method: draft.method,
    location: draft.location,
    notes: draft.notes,
    procedures: draft.procedures.map((row) => row.sop),
    attendees: draft.attendees.map((row) => row.user),
  })
}

watch(open, (value) => {
  if (!value) return

  const source = props.session
  const [date, time] = String(source?.scheduled_on || '').split(' ')

  Object.assign(draft, {
    name: source?.name || null,
    title: source?.title || '',
    date: date || '',
    time: time ? time.slice(0, 5) : '',
    method: source?.method || 'Classroom',
    location: source?.location || '',
    notes: source?.notes || '',
    procedures: source ? source.procedures.map((row) => ({ ...row })) : [],
    attendees: source ? source.attendees.map((row) => ({ ...row })) : [],
  })

  people.submit({ search: '' })
  options.reload()
})
</script>
