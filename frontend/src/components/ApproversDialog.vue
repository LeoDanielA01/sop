<template>
  <Dialog v-model:open="open" title="Send for approval" size="md">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="error" />

        <div v-if="chosen.length" class="flex flex-col gap-1.5">
          <div
            v-for="(row, index) in chosen"
            :key="row.approver"
            class="flex items-center gap-2 rounded-md border border-outline-gray-2 px-2 py-1.5"
          >
            <Avatar :image="row.approver_image" :label="row.approver_name" size="sm" />
            <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
              {{ row.approver_name }}
            </span>
            <Select v-model="row.approval_role" :options="ROLES" />
            <Button
              variant="ghost"
              icon="lucide-x"
              label="Remove"
              @click="chosen.splice(index, 1)"
            />
          </div>
        </div>

        <FormControl
          type="text"
          placeholder="Search people to add"
          v-model="query"
          @update:modelValue="lookup"
        />

        <div class="flex max-h-56 flex-col gap-1 overflow-y-auto">
          <Button
            v-for="person in candidates"
            :key="person.name"
            variant="ghost"
            class="!justify-start"
            @click="add(person)"
          >
            <Avatar :image="person.user_image" :label="person.full_name" size="sm" />
            <span class="ml-2 min-w-0 flex-1 truncate text-left">{{ person.full_name }}</span>
            <span class="truncate text-sm text-ink-gray-4">{{ person.name }}</span>
          </Button>

          <p
            v-if="!people.loading && !candidates.length"
            class="px-2 py-4 text-center text-sm text-ink-gray-5"
          >
            Nobody left to add.
          </p>
        </div>

        <p class="text-sm text-ink-gray-5">
          Everyone listed has to approve before the procedure can come into force.
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          label="Send for approval"
          :loading="loading"
          :disabled="!chosen.length"
          @click="emit('submit', payload())"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  Avatar,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Select,
  createResource,
} from 'frappe-ui'

const open = defineModel('open', { type: Boolean, default: false })

const props = defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  current: { type: Array, default: () => [] },
})

const emit = defineEmits(['submit'])

const ROLES = ['Approver', 'Reviewer', 'Quality', 'Department Head']

const query = ref('')
const chosen = ref([])

const people = createResource({
  url: 'sop.api.procedures.people',
  makeParams: () => ({ search: query.value }),
})

const candidates = computed(() => {
  const taken = new Set(chosen.value.map((row) => row.approver))
  return (people.data || []).filter((person) => !taken.has(person.name))
})

function lookup() {
  people.reload()
}

function add(person) {
  chosen.value.push({
    approver: person.name,
    approver_name: person.full_name,
    approver_image: person.user_image,
    approval_role: 'Approver',
  })
  query.value = ''
  people.reload()
}

function payload() {
  return chosen.value.map((row) => ({
    approver: row.approver,
    approval_role: row.approval_role,
  }))
}

watch(open, (value) => {
  if (!value) return

  query.value = ''
  chosen.value = props.current.map((row) => ({
    approver: row.approver,
    approver_name: row.approver_name,
    approver_image: row.approver_image,
    approval_role: row.approval_role || 'Approver',
  }))
  people.reload()
})
</script>
