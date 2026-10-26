<template>
  <PageHeader>
    <AppBreadcrumbs />
  </PageHeader>

  <div class="mx-auto w-full max-w-[940px] space-y-5 px-3 pb-12 pt-5 sm:px-5">
    <div>
      <h1 class="text-xl font-semibold text-ink-gray-9">{{ __('Import procedures from Word') }}</h1>
      <p class="mt-1 text-base text-ink-gray-6">
        {{
          __(
            'Upload a .zip of your SOP folders or a single .docx. English files are imported as drafts — steps, critical boxes, notes and SOP references are kept, and Appendix A files become risk assessments with scored hazards, actions and recurring checks. Nothing goes live until it is approved.',
          )
        }}
      </p>
    </div>

    <div class="flex flex-wrap items-end gap-3 rounded-4 border border-outline-gray-2 bg-surface-base p-4">
      <FormControl
        v-model="space"
        type="select"
        class="w-60"
        :label="__('Into space')"
        :options="spaces.map((row) => ({ label: row.title, value: row.name }))"
      />
      <input ref="picker" type="file" accept=".zip,.docx" class="hidden" @change="pick" />
      <Button
        :label="fileName || __('Choose .zip or .docx')"
        icon-left="lucide-file-up"
        :loading="uploading || preview.loading"
        @click="picker.click()"
      />
      <span v-if="fileName && !preview.loading" class="text-sm text-ink-gray-5">
        {{ __('{0} to import · {1} skipped').format(fresh.length, (preview.data?.skipped || []).length) }}
      </span>
    </div>

    <ErrorMessage :message="errorOf(preview) || errorOf(run)" />

    <div v-if="result" class="space-y-3 rounded-4 border border-outline-green-2 bg-surface-green-1 p-4">
      <p class="font-medium text-ink-gray-9">
        {{ __('{0} procedures imported as drafts.').format(result.created.length) }}
      </p>
      <ul class="space-y-1 text-base">
        <li v-for="row in result.created" :key="row.name">
          <a v-if="row.url" :href="row.url" target="_blank" class="text-ink-blue-3 hover:underline">{{ row.name }}</a>
          <router-link v-else :to="`/${row.name}`" class="text-ink-blue-3 hover:underline">{{ row.name }}</router-link>
          <span class="text-ink-gray-7"> — {{ row.title }}</span>
          <span v-for="warning in row.warnings" :key="warning" class="ml-2 text-sm text-ink-amber-6">⚠ {{ warning }}</span>
        </li>
      </ul>
      <Button :label="__('Go to procedures')" @click="router.push('/procedures')" />
    </div>

    <template v-else-if="groups.length">
      <div v-for="group in groups" :key="group.key" class="rounded-4 border border-outline-gray-2 bg-surface-base">
        <div class="flex items-center gap-2 border-b border-outline-gray-1 px-4 py-2.5">
          <span class="lucide-folder-tree size-4 text-ink-gray-5" aria-hidden="true" />
          <input
            v-model="processNames[group.key]"
            class="min-w-0 flex-1 rounded-2 border border-transparent bg-transparent px-1.5 py-0.5 text-base font-medium text-ink-gray-9 hover:border-outline-gray-2 focus:border-outline-gray-3 focus:outline-none"
            :placeholder="__('Process name')"
          />
          <span class="text-sm text-ink-gray-5">{{ __('process') }}</span>
        </div>
        <div
          v-for="row in group.rows"
          :key="row.sop_no"
          class="flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-outline-gray-1 px-4 py-2 last:border-0"
        >
          <span class="w-32 shrink-0 font-mono text-sm text-ink-gray-8">{{ row.sop_no }}</span>
          <span class="min-w-0 flex-1 text-base text-ink-gray-8">{{ row.title }}</span>
          <Badge :label="row.document_type" :theme="typeTheme(row.document_type)" />
          <span v-if="row.steps" class="text-sm text-ink-gray-5">{{ __('{0} steps').format(row.steps) }}</span>
          <span v-if="row.hazards?.length" class="text-sm text-ink-gray-5">{{ __('{0} hazards').format(row.hazards.length) }}</span>
          <Badge v-if="row.exists" :label="__('Already exists — skipped')" theme="gray" />
          <p v-for="warning in row.warnings" :key="warning" class="w-full pl-32 text-sm text-ink-amber-6">
            ⚠ {{ warning }}
          </p>
        </div>
      </div>

      <details v-if="preview.data.skipped.length" class="rounded-4 border border-outline-gray-2 bg-surface-base px-4 py-2.5">
        <summary class="cursor-pointer text-base text-ink-gray-7">
          {{ __('{0} files not imported').format(preview.data.skipped.length) }}
        </summary>
        <ul class="mt-2 space-y-1">
          <li v-for="row in preview.data.skipped" :key="row.file" class="text-sm">
            <span class="text-ink-gray-8">{{ row.file }}</span>
            <span class="text-ink-gray-5"> — {{ row.reason }}</span>
          </li>
        </ul>
      </details>

      <div class="flex justify-end">
        <Button
          variant="solid"
          :label="__('Import {0} as drafts').format(fresh.length)"
          :disabled="!space || !fresh.length"
          :loading="run.loading"
          @click="startImport"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Badge, Button, ErrorMessage, FormControl, PageHeader, createResource, useFileUpload } from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import { translate as __ } from '@/translation'
import { activeSpace, spaces } from '@/data/navigation'

const router = useRouter()
const picker = ref(null)
const fileName = ref('')
const fileUrl = ref('')
const uploading = ref(false)
const space = ref(activeSpace.value || spaces.value[0]?.name || '')
const processNames = reactive({})
const result = ref(null)
const fileUpload = useFileUpload()

const preview = createResource({ url: 'sop.api.importer.preview' })
const run = createResource({ url: 'sop.api.importer.run' })

const rows = computed(() => preview.data?.procedures || [])
const fresh = computed(() => rows.value.filter((row) => !row.exists))

const groups = computed(() => {
  const found = []
  for (const row of rows.value) {
    const key = row.process || ''
    let group = found.find((item) => item.key === key)
    if (!group) {
      group = { key, rows: [] }
      found.push(group)
    }
    group.rows.push(row)
  }
  return found
})

watch(groups, (list) => {
  for (const group of list) {
    if (!(group.key in processNames)) processNames[group.key] = group.key
  }
})

function typeTheme(type) {
  return { 'Equipment SOP': 'blue', Appendix: 'gray', 'Risk Assessment': 'orange' }[type] || 'green'
}

function errorOf(resource) {
  return resource.error?.messages?.[0] || resource.error?.message || ''
}

async function pick(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  result.value = null
  fileName.value = file.name
  uploading.value = true
  try {
    const uploaded = await fileUpload.upload(file, { private: true, folder: 'Home' })
    fileUrl.value = uploaded.file_url
  } finally {
    uploading.value = false
  }
  preview.submit({ file_url: fileUrl.value })
}

function startImport() {
  const processes = {}
  for (const row of fresh.value) processes[row.sop_no] = processNames[row.process || ''] || ''

  run.submit(
    { file_url: fileUrl.value, space: space.value, processes },
    {
      onSuccess(data) {
        result.value = data
      },
    },
  )
}
</script>
