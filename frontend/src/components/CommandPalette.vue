<template>
  <Dialog v-model:open="show" size="2xl" bare>
    <template #default>
      <div class="text-base">
        <div class="flex items-center gap-2 border-b border-outline-gray-1 px-4">
          <span class="lucide-search size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
          <TextInput
            ref="field"
            class="w-full"
            variant="ghost"
            size="md"
            autocomplete="off"
            :placeholder="__('Search a procedure, or a record one mentions')"
            v-model="query"
            @update:modelValue="onInput"
            @keydown.down.prevent="move(1)"
            @keydown.up.prevent="move(-1)"
            @keydown.enter.prevent="choose(active)"
          />
          <Badge v-if="search.loading" variant="subtle" theme="gray" size="sm" :label="__('Searching')" />
        </div>

        <div ref="scroller" class="max-h-96 overflow-auto px-2 py-2">
          <div v-for="group in groups" :key="group.title" class="mt-3 first:mt-0">
            <div class="px-2 pb-1 text-sm text-ink-gray-5">{{ group.title }}</div>

            <div
              v-for="item in group.items"
              :key="item.key"
              :ref="(el) => setRow(el, item.index)"
              class="flex cursor-pointer items-center gap-3 rounded-3 px-2.5 py-2"
              :class="item.index === cursor ? 'bg-surface-gray-2' : 'hover:bg-surface-gray-2'"
              @click="choose(item)"
              @mouseenter="cursor = item.index"
            >
              <span :class="item.icon" class="size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />

              <span class="min-w-0 flex-1">
                <span class="block truncate text-base text-ink-gray-8">{{ item.label }}</span>
                <span v-if="item.description" class="block truncate text-sm text-ink-gray-5">
                  {{ item.description }}
                </span>
              </span>

              <Badge v-if="item.count" variant="subtle" theme="orange" size="sm">
                {{ item.count }}
              </Badge>
              <Badge v-else-if="item.badge" variant="subtle" :theme="TONE[item.badge]" size="sm">
                {{ item.badge }}
              </Badge>
            </div>
          </div>

          <p v-if="empty" class="px-3 py-10 text-center text-base text-ink-gray-5">
            {{ __('Nothing matches that. Search by title, by procedure number, or by the code of anything a procedure mentions.') }}
          </p>
        </div>

        <div
          class="flex items-center gap-5 border-t border-outline-gray-1 px-4 py-2 text-sm text-ink-gray-6"
        >
          <div class="flex items-center gap-2">
            <span
              class="lucide-move-up size-5 rounded-3 bg-surface-gray-2 p-1"
              aria-hidden="true"
            />
            <span
              class="lucide-move-down size-5 rounded-3 bg-surface-gray-2 p-1"
              aria-hidden="true"
            />
            <span>{{ __('to move') }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="lucide-corner-down-left size-5 rounded-3 bg-surface-gray-2 p-1"
              aria-hidden="true"
            />
            <span>{{ __('to open') }}</span>
          </div>
          <div class="ml-auto flex items-center gap-2">
            <span class="rounded-3 bg-surface-gray-2 px-1.5 py-0.5">esc</span>
            <span>{{ __('to close') }}</span>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Badge, Dialog, TextInput, createResource, debounce } from 'frappe-ui'
import { SECTIONS, activeSpace, spaces, views } from '@/data/navigation'
import { translate as __ } from '@/translation'

const show = defineModel('open', { type: Boolean, default: false })

const router = useRouter()
const field = ref(null)
const scroller = ref(null)
const rows = ref({})
const query = ref('')
const cursor = ref(0)

const TONE = {
  Effective: 'green',
  'Pending Approval': 'orange',
  Draft: 'gray',
  Retired: 'red',
  Superseded: 'gray',
}

const search = createResource({
  url: 'sop.api.search.query',
  makeParams: () => ({ text: query.value, space: activeSpace.value }),
  onSuccess() {
    cursor.value = 0
  },
})

const jumpTo = computed(() => [
  {
    title: __('Jump to'),
    items: [
      ...SECTIONS.map((section) => ({
        label: section.label,
        icon: section.icon,
        route: section.route,
      })),
      { label: __('New procedure'), icon: 'lucide-plus', route: '/new' },
      { label: __('Training matrix'), icon: 'lucide-grid-3x3', route: '/training/matrix' },
    ],
  },
  {
    title: __('My work'),
    items: views.value
      .filter((view) => view.count)
      .map((view) => ({
        label: view.label,
        icon: view.icon,
        count: view.count,
        route: `/?view=${view.value}`,
      })),
  },
  {
    title: __('Spaces'),
    items: spaces.value.map((space) => ({
      label: space.title,
      icon: 'lucide-book-text',
      description: `${space.space_code} · ${space.total ?? 0} procedures`,
      route: `/?space=${space.name}`,
    })),
  },
])

const groups = computed(() => {
  const source = query.value.trim() ? search.data?.groups || [] : jumpTo.value

  let index = -1
  return source
    .filter((group) => group.items?.length)
    .map((group) => ({
      title: group.title,
      items: group.items.map((item) => {
        index += 1
        return { ...item, index, key: `${item.route}:${item.label}` }
      }),
    }))
})

const flat = computed(() => groups.value.flatMap((group) => group.items))
const active = computed(() => flat.value[cursor.value])
const empty = computed(() => !!query.value.trim() && !search.loading && !flat.value.length)

const run = debounce(() => search.reload(), 250)

function onInput() {
  cursor.value = 0
  if (query.value.trim()) run()
}

function setRow(el, index) {
  if (el) rows.value[index] = el
  else delete rows.value[index]
}

async function move(step) {
  if (!flat.value.length) return

  cursor.value = (cursor.value + step + flat.value.length) % flat.value.length
  await nextTick()
  rows.value[cursor.value]?.scrollIntoView({ block: 'nearest' })
}

function choose(item) {
  if (!item) return

  show.value = false
  router.push(item.route)
}

watch(show, async (open) => {
  if (!open) {
    query.value = ''
    return
  }

  cursor.value = 0
  await nextTick()
  field.value?.$el?.querySelector('input')?.focus()
})
</script>
