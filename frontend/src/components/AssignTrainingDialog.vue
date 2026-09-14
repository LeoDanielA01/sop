<template>
  <Dialog v-model:open="open" title="Assign training" size="md">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="assign.error?.messages?.[0]" />

        <FormControl type="select" label="Procedure" :options="procedureOptions" v-model="sop" />

        <div class="grid gap-3 sm:grid-cols-2">
          <FormControl type="select" label="How they train" :options="METHODS" v-model="method" />
          <FormControl type="number" label="Due in (days)" v-model="dueDays" />
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

        <FormControl
          type="text"
          placeholder="Search people to train"
          v-model="query"
          @update:modelValue="people.reload()"
        />

        <div class="flex max-h-52 flex-col gap-1 overflow-y-auto">
          <Button
            v-for="person in candidates"
            :key="person.name"
            variant="ghost"
            class="!justify-start"
            @click="add(person)"
          >
            <Avatar :image="person.user_image" :label="person.full_name" size="sm" />
            <span class="ml-2 min-w-0 flex-1 truncate text-left">{{ person.full_name }}</span>
          </Button>

          <p
            v-if="!people.loading && !candidates.length"
            class="px-2 py-4 text-center text-sm text-ink-gray-5"
          >
            Nobody left to add.
          </p>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          label="Assign"
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
import { Avatar, Button, Dialog, ErrorMessage, FormControl, createResource } from 'frappe-ui'

const open = defineModel('open', { type: Boolean, default: false })

const props = defineProps({
  procedures: { type: Array, default: () => [] },
})

const emit = defineEmits(['assigned'])

const METHODS = ['Read & Understand', 'Classroom', 'On the Job', 'Assessment']

const sop = ref(null)
const method = ref('Read & Understand')
const dueDays = ref(14)
const query = ref('')
const chosen = ref([])

const procedureOptions = computed(() =>
  props.procedures.map((row) => ({ label: `${row.sop_no} · ${row.title}`, value: row.name })),
)

const people = createResource({
  url: 'sop.api.procedures.people',
  makeParams: () => ({ search: query.value }),
})

const candidates = computed(() => {
  const taken = new Set(chosen.value.map((row) => row.name))
  return (people.data || []).filter((person) => !taken.has(person.name))
})

const assign = createResource({
  url: 'sop.api.training.assign',
  onSuccess() {
    open.value = false
    emit('assigned')
  },
})

function add(person) {
  chosen.value.push(person)
  query.value = ''
  people.reload()
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
  query.value = ''
  chosen.value = []
  people.reload()
})
</script>
