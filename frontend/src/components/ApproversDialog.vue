<template>
  <Dialog v-model:open="open" title="Send for approval" size="md">
    <template #default>
      <div class="flex flex-col gap-4">
        <ErrorMessage :message="error" />

        <div class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <span class="text-sm text-ink-gray-5">Who signs it off</span>
            <Badge v-if="chosen.length" variant="subtle" size="sm">
              {{ chosen.length }} to sign
            </Badge>
          </div>

          <div
            v-if="chosen.length"
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
          >
            <div
              v-for="(row, index) in chosen"
              :key="row.approver"
              class="flex items-center gap-2.5 px-2.5 py-2"
            >
              <Avatar :image="row.approver_image" :label="row.approver_name" size="md" />

              <div class="min-w-0 flex-1">
                <div class="truncate text-base text-ink-gray-8">{{ row.approver_name }}</div>
                <div class="truncate text-sm text-ink-gray-5">{{ row.approver }}</div>
              </div>

              <Select v-model="row.approval_role" :options="ROLES" size="sm" class="w-36" />

              <Tooltip text="Take them off the list">
                <Button
                  variant="ghost"
                  size="sm"
                  icon="lucide-x"
                  label="Remove"
                  @click="chosen.splice(index, 1)"
                />
              </Tooltip>
            </div>
          </div>

          <p
            v-else
            class="rounded-lg border border-dashed border-outline-gray-2 px-3 py-5 text-center text-sm text-ink-gray-5"
          >
            Nobody chosen yet. Add whoever has to sign this off.
          </p>
        </div>

        <div class="flex flex-col gap-1.5">
          <div class="flex items-center gap-2 rounded-lg border border-outline-gray-2 px-2.5">
            <span class="lucide-search size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
            <TextInput
              class="w-full"
              variant="ghost"
              placeholder="Search people by name or email"
              v-model="query"
              @update:modelValue="lookup"
            />
          </div>

          <div class="flex max-h-52 flex-col gap-0.5 overflow-y-auto">
            <Button
              v-for="person in candidates"
              :key="person.name"
              variant="ghost"
              class="!h-auto w-full !justify-start !px-2 !py-1.5"
              @click="add(person)"
            >
              <Avatar :image="person.user_image" :label="person.full_name" size="sm" />
              <span class="ml-2.5 min-w-0 flex-1 text-left">
                <span class="block truncate text-base text-ink-gray-8">{{ person.full_name }}</span>
                <span class="block truncate text-sm text-ink-gray-5">{{ person.name }}</span>
              </span>
              <span class="lucide-plus size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
            </Button>

            <p
              v-if="!people.loading && !candidates.length"
              class="px-2 py-4 text-center text-sm text-ink-gray-5"
            >
              {{ query ? 'Nobody matches that.' : 'Everyone available is already on the list.' }}
            </p>
          </div>
        </div>

        <p class="flex items-start gap-2 text-sm text-ink-gray-5">
          <span class="lucide-info mt-0.5 size-4 shrink-0" aria-hidden="true" />
          Every person listed has to approve before the procedure comes into force.
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
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  Select,
  TextInput,
  Tooltip,
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
