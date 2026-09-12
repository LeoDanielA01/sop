<template>
  <Dialog v-model="open" :options="{ title: 'New process', size: 'sm' }">
    <template #body-content>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="createProcess.error?.messages?.[0]" />

        <p class="text-sm text-ink-gray-5">
          <template v-if="state.parentTitle">Inside {{ state.parentTitle }}.</template>
          <template v-else>A top-level process in this space.</template>
          Procedures can sit on any process, at any depth.
        </p>

        <FormControl type="text" label="Name" placeholder="Mixing and blending" v-model="title" />
        <FormControl
          type="number"
          label="Sequence"
          description="Order among its siblings — lower comes first"
          v-model="sequence"
        />
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        label="Add process"
        :loading="createProcess.loading"
        :disabled="!title"
        @click="submit"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { createProcess } from '@/data/processes'
import { processDialog } from '@/data/ui'

const state = processDialog

const open = computed({
  get: () => state.value.open,
  set: (value) => (state.value = { ...state.value, open: value }),
})

const title = ref('')
const sequence = ref(10)

function submit() {
  createProcess.submit(
    {
      title: title.value,
      space: state.value.space,
      parent: state.value.parent,
      sequence: sequence.value,
    },
    { onSuccess: () => (open.value = false) },
  )
}

watch(open, (value) => {
  if (value) {
    title.value = ''
    sequence.value = 10
    createProcess.error = null
  }
})
</script>
