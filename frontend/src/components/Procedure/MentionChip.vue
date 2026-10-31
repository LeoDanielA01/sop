<template>
  <Teleport v-for="(target, index) in targets" :key="index" :to="target">
    <HoverCard :hover-delay="0.25" :leave-delay="0.2" @update:open="(value) => value && load()">
      <template #trigger>
        <a
          :href="reference.url || undefined"
          :target="internal ? undefined : '_blank'"
          data-mention-chip
          :class="{ 'cursor-pointer': isUser && !self }"
          @click="follow"
          class="inline-flex items-center gap-1.5 rounded-3 border border-outline-gray-2 bg-surface-gray-1 px-1.5 py-px align-baseline text-ink-gray-8 no-underline hover:bg-surface-gray-2"
        >
          <span class="text-xs uppercase tracking-wide text-ink-gray-5">
            {{ reference.short_type || reference.reference_doctype }}
          </span>
          <span>{{ reference.label || reference.reference_name }}</span>
          <Badge
            v-for="badge in reference.badges || []"
            :key="badge.label"
            :theme="badge.tone || 'gray'"
            variant="subtle"
            size="sm"
          >
            {{ badge.label }}
          </Badge>
        </a>
      </template>

      <div class="w-80 p-3">
        <div v-if="card.loading && !info" class="flex flex-col gap-2">
          <Skeleton class="h-4 w-2/3" />
          <Skeleton class="h-3 w-1/2" />
          <Skeleton class="h-3 w-3/4" />
        </div>

        <p v-else-if="!info || info.missing" class="text-sm text-ink-gray-5">
          {{ __('This record no longer exists.') }}
        </p>

        <p v-else-if="info.blocked" class="text-sm text-ink-gray-5">
          {{ __('You are not allowed to see this record.') }}
        </p>

        <template v-else-if="info.is_user || info.doctype === 'User'">
          <div class="flex items-center gap-3">
            <Avatar :image="info.image" :label="info.title" size="xl" shape="circle" />
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5">
                <p class="truncate text-base font-semibold text-ink-gray-9">{{ info.title }}</p>
                <Badge v-if="info.status" :theme="info.status_tone" variant="subtle" size="sm">
                  {{ info.status }}
                </Badge>
              </div>
              <p class="truncate text-xs text-ink-gray-5 mt-0.5">{{ info.role }}</p>
              <p class="truncate text-xs font-mono text-ink-gray-6 mt-0.5">{{ info.email }}</p>
            </div>
          </div>

          <div class="mt-4 flex items-center justify-between gap-2 border-t border-outline-gray-1 pt-3">
            <button
              type="button"
              :disabled="self"
              class="flex flex-1 items-center justify-center gap-1.5 rounded-2 border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-xs font-medium text-ink-gray-8 hover:bg-surface-gray-2 hover:text-ink-gray-9 transition-colors shadow-xs disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-surface-white"
              @click="openMail(person, sop)"
            >
              <span class="lucide-mail size-3.5 text-ink-gray-5" />
              {{ __('Mail') }}
            </button>

            <button
              type="button"
              :disabled="self"
              class="flex flex-1 items-center justify-center gap-1.5 rounded-2 border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-xs font-medium text-ink-gray-8 hover:bg-surface-gray-2 hover:text-ink-gray-9 transition-colors shadow-xs disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-surface-white"
              @click="openChat(person, sop)"
            >
              <span class="lucide-message-square size-3.5 text-ink-gray-5" />
              {{ __('Message') }}
            </button>

            <button
              type="button"
              :disabled="self"
              class="flex flex-1 items-center justify-center gap-1.5 rounded-2 border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-xs font-medium text-ink-gray-8 hover:bg-surface-gray-2 hover:text-ink-gray-9 transition-colors shadow-xs disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-surface-white"
              @click="startCall(person, sop)"
            >
              <span class="lucide-phone size-3.5 text-ink-gray-5" />
              {{ __('Call') }}
            </button>
          </div>
        </template>

        <RecordCardBody v-else :info="info" />
      </div>
    </HoverCard>
  </Teleport>
</template>

<script setup>
import { computed, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Avatar, Badge, Button, HoverCard, Skeleton, createResource } from 'frappe-ui'
import { startCall } from '@/data/call'
import { openChat, openMail } from '@/data/chat'
import { session } from '@/data/session'
import RecordCardBody from '@/components/Records/RecordCardBody.vue'

const props = defineProps({
  reference: { type: Object, required: true },
  root: { type: [Object, null], default: null },
})

const route = useRoute()
const router = useRouter()

const internal = computed(() => props.reference.url?.startsWith('/sop/'))

const isUser = computed(() => props.reference.reference_doctype === 'User')

const self = computed(() => props.reference.reference_name === session.user.name)

const sop = computed(() => (route.name === 'Procedure' ? route.params.name : null))

const person = computed(() => ({
  name: props.reference.reference_name,
  full_name: info.value?.title || props.reference.label || props.reference.reference_name,
  image: info.value?.image || null,
}))

function follow(event) {
  if (isUser.value) {
    event.preventDefault()
    if (!self.value) openChat(person.value, sop.value)
    return
  }

  if (!internal.value || event.metaKey || event.ctrlKey || event.shiftKey || event.button) return
  event.preventDefault()
  router.push(props.reference.url.slice('/sop'.length))
}

const targets = shallowRef([])

watch(
  () => props.root,
  (root) => {
    if (!root) return

    const { reference_doctype: doctype, reference_name: name } = props.reference

    const escaped = CSS.escape ? CSS.escape(name) : name

    const found = root.querySelectorAll(
      [
        `a[href="#mention:${doctype}:${name}"]`,
        `span[data-type="mention"][data-id="${escaped}"]`,
        `[data-mention][data-doctype="${doctype}"][data-name="${name}"]`,
      ].join(', '),
    )

    targets.value = [...found].map((element) => {
      const host = document.createElement('span')
      element.replaceWith(host)
      return host
    })
  },
  { immediate: true },
)

const card = createResource({
  url: 'sop.api.mentions.card',
  makeParams: () => ({
    doctype: props.reference.reference_doctype,
    name: props.reference.reference_name,
  }),
})

const info = computed(() => card.data || null)

function load() {
  if (!card.data && !card.loading) card.fetch()
}

function openRecord() {
  const url = props.reference.url
  if (!url) return
  if (internal.value) router.push(url.slice('/sop'.length))
  else window.open(url, '_blank')
}
</script>
