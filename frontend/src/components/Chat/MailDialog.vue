<template>
  <Dialog v-model:open="mail.open" :title="__('New email')" size="2xl">
    <template #default>
      <div class="flex flex-col gap-3">
        <div class="flex items-center gap-2">
          <span class="w-10 shrink-0 text-sm text-ink-gray-5">{{ __('To') }}</span>
          <span
            class="inline-flex min-w-0 items-center gap-1.5 rounded-2 border border-outline-gray-2 bg-surface-gray-1 py-0.5 pl-0.5 pr-2"
          >
            <Avatar :image="mail.person?.image" :label="mail.person?.full_name" size="sm" shape="circle" />
            <span class="truncate text-sm text-ink-gray-8">{{ mail.person?.full_name }}</span>
          </span>

          <div class="flex-1" />

          <Button v-if="!showCc" variant="ghost" size="sm" :label="__('Cc')" @click="showCc = true" />
        </div>

        <div v-if="showCc" class="flex items-center gap-2">
          <span class="w-10 shrink-0 text-sm text-ink-gray-5">{{ __('Cc') }}</span>
          <TextInput
            v-model="cc"
            class="flex-1"
            type="text"
            :placeholder="__('Email addresses, separated by commas')"
          />
        </div>

        <div class="flex items-center gap-2">
          <span class="w-10 shrink-0 text-sm text-ink-gray-5">{{ __('Use') }}</span>
          <FormControl
            v-model="template"
            class="flex-1"
            type="select"
            :options="templateOptions"
            :disabled="applying"
          />
        </div>

        <div class="flex items-center gap-2">
          <span class="w-10 shrink-0 text-sm text-ink-gray-5">{{ __('Subject') }}</span>
          <TextInput v-model="subject" class="flex-1" type="text" />
        </div>

        <div class="rounded-2 border border-outline-gray-2 bg-surface-base">
          <EditorFixedMenu
            v-if="editor"
            :editor="editor"
            :items="TOOLS"
            class="overflow-x-auto border-b border-outline-gray-1 px-1.5 py-1"
          />
          <EditorContent
            :editor="editor"
            class="prose-sop max-h-[45vh] min-h-48 overflow-y-auto px-3 py-2.5 text-base text-ink-gray-8"
          />
        </div>

        <div v-if="files.length || uploading" class="flex flex-wrap gap-1.5">
          <span
            v-for="file in files"
            :key="file.name"
            class="inline-flex max-w-60 items-center gap-1.5 rounded-2 border border-outline-gray-2 bg-surface-gray-1 py-1 pl-2 pr-1 text-sm text-ink-gray-8"
          >
            <span class="lucide-paperclip size-3.5 shrink-0 text-ink-gray-5" aria-hidden="true" />
            <span class="truncate">{{ file.file_name }}</span>
            <button
              type="button"
              class="grid size-5 shrink-0 place-content-center rounded-1 text-ink-gray-5 hover:bg-surface-gray-3 hover:text-ink-gray-8"
              :aria-label="__('Remove {0}').format(file.file_name)"
              @click="files = files.filter((row) => row.name !== file.name)"
            >
              <span class="lucide-x size-3" aria-hidden="true" />
            </button>
          </span>
          <span v-if="uploading" class="inline-flex items-center gap-1.5 px-1 text-sm text-ink-gray-5">
            <span class="lucide-loader-circle size-3.5 animate-spin" aria-hidden="true" />
            {{ __('Uploading…') }}
          </span>
        </div>

        <div class="flex flex-wrap items-center gap-x-5 gap-y-2">
          <FormControl
            v-if="mail.sop"
            v-model="addLink"
            type="checkbox"
            :label="__('Add a link to {0}').format(mail.sop)"
          />
          <FormControl v-model="copyMe" type="checkbox" :label="__('Send me a copy')" />
        </div>

        <div v-if="naming" class="flex items-end gap-2 rounded-2 border border-outline-gray-2 bg-surface-gray-1 p-2.5">
          <FormControl
            v-model="templateName"
            class="flex-1"
            type="text"
            :label="__('Template name')"
            :placeholder="__('e.g. Review reminder')"
          />
          <Button :label="__('Cancel')" @click="naming = false" />
          <Button
            variant="solid"
            :label="__('Save template')"
            :loading="saving"
            :disabled="!templateName.trim()"
            @click="keepTemplate"
          />
        </div>

        <ErrorMessage :message="error" />

        <input ref="picker" type="file" multiple class="hidden" @change="upload" />
      </div>
    </template>

    <template #actions>
      <div class="flex items-center gap-2">
        <Button variant="subtle" icon-left="lucide-paperclip" :label="__('Attach')" @click="picker?.click()" />
        <Button
          v-if="canSaveTemplates && !naming"
          variant="ghost"
          icon-left="lucide-bookmark-plus"
          :label="__('Save as template')"
          :disabled="!subject.trim() || empty"
          @click="startNaming"
        />

        <div class="flex-1" />

        <Button :label="__('Cancel')" @click="mail.open = false" />
        <Button
          variant="solid"
          icon-left="lucide-send-horizontal"
          :label="__('Send')"
          :loading="sending"
          :disabled="!subject.trim() || empty || uploading"
          @click="send"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  Avatar,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  TextInput,
  createResource,
  toast,
  useFileUpload,
} from 'frappe-ui'
import {
  Blockquote,
  Bold,
  BulletList,
  EditorContent,
  EditorFixedMenu,
  InsertLink,
  Italic,
  OrderedList,
  Redo,
  RichTextKit,
  Separator,
  Strike,
  Undo,
  useEditor,
} from 'frappe-ui/editor'
import { applyTemplate, mail, saveTemplate, sendMail } from '@/data/chat'
import { session } from '@/data/session'
import { translate as __ } from '@/translation'

const TOOLS = [
  Bold,
  Italic,
  Strike,
  Separator,
  BulletList,
  OrderedList,
  Blockquote,
  Separator,
  InsertLink,
  Separator,
  Undo,
  Redo,
]

const subject = ref('')
const body = ref('')
const cc = ref('')
const showCc = ref(false)
const template = ref('')
const files = ref([])
const addLink = ref(true)
const copyMe = ref(false)
const error = ref(null)
const sending = ref(false)
const applying = ref(false)
const uploading = ref(false)
const naming = ref(false)
const saving = ref(false)
const templateName = ref('')
const picker = ref(null)

const fileUpload = useFileUpload()

const editor = useEditor({
  content: body,
  format: 'html',
  placeholder: __('Write your email…'),
  extensions: [RichTextKit],
  onUpdate({ editor }) {
    body.value = editor.getHTML()
  },
})

const templates = createResource({ url: 'sop.api.chat.templates' })

const templateOptions = computed(() => [
  { label: __('No template'), value: '' },
  ...(templates.data || []).map((row) => ({ label: row.name, value: row.name })),
])

const canSaveTemplates = computed(() => session.user.is_author || session.user.is_manager)

const empty = computed(() => !body.value.replace(/<[^>]*>/g, '').trim())

function setBody(html) {
  body.value = html
  editor.value?.commands.setContent(html || '')
}

watch(
  () => mail.open,
  (open) => {
    if (!open) return

    subject.value = mail.subject || (mail.sop ? __('About {0}').format(mail.sop) : '')
    setBody('')
    cc.value = ''
    showCc.value = false
    template.value = ''
    files.value = []
    addLink.value = true
    copyMe.value = false
    naming.value = false
    error.value = null
    templates.reload()
  },
)

watch(template, async (name) => {
  if (!name) return

  applying.value = true
  error.value = null

  try {
    const filled = await applyTemplate(name)
    subject.value = filled.subject || subject.value
    setBody(filled.message)
  } catch (failure) {
    error.value = failure.messages?.[0] || failure.message
  } finally {
    applying.value = false
  }
})

async function upload(event) {
  const chosen = Array.from(event.target.files || [])
  event.target.value = ''
  if (!chosen.length) return

  uploading.value = true
  error.value = null

  try {
    for (const file of chosen) {
      const saved = await fileUpload.upload(file, { private: true, folder: 'Home/Attachments' })
      files.value = [...files.value, saved]
    }
  } catch (failure) {
    error.value = failure.messages?.[0] || failure.message || __('Upload failed')
  } finally {
    uploading.value = false
  }
}

function startNaming() {
  templateName.value = template.value || subject.value
  naming.value = true
}

async function keepTemplate() {
  saving.value = true
  error.value = null

  try {
    const saved = await saveTemplate({
      title: templateName.value,
      subject: subject.value,
      message: body.value,
    })
    naming.value = false
    await templates.reload()
    toast.success(__('Template {0} saved').format(saved.name))
  } catch (failure) {
    error.value = failure.messages?.[0] || failure.message
  } finally {
    saving.value = false
  }
}

async function send() {
  sending.value = true
  error.value = null

  try {
    await sendMail({
      subject: subject.value,
      message: body.value,
      cc: cc.value,
      attachments: files.value.map((file) => file.name),
      copy_me: copyMe.value ? 1 : 0,
      add_link: addLink.value ? 1 : 0,
    })
    mail.open = false
    toast.success(__('Email sent'))
  } catch (failure) {
    error.value = failure.messages?.[0] || failure.message
  } finally {
    sending.value = false
  }
}
</script>
