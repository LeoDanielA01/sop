<template>
  <Dialog
    v-model:open="open"
    :title="purge ? __('Delete permanently?') : __('Delete this draft?')"
    size="sm"
  >
    <template #default>
      <div class="flex flex-col gap-3">
        <p class="text-base text-ink-gray-7">{{ message }}</p>

        <FormControl
          v-if="purge"
          type="text"
          :label="__('Type {0} to confirm').format(target.sop_no)"
          v-model="typed"
        />

        <ErrorMessage :message="running.error?.messages?.[0]" />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="open = false" />
        <Button
          variant="solid"
          theme="red"
          :label="purge ? __('Delete permanently') : __('Delete draft')"
          :loading="running.loading"
          :disabled="purge && typed.trim() !== target.sop_no"
          @click="confirm"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dialog, ErrorMessage, FormControl, createResource, toast } from 'frappe-ui'
import { refreshCounts } from '@/data/navigation'
import { processTree } from '@/data/processes'
import { reloadProcedures } from '@/data/procedures'
import { useUI } from '@/stores/ui'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()
const ui = useUI()
const typed = ref('')

const target = computed(() => ui.removeProcedure || {})
const purge = computed(() => target.value.mode === 'purge')

const open = computed({
  get: () => !!ui.removeProcedure,
  set: (value) => {
    if (!value) ui.removeProcedure = null
  },
})

const message = computed(() =>
  purge.value
    ? __(
        '{0} and everything recorded against it — revisions, sign-offs and training — will be gone for good. Auditors will not be able to see it afterwards.',
      ).format(target.value.sop_no)
    : __('{0} was never in force, so nothing depends on it. Its review comments go with it.').format(
        target.value.sop_no,
      ),
)

function done() {
  const name = target.value.name

  ui.removeProcedure = null
  reloadProcedures()
  refreshCounts()
  processTree.reload()
  toast.success(__('Deleted'))

  if (route.params.name === name) router.push('/')
}

const draft = createResource({ url: 'sop.api.removal.delete_draft', onSuccess: done })
const forever = createResource({ url: 'sop.api.removal.purge_procedure', onSuccess: done })

const running = computed(() => (purge.value ? forever : draft))

function confirm() {
  if (purge.value) {
    forever.submit({ sop: target.value.name, confirm: typed.value.trim() })
    return
  }

  draft.submit({ sop: target.value.name })
}

watch(open, (value) => {
  if (value) typed.value = ''
})
</script>
