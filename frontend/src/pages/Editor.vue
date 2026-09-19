<template>
  <PageHeader>
    <div class="flex min-w-0 items-center gap-2">
      <AppBreadcrumbs
        :tail="[
          { label: isNew ? 'New procedure' : draft.sop_no, route: crumbRoute },
          { label: 'Edit' },
        ]"
      />
      <Badge variant="subtle" size="sm">{{ draft.status }}</Badge>
      <SaveIndicator
        :loading="save.loading"
        :dirty="dirty"
        :saved-at="savedAt"
        :error="save.error?.messages?.[0] || ''"
        :autosave="!!preferences.autosave"
        @retry="submit"
      />
    </div>

    <div class="flex items-center gap-2">
      <Button
        v-if="!isNew"
        variant="ghost"
        :label="__('Preview')"
        icon-left="lucide-eye"
        @click="router.push(`/${route.params.name}`)"
      />
      <Button
        variant="solid"
        :label="__('Save draft')"
        :loading="save.loading"
        :disabled="!draft.title || !spaces.length"
        @click="submit"
      />
    </div>
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[820px] px-3 pb-16 sm:px-5">
    <div
      v-if="!spaces.length"
      class="mt-12 flex flex-col items-center gap-3 px-6 text-center text-base text-ink-gray-5"
    >
      <span>
        {{ __('A procedure needs a space to live in — its code becomes the procedure number.') }}
      </span>
      <Button
        variant="solid"
        icon-left="lucide-plus"
        :label="__('Create a space')"
        @click="ui.spaceDialog = true"
      />
    </div>

    <template v-else>
    <div class="mb-4 flex flex-col gap-3">
      <FormControl
        type="text"
        size="lg"
        :placeholder="__('Title what this procedure covers')"
        v-model="draft.title"
      />
      <div class="grid gap-3 sm:grid-cols-2">
        <FormControl type="select" :label="__('Space')" :options="spaceOptions" v-model="draft.space" />
        <FormControl
          type="select"
          :label="__('Process')"
          :options="processOptions"
          v-model="draft.process"
        />
      </div>

      <FormControl
        type="text"
        :label="__('Summary')"
        :placeholder="__('One line, shown in search results')"
        v-model="draft.summary"
      />
    </div>

    <ProcedureEditor v-model="draft.content" />
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import {
  Badge,
  Button,
  FormControl,
  PageHeader,
  createResource,
} from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import SaveIndicator from '@/components/Editor/SaveIndicator.vue'
import ProcedureEditor from '@/components/Editor/ProcedureEditor.vue'
import { activeSpace, spaces } from '@/data/navigation'
import { preferences } from '@/data/preferences'
import { activeProcess, flatten } from '@/data/processes'
import { useUI } from '@/stores/ui'

const route = useRoute()
const router = useRouter()
const ui = useUI()

const draft = reactive({
  title: '',
  summary: '',
  content: '',
  space: null,
  process: null,
  sop_no: null,
  status: 'Draft',
})

const dirty = ref(false)
const savedAt = ref(null)
let loading = false

const isNew = computed(() => !route.params.name)
const crumbRoute = computed(() => (isNew.value ? '/' : `/${route.params.name}`))
const spaceOptions = computed(() => spaces.value.map((s) => ({ label: s.title, value: s.name })))

const spaceProcesses = createResource({
  url: 'sop.api.processes.tree',
  makeParams: () => ({ space: draft.space }),
})

const processOptions = computed(() => [
  { label: 'Not filed under a process', value: null },
  ...flatten(spaceProcesses.data || []).map((node) => ({
    label: `${'— '.repeat(node.depth)}${node.title}`,
    value: node.name,
  })),
])

const load = createResource({
  url: 'sop.api.procedures.get_procedure',
  onSuccess(doc) {
    loading = true
    Object.assign(draft, {
      title: doc.title,
      summary: doc.summary,
      content: doc.content,
      space: doc.space,
      process: doc.process,
      sop_no: doc.sop_no,
      status: doc.status,
    })
    dirty.value = false
    loading = false
  },
})

const save = createResource({
  url: 'sop.api.procedures.save_draft',
  onSuccess(doc) {
    dirty.value = false
    savedAt.value = new Date()
    draft.sop_no = doc.sop_no
    draft.status = doc.status
    if (isNew.value) router.replace(`/${doc.name}/edit`)
  },
})

function submit() {
  save.submit({
    name: route.params.name,
    space: draft.space || activeSpace.value,
    title: draft.title,
    summary: draft.summary,
    content: draft.content,
    process: draft.process || undefined,
  })
}

let timer = null
watch(
  () => [draft.title, draft.summary, draft.content],
  () => {
    if (loading) return

    dirty.value = true
    clearTimeout(timer)

    if (preferences.autosave && draft.title) timer = setTimeout(submit, 2000)
  },
)

onMounted(() => {
  if (!isNew.value) {
    load.submit({ name: route.params.name })
    return
  }

  draft.space = activeSpace.value || spaces.value[0]?.name
  draft.process = activeProcess.value
})

watch(spaces, (list) => {
  if (isNew.value && !draft.space) draft.space = activeSpace.value || list[0]?.name
})

watch(
  () => draft.space,
  (space) => {
    if (!space) return

    spaceProcesses.submit({ space }).then(() => {
      const names = flatten(spaceProcesses.data || []).map((node) => node.name)
      if (draft.process && !names.includes(draft.process)) draft.process = null
    })
  },
  { immediate: true },
)

function onKeydown(event) {
  if (!(event.metaKey || event.ctrlKey) || event.key.toLowerCase() !== 's') return

  event.preventDefault()
  if (draft.title && dirty.value) submit()
}

function onBeforeUnload(event) {
  if (!dirty.value) return

  event.preventDefault()
  event.returnValue = ''
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('beforeunload', onBeforeUnload)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('beforeunload', onBeforeUnload)
})

onBeforeRouteLeave(() => {
  clearTimeout(timer)

  if (preferences.autosave && dirty.value && draft.title) submit()
})
</script>
