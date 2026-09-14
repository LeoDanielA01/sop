<template>
  <Dialog v-model:open="open" title="New space" size="sm">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="createSpace.error?.messages?.[0]" />

        <FormControl
          type="text"
          label="Name"
          placeholder="Quality Assurance"
          v-model="title"
          @update:modelValue="touchCode"
        />
        <FormControl
          type="text"
          label="Code"
          :description="`Procedures here are numbered SOP-${code || 'CODE'}-0001`"
          :modelValue="code"
          @update:modelValue="setCode"
        />
        <FormControl
          type="select"
          label="Who can see it"
          :options="['Public', 'Team', 'Private']"
          v-model="visibility"
        />
        <FormControl type="number" label="Review every (months)" v-model="reviewMonths" />

        <FormControl
          type="select"
          label="Start from"
          :options="templateOptions"
          v-model="template"
        />

        <div v-if="template" class="flex flex-col gap-2 rounded-4 bg-surface-gray-1 px-3 py-2.5">
          <p class="text-sm text-ink-gray-6">{{ templateNote }}</p>
          <FormControl
            type="checkbox"
            label="Also start a draft procedure on every process"
            v-model="withDrafts"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          label="Create space"
          :loading="createSpace.loading"
          :disabled="!title"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { createSpace } from '@/data/navigation'
import { processTree, templates } from '@/data/processes'

const open = defineModel('open', { type: Boolean, default: false })

const title = ref('')
const code = ref('')
const visibility = ref('Public')
const reviewMonths = ref(12)
const edited = ref(false)
const template = ref('')
const withDrafts = ref(false)

const templateOptions = computed(() => [
  { label: 'An empty space', value: '' },
  ...(templates.data || []).map((row) => ({ label: row.title, value: row.key })),
])

const templateNote = computed(
  () => (templates.data || []).find((row) => row.key === template.value)?.description || '',
)

function touchCode() {
  if (edited.value) return

  const words = title.value.split(/[^A-Za-z0-9]+/).filter(Boolean)
  const initials = words.map((word) => word[0]).join('')
  code.value = (words.length > 1 ? initials.slice(0, 4) : (words[0] || '').slice(0, 3)).toUpperCase()
}

function setCode(value) {
  edited.value = true
  code.value = (value || '')
    .toUpperCase()
    .replace(/[^A-Z0-9-]/g, '')
    .slice(0, 10)
}

function submit() {
  createSpace.submit(
    {
      title: title.value,
      space_code: code.value,
      visibility: visibility.value,
      review_interval_months: reviewMonths.value,
      template: template.value || undefined,
      with_drafts: withDrafts.value ? 1 : 0,
    },
    {
      onSuccess: () => {
        open.value = false
        processTree.reload()
      },
    },
  )
}

watch(open, (value) => {
  if (value) return

  title.value = ''
  code.value = ''
  visibility.value = 'Public'
  reviewMonths.value = 12
  edited.value = false
  template.value = ''
  withDrafts.value = false
  createSpace.error = null
})
</script>
