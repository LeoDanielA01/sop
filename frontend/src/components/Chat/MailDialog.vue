<template>
  <Dialog v-model:open="mail.open" :title="__('New email')" size="2xl">
    <template #default>
      <div class="flex flex-col gap-3">
        <div class="overflow-hidden rounded-2 border border-outline-gray-2 bg-surface-base">
          <div class="flex min-h-10 items-center gap-3 border-b border-outline-gray-1 px-3">
            <span class="w-14 shrink-0 text-sm text-ink-gray-5">{{ __('To') }}</span>
            <span
              class="inline-flex min-w-0 items-center gap-1.5 rounded-3 bg-surface-gray-2 py-0.5 pl-0.5 pr-2"
            >
              <Avatar :image="mail.person?.image" :label="mail.person?.full_name" size="sm" shape="circle" />
              <span class="truncate text-sm text-ink-gray-8">{{ mail.person?.full_name }}</span>
            </span>
            <div class="flex-1" />
            <button
              v-if="!showCc"
              type="button"
              class="rounded-1 px-1.5 py-0.5 text-sm text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
              @click="revealCc"
            >
              {{ __('Cc') }}
            </button>
          </div>

          <div v-if="showCc" class="flex min-h-10 items-center gap-3 border-b border-outline-gray-1 px-3">
            <span class="w-14 shrink-0 text-sm text-ink-gray-5">{{ __('Cc') }}</span>
            <input
              ref="ccInput"
              v-model="cc"
              type="text"
              :placeholder="__('Email addresses, separated by commas')"
              class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:ring-0"
            />
          </div>

          <div class="flex min-h-10 items-center gap-3 border-b border-outline-gray-1 px-3">
            <span class="w-14 shrink-0 text-sm text-ink-gray-5">{{ __('Subject') }}</span>
            <input
              v-model="subject"
              type="text"
              :placeholder="__('What is this about?')"
              class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base font-medium text-ink-gray-9 placeholder:font-normal placeholder:text-ink-gray-4 focus:ring-0"
            />
          </div>

          <div class="flex items-center gap-2 border-b border-outline-gray-1 bg-surface-gray-1 pl-1.5 pr-2">
            <EditorFixedMenu v-if="editor" :editor="editor" :items="TOOLS" class="min-w-0 flex-1 overflow-x-auto py-1" />

            <Dropdown :options="templateMenu" align="end">
              <Button
                variant="ghost"
                size="sm"
                icon-left="lucide-layout-template"
                icon-right="lucide-chevron-down"
                :label="template || __('Templates')"
                :loading="applying"
              />
            </Dropdown>
          </div>

          <EditorContent
            :editor="editor"
            class="prose-sop max-h-[45vh] min-h-56 overflow-y-auto px-4 py-3 text-base text-ink-gray-8"
          />

          <div
            v-if="files.length || uploading"
            class="flex flex-wrap gap-1.5 border-t border-outline-gray-1 bg-surface-gray-1 px-3 py-2"
          >
            <span
              v-for="file in files"
              :key="file.name"
              class="inline-flex max-w-60 items-center gap-1.5 rounded-2 border border-outline-gray-2 bg-surface-base py-1 pl-2 pr-1 text-sm text-ink-gray-8"
            >
              <span class="lucide-paperclip size-3.5 shrink-0 text-ink-gray-5" aria-hidden="true" />
              <span class="truncate">{{ file.file_name }}</span>
              <button
                type="button"
                class="grid size-5 shrink-0 place-content-center rounded-1 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
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
        </div>

        <div class="flex flex-wrap items-center gap-1.5">
          <button
            v-if="mail.sop"
            type="button"
            class="inline-flex items-center gap-1.5 rounded-3 border px-2.5 py-1 text-sm transition-colors"
            :class="pillClass(addLink)"
            :aria-pressed="addLink"
            @click="addLink = !addLink"
          >
            <span :class="addLink ? 'lucide-check' : 'lucide-link'" class="size-3.5" aria-hidden="true" />
            {{ __('Link to {0}').format(mail.sop) }}
          </button>

          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-3 border px-2.5 py-1 text-sm transition-colors"
            :class="pillClass(copyMe)"
            :aria-pressed="copyMe"
            @click="copyMe = !copyMe"
          >
            <span :class="copyMe ? 'lucide-check' : 'lucide-copy'" class="size-3.5" aria-hidden="true" />
            {{ __('Send me a copy') }}
          </button>
        </div>

        <div
          v-if="naming"
          class="flex items-center gap-2 rounded-2 border border-outline-gray-2 bg-surface-gray-1 p-2"
        >
          <span class="lucide-bookmark-plus ml-1 size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          <input
            ref="nameInput"
            v-model="templateName"
            type="text"
            :placeholder="__('Name this template')"
            class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:ring-0"
            @keydown.enter.prevent="keepTemplate"
          />
          <Button variant="ghost" :label="__('Cancel')" @click="naming = false" />
          <Button
            variant="solid"
            :label="__('Save')"
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
        <Tooltip :text="__('Attach files')">
          <Button variant="subtle" icon="lucide-paperclip" :label="__('Attach files')" @click="picker?.click()" />
        </Tooltip>

        <span class="truncate text-sm text-ink-gray-5">
          {{ files.length ? __('{0} attached').format(files.length) : '' }}
        </span>

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
import { computed, nextTick, ref, watch } from 'vue'
import {
  Avatar,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  Tooltip,
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

const TOOLS = [Bold, Italic, Strike, Separator, BulletList, OrderedList, Blockquote, Separator, InsertLink, Separator, Undo, Redo]

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
const ccInput = ref(null)
const nameInput = ref(null)

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

const canSaveTemplates = computed(() => session.user.is_author || session.user.is_manager)

const empty = computed(() => !body.value.replace(/<[^>]*>/g, '').trim())

const templateMenu = computed(() => [
  ...(templates.data || []).map((row) => ({
    label: row.name,
    icon: row.name === template.value ? 'lucide-check' : 'lucide-file-text',
    onClick: () => pick(row.name),
  })),
  {
    label: __('No templates yet'),
    icon: 'lucide-info',
    onClick: () => {},
    condition: () => !(templates.data || []).length,
  },
  {
    label: __('Save this email as a template'),
    icon: 'lucide-bookmark-plus',
    onClick: startNaming,
    condition: () => canSaveTemplates.value && !!subject.value.trim() && !empty.value,
  },
])

function pillClass(on) {
  return on
    ? 'border-outline-gray-4 bg-surface-gray-2 text-ink-gray-9'
    : 'border-outline-gray-2 text-ink-gray-6 hover:bg-surface-gray-1'
}

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

async function revealCc() {
  showCc.value = true
  await nextTick()
  ccInput.value?.focus()
}

async function pick(name) {
  applying.value = true
  error.value = null

  try {
    const filled = await applyTemplate(name)
    template.value = name
    subject.value = filled.subject || subject.value
    setBody(filled.message)
  } catch (failure) {
    error.value = failure.messages?.[0] || failure.message
  } finally {
    applying.value = false
  }
}

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

async function startNaming() {
  templateName.value = template.value || subject.value
  naming.value = true
  await nextTick()
  nameInput.value?.select()
}

async function keepTemplate() {
  if (!templateName.value.trim() || saving.value) return

  saving.value = true
  error.value = null

  try {
    const saved = await saveTemplate({
      title: templateName.value,
      subject: subject.value,
      message: body.value,
    })
    naming.value = false
    template.value = saved.name
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
