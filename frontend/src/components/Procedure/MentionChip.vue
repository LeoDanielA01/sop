<template>
  <Teleport v-if="target" :to="target">
    <HoverCard :hover-delay="0.25" :leave-delay="0.2" @update:open="(value) => value && load()">
      <template #trigger>
        <a
          :href="reference.url || undefined"
          target="_blank"
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
            <a
              :href="`mailto:${info.email}`"
              class="flex flex-1 items-center justify-center gap-1.5 rounded-md border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-xs font-medium text-ink-gray-8 no-underline hover:bg-surface-gray-2 hover:text-ink-gray-9 transition-colors shadow-xs"
            >
              <span class="lucide-mail size-3.5 text-ink-gray-5" />
              {{ __('Mail') }}
            </a>

            <a
              :href="`mailto:${info.email}?subject=Internal%20Message`"
              class="flex flex-1 items-center justify-center gap-1.5 rounded-md border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-xs font-medium text-ink-gray-8 no-underline hover:bg-surface-gray-2 hover:text-ink-gray-9 transition-colors shadow-xs"
            >
              <span class="lucide-message-square size-3.5 text-ink-gray-5" />
              {{ __('Message') }}
            </a>

            <a
              :href="info.phone ? `tel:${info.phone}` : undefined"
              :class="info.phone ? 'hover:bg-surface-gray-2 text-ink-gray-8' : 'opacity-50 cursor-not-allowed text-ink-gray-4'"
              class="flex flex-1 items-center justify-center gap-1.5 rounded-md border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-xs font-medium no-underline transition-colors shadow-xs"
            >
              <span class="lucide-phone size-3.5 text-ink-gray-5" />
              {{ __('Call') }}
            </a>
          </div>
        </template>

        <template v-else>
          <div class="flex items-start gap-2.5">
            <Avatar :image="info.image" :label="info.title" size="xl" shape="square" />
            <div class="min-w-0 flex-1">
              <p class="truncate text-base font-medium text-ink-gray-9">{{ info.title }}</p>
              <p class="truncate text-sm text-ink-gray-5">{{ info.doctype }} · {{ info.name }}</p>
            </div>
            <Badge v-if="info.status" :theme="info.status_tone" variant="subtle" size="sm">
              {{ info.status }}
            </Badge>
          </div>

          <dl
            v-if="info.facts.length"
            class="mt-3 divide-y divide-outline-gray-1 border-t border-outline-gray-1"
          >
            <div
              v-for="fact in info.facts"
              :key="fact.label"
              class="flex items-center justify-between gap-3 py-1.5"
            >
              <dt class="shrink-0 text-sm text-ink-gray-5">{{ fact.label }}</dt>
              <dd class="min-w-0 truncate text-right text-sm text-ink-gray-8">
                <Badge
                  v-if="fact.tone && fact.tone !== 'gray'"
                  :theme="fact.tone"
                  variant="subtle"
                  size="sm"
                >
                  {{ fact.value }}
                </Badge>
                <template v-else>{{ fact.value }}</template>
              </dd>
            </div>
          </dl>

          <div v-if="info.counts.length" class="mt-3">
            <p class="mb-1.5 text-sm text-ink-gray-5">{{ __('Linked records') }}</p>
            <div class="flex flex-wrap gap-1.5">
              <a
                v-for="count in info.counts"
                :key="count.doctype"
                :href="count.route || undefined"
                target="_blank"
                class="inline-flex items-center gap-1 rounded-3 bg-surface-gray-2 px-1.5 py-0.5 text-sm text-ink-gray-7 no-underline hover:bg-surface-gray-3"
              >
                {{ count.doctype }}
                <span class="tabular-nums text-ink-gray-9">{{ count.label }}</span>
              </a>
            </div>
          </div>

          <div class="mt-3 flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              icon-right="lucide-arrow-up-right"
              :label="__('Open')"
              @click="openRecord"
            />
          </div>
        </template>
      </div>
    </HoverCard>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { Avatar, Badge, Button, HoverCard, Skeleton, createResource } from 'frappe-ui'

const props = defineProps({
  reference: { type: Object, required: true },
  root: { type: [Object, null], default: null },
})

const target = computed(() => {
  if (!props.root) return null

  const { reference_doctype: doctype, reference_name: name } = props.reference

  const escaped = CSS.escape ? CSS.escape(name) : name

  return (
    props.root.querySelector(`a[href="#mention:${doctype}:${name}"]`) ||
    props.root.querySelector(`span[data-type="mention"][data-id="${escaped}"]`) ||
    props.root.querySelector(`[data-mention][data-doctype="${doctype}"][data-name="${name}"]`)
  )
})

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
  if (props.reference.url) window.open(props.reference.url, '_blank')
}
</script>
