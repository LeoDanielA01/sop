<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, Button, FormControl, PageHeader, PageHeaderTitle, createResource } from 'frappe-ui'
import ProcedureEditor from '@/components/editor/ProcedureEditor.vue'
import { activeSpace, spaces } from '@/data/navigation'

const route = useRoute()
const router = useRouter()

const draft = reactive({ title: '', summary: '', content: '', space: null, sop_no: null, status: 'Draft' })
const dirty = ref(false)
const savedAt = ref(null)

const isNew = computed(() => !route.params.name)
const spaceOptions = computed(() => spaces.value.map((s) => ({ label: s.title, value: s.name })))

const load = createResource({
  url: 'sop.api.procedures.get_procedure',
  onSuccess(doc) {
    Object.assign(draft, {
      title: doc.title,
      summary: doc.summary,
      content: doc.content,
      space: doc.space,
      sop_no: doc.sop_no,
      status: doc.status,
    })
    dirty.value = false
  },
})

const save = createResource({
  url: 'sop.api.procedures.save_draft',
  onSuccess(doc) {
    dirty.value = false
    savedAt.value = new Date()
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
  })
}

// Autosave is a promise the editor makes: nobody should lose a paragraph to a
// closed tab. Two seconds after typing stops, not on every keystroke.
let timer = null
watch(
  () => [draft.title, draft.summary, draft.content],
  () => {
    dirty.value = true
    clearTimeout(timer)
    if (draft.title) timer = setTimeout(submit, 2000)
  },
)

onMounted(() => {
  if (!isNew.value) load.submit({ name: route.params.name })
  else draft.space = activeSpace.value
})
</script>

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
        :disabled="!draft.title"
        @click="submit"
      />
    </div>
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[820px] px-3 pb-16 sm:px-5">
    <div class="mb-4 flex flex-col gap-3">
      <FormControl
        type="text"
        size="lg"
        placeholder="Title — what this procedure covers"
        v-model="draft.title"
      />
      <div class="grid gap-3 sm:grid-cols-2">
        <FormControl
          type="select"
          label="Space"
          :options="spaceOptions"
          v-model="draft.space"
        />
        <FormControl
          type="text"
          label="Summary"
          placeholder="One line, shown in search results"
          v-model="draft.summary"
        />
      </div>
    </div>

    <ProcedureEditor v-model="draft.content" />
  </div>
</template>
