<template>
  <Dialog v-model:open="open" :title="__('Delete space?')" size="sm">
    <template #default>
      <p v-if="summary.loading && !info" class="text-base text-ink-gray-5">
        {{ __('Checking what is inside…') }}
      </p>

      <div v-else-if="info" class="flex flex-col gap-3">
        <p v-if="info.in_force" class="text-base text-ink-gray-7">
          {{
            __('{0} has {1} procedures in force. Retire them before deleting the space.').format(
              info.title,
              info.in_force,
            )
          }}
        </p>

        <p v-else-if="info.blocked_by_policy" class="text-base text-ink-gray-7">
          {{
            __(
              '{0} holds retired procedures, and your organisation keeps every record, so it cannot be deleted.',
            ).format(info.title)
          }}
        </p>

        <p v-else-if="!info.can_delete" class="text-base text-ink-gray-7">
          {{ __('Only an SOP manager can delete a space.') }}
        </p>

        <template v-else>
          <p class="text-base text-ink-gray-7">
            {{ __('{0} will be deleted, with everything in it:').format(info.title) }}
          </p>

          <ul v-if="lines.length" class="flex flex-col gap-1">
            <li
              v-for="line in lines"
              :key="line.label"
              class="flex items-center justify-between rounded-4 bg-surface-gray-1 px-3 py-1.5 text-base text-ink-gray-7"
            >
              <span>{{ line.label }}</span>
              <span class="tabular-nums text-ink-gray-8">{{ line.count }}</span>
            </li>
          </ul>
          <p v-else class="text-base text-ink-gray-5">{{ __('It is empty.') }}</p>

          <template v-if="info.needs_confirm">
            <p class="text-sm text-ink-red-3">
              {{
                __(
                  'The retired procedures and their history — revisions, sign-offs and training — will be gone for good.',
                )
              }}
            </p>
            <FormControl
              type="text"
              :label="__('Type {0} to confirm').format(info.code)"
              v-model="typed"
            />
          </template>
        </template>

        <ErrorMessage :message="summary.error?.messages?.[0] || remove.error?.messages?.[0]" />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="open = false" />
        <Button
          v-if="info?.can_delete"
          variant="solid"
          theme="red"
          :label="__('Delete space')"
          :loading="remove.loading"
          :disabled="info.needs_confirm && typed.trim() !== info.code"
          @click="remove.submit({ space: info.name, confirm: typed.trim() })"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dialog, ErrorMessage, FormControl, createResource, toast } from 'frappe-ui'
import { activeSpace, refreshCounts, setSpace, spacesResource } from '@/data/navigation'
import { processTree, setProcess } from '@/data/processes'
import { reloadProcedures } from '@/data/procedures'
import { useUI } from '@/stores/ui'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()
const ui = useUI()
const typed = ref('')

const open = computed({
  get: () => !!ui.removeSpace,
  set: (value) => {
    if (!value) ui.removeSpace = null
  },
})

const summary = createResource({ url: 'sop.api.removal.space_removal' })

const info = computed(() => summary.data || null)

const lines = computed(() => {
  const data = info.value || {}

  return [
    { label: __('Drafts that were never in force'), count: data.drafts },
    { label: __('Retired procedures'), count: data.history },
    { label: __('Processes'), count: data.processes },
    { label: __('Training rules'), count: data.rules },
  ].filter((line) => line.count)
})

const remove = createResource({
  url: 'sop.api.removal.delete_space',
  onSuccess() {
    const name = info.value.name

    ui.removeSpace = null

    if (activeSpace.value === name) {
      setSpace(null)
      setProcess(null)
    }

    spacesResource.reload()
    processTree.reload()
    refreshCounts()
    reloadProcedures()
    toast.success(__('Space deleted'))

    if (route.query.space === name) router.push('/')
  },
})

watch(
  () => ui.removeSpace,
  (value) => {
    typed.value = ''
    if (value) summary.submit({ space: value.name })
  },
)
</script>
