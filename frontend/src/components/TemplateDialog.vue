<template>
  <Dialog v-model:open="open" title="Start from a template" size="sm">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="applyTemplate.error?.messages?.[0]" />

        <p class="text-sm text-ink-gray-5">
          Fills {{ spaceTitle }} with a ready-made process tree. Anything already there is left
          alone, so it is safe to run twice.
        </p>

        <FormControl type="select" label="Template" :options="options" v-model="template" />
        <p v-if="note" class="text-sm text-ink-gray-6">{{ note }}</p>

        <FormControl
          type="checkbox"
          label="Also start a draft procedure on every process"
          v-model="withDrafts"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          label="Add the processes"
          :loading="applyTemplate.loading"
          :disabled="!template"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { applyTemplate, templates } from '@/data/processes'
import { activeSpace, spaces } from '@/data/navigation'
import { templateDialog } from '@/data/ui'

const open = templateDialog

const template = ref('')
const withDrafts = ref(false)

const options = computed(() =>
  (templates.data || []).map((row) => ({ label: row.title, value: row.key })),
)

const note = computed(
  () => (templates.data || []).find((row) => row.key === template.value)?.description || '',
)

const spaceTitle = computed(
  () => spaces.value.find((row) => row.name === activeSpace.value)?.title || 'this space',
)

function submit() {
  applyTemplate.submit(
    {
      space: activeSpace.value,
      template: template.value,
      with_drafts: withDrafts.value ? 1 : 0,
    },
    { onSuccess: () => (open.value = false) },
  )
}

watch(open, (value) => {
  if (!value) return

  template.value = templates.data?.[0]?.key || ''
  withDrafts.value = false
  applyTemplate.error = null
})
</script>
