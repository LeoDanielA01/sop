<template>
  <Dialog v-model:open="open" :title="draft.name ? 'Edit session' : 'Plan a session'" size="lg">
    <template #default>
      <div class="flex flex-col gap-4">
        <ErrorMessage :message="save.error?.messages?.[0]" />

        <div class="grid gap-3 sm:grid-cols-2">
          <FormControl
            type="text"
            label="What it covers"
            placeholder="Line clearance, morning shift"
            v-model="draft.title"
          />
          <FormControl type="datetime-local" label="When" v-model="draft.scheduled_on" />
          <FormControl
            type="select"
            label="How it runs"
            :options="METHODS"
            v-model="draft.method"
          />
          <FormControl type="text" label="Where" placeholder="Line 2" v-model="draft.location" />
        </div>

        <div class="flex flex-col gap-2">
          <span class="text-sm text-ink-gray-5">Procedures covered</span>

          <div v-if="draft.procedures.length" class="flex flex-wrap gap-1.5">
            <Button
              v-for="(row, index) in draft.procedures"
              :key="row.sop"
              variant="subtle"
              icon-right="lucide-x"
              :label="row.title"
              @click="draft.procedures.splice(index, 1)"
            />
          </div>

          <Select
            :options="procedureChoices"
            :modelValue="''"
            placeholder="Add a procedure"
            @update:modelValue="addProcedure"
          />
        </div>

        <div class="flex flex-col gap-2">
          <span class="text-sm text-ink-gray-5">Who attends</span>

          <div v-if="draft.attendees.length" class="flex flex-wrap gap-1.5">
            <Button
              v-for="(person, index) in draft.attendees"
              :key="person.user"
              variant="subtle"
              icon-right="lucide-x"
              :label="person.full_name"
              @click="draft.attendees.splice(index, 1)"
            />
          </div>

          <div class="flex items-center gap-2 rounded-lg border border-outline-gray-2 px-2.5">
            <span class="lucide-search size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
            <TextInput
              class="w-full"
              variant="ghost"
              placeholder="Search people by name or email"
              v-model="query"
              @update:modelValue="people.reload()"
            />
          </div>

          <div v-if="candidates.length" class="flex max-h-40 flex-col gap-0.5 overflow-y-auto">
            <Button
              v-for="person in candidates"
              :key="person.name"
              variant="ghost"
              class="!h-auto w-full !justify-start !px-2 !py-1.5"
              @click="addPerson(person)"
            >
              <Avatar :image="person.user_image" :label="person.full_name" size="sm" />
              <span class="ml-2.5 min-w-0 flex-1 text-left">
                <span class="block truncate text-base text-ink-gray-8">{{ person.full_name }}</span>
                <span class="block truncate text-sm text-ink-gray-5">{{ person.name }}</span>
              </span>
              <span class="lucide-plus size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
            </Button>
          </div>
        </div>

        <FormControl
          type="textarea"
          label="Notes"
          placeholder="What the trainer should cover"
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
import { computed, reactive, ref, watch } from 'vue'
import {
  Avatar,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Select,
  TextInput,
  createResource,
} from 'frappe-ui'

const open = defineModel('open', { type: Boolean, default: false })

const props = defineProps({
  session: { type: Object, default: null },
})

const emit = defineEmits(['saved'])

const METHODS = ['Classroom', 'On the Job', 'Assessment']

const query = ref('')

const draft = reactive({
  name: null,
  title: '',
  scheduled_on: '',
  method: 'Classroom',
  location: '',
  notes: '',
  procedures: [],
  attendees: [],
})

const options = createResource({ url: 'sop.api.sessions.procedure_options', auto: true })

const people = createResource({
  url: 'sop.api.procedures.people',
  makeParams: () => ({ search: query.value }),
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
  return [
    { label: 'Add a procedure', value: '' },
    ...(options.data || []).filter((row) => !taken.has(row.value)),
  ]
})

const candidates = computed(() => {
  const taken = new Set(draft.attendees.map((row) => row.user))
  return (people.data || []).filter((person) => !taken.has(person.name))
})

function addProcedure(value) {
  const row = (options.data || []).find((option) => option.value === value)
  if (row) draft.procedures.push({ sop: row.value, title: row.label })
}

function addPerson(person) {
  draft.attendees.push({ user: person.name, full_name: person.full_name })
  query.value = ''
  people.reload()
}

function submit() {
  save.submit({
    name: draft.name,
    title: draft.title,
    scheduled_on: draft.scheduled_on || null,
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

  Object.assign(draft, {
    name: source?.name || null,
    title: source?.title || '',
    scheduled_on: source?.scheduled_on || '',
    method: source?.method || 'Classroom',
    location: source?.location || '',
    notes: source?.notes || '',
    procedures: source ? source.procedures.map((row) => ({ ...row })) : [],
    attendees: source ? source.attendees.map((row) => ({ ...row })) : [],
  })

  query.value = ''
  people.reload()
  options.reload()
})
</script>
