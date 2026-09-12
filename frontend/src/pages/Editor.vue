<template>
  <PageHeader>
    <div class="flex min-w-0 items-center gap-2">
      <PageHeaderTitle>{{ isNew ? 'New procedure' : draft.sop_no }}</PageHeaderTitle>
      <Badge variant="subtle" size="sm">{{ draft.status }}</Badge>
      <span class="text-sm text-ink-gray-4">
        <template v-if="save.loading">Saving…</template>
        <template v-else-if="dirty">Unsaved</template>
        <template v-else-if="savedAt">Saved</template>
      </span>
    </div>

    <div class="flex items-center gap-2">
      <Button
        v-if="!isNew"
        variant="ghost"
        label="Preview"
        icon-left="lucide-eye"
        @click="router.push(`/${route.params.name}`)"
      />
      <Button
        variant="solid"
        label="Save draft"
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
        A procedure needs a space to live in — its code becomes the procedure number.
      </span>
      <Button
        variant="solid"
        icon-left="lucide-plus"
        label="Create a space"
        @click="spaceDialog = true"
      />
    </div>

    <template v-else>
    <ErrorMessage :message="save.error?.messages?.[0]" class="mb-3" />

    <div class="mb-4 flex flex-col gap-3">
      <FormControl
        type="text"
        size="lg"
        placeholder="Title — what this procedure covers"
        v-model="draft.title"
      />
      <div class="grid gap-3 sm:grid-cols-2">
        <FormControl type="select" label="Space" :options="spaceOptions" v-model="draft.space" />
        <FormControl
          type="select"
          label="Process"
          :options="processOptions"
          v-model="draft.process"
        />
      </div>

      <FormControl
        type="text"
        label="Summary"
        placeholder="One line, shown in search results"
        v-model="draft.summary"
      />
    </div>

    <ProcedureEditor v-model="draft.content" />
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Badge,
  Button,
  ErrorMessage,
  FormControl,
  PageHeader,
  PageHeaderTitle,
  createResource,
} from 'frappe-ui'
import ProcedureEditor from '@/components/editor/ProcedureEditor.vue'
import { activeSpace, spaces } from '@/data/navigation'
import { activeProcess, flatten, processes } from '@/data/processes'
import { spaceDialog } from '@/data/ui'

const route = useRoute()
const router = useRouter()

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
const spaceOptions = computed(() => spaces.value.map((s) => ({ label: s.title, value: s.name })))

const processOptions = computed(() => [
  { label: 'Not filed under a process', value: null },
  ...flatten(processes.value).map((node) => ({
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
    if (draft.title) timer = setTimeout(submit, 2000)
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
</script>
