<template>
  <Dialog v-model="open" :options="{ size: '2xl' }">
    <template #body>
      <div class="border-b border-outline-gray-1 px-3 py-2.5">
        <div class="flex items-center gap-2">
          <span class="lucide-search size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          <TextInput
            ref="input"
            class="w-full"
            variant="ghost"
            placeholder="Search procedures, or a record they mention"
            v-model="text"
            @update:modelValue="onType"
            @keydown.down.prevent="move(1)"
            @keydown.up.prevent="move(-1)"
            @keydown.enter.prevent="choose(flat[cursor])"
          />
          <Badge variant="subtle" size="sm">Esc</Badge>
        </div>
      </div>

      <div class="max-h-[60vh] overflow-y-auto p-1.5">
        <div v-for="group in groups" :key="group.title" class="pb-1">
          <div class="px-2 py-1 text-xs uppercase tracking-wide text-ink-gray-4">
            {{ group.title }}
          </div>
          <Button
            v-for="item in group.items"
            :key="item.route + item.label"
            :variant="flat[cursor] === item ? 'subtle' : 'ghost'"
            class="!h-auto w-full !justify-start !px-2 !py-2"
            @click="choose(item)"
          >
            <span :class="item.icon" class="size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
            <span class="ml-2 min-w-0 flex-1 text-left">
              <span class="block truncate text-base text-ink-gray-8">{{ item.label }}</span>
              <span class="block truncate text-sm text-ink-gray-5">{{ item.description }}</span>
            </span>
            <Badge v-if="item.badge" variant="subtle" size="sm">{{ item.badge }}</Badge>
          </Button>
        </div>

        <p v-if="text && !search.loading && !flat.length" class="px-3 py-8 text-center text-base text-ink-gray-5">
          Nothing matches “{{ text }}”.
        </p>

        <p v-if="!text" class="px-3 py-8 text-center text-sm text-ink-gray-5">
          Type a title, a procedure number, or the code of anything a procedure mentions.
        </p>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Badge, Button, Dialog, TextInput, createResource } from 'frappe-ui'
import { activeSpace } from '@/data/navigation'

const open = defineModel('open', { type: Boolean, default: false })

const router = useRouter()
const input = ref(null)
const text = ref('')
const cursor = ref(0)
let timer = null

const search = createResource({
  url: 'sop.api.search.query',
  onSuccess() {
    cursor.value = 0
  },
})

const groups = computed(() => search.data?.groups || [])
const flat = computed(() => groups.value.flatMap((group) => group.items))

function onType() {
  clearTimeout(timer)
  if (!text.value.trim()) {
    search.reset?.()
    return
  }
  timer = setTimeout(() => search.submit({ text: text.value, space: activeSpace.value }), 180)
}

function move(step) {
  if (!flat.value.length) return
  cursor.value = (cursor.value + step + flat.value.length) % flat.value.length
}

function choose(item) {
  if (!item) return
  open.value = false
  router.push(item.route)
}

watch(open, async (value) => {
  if (!value) return
  text.value = ''
  cursor.value = 0
  search.reset?.()
  await nextTick()
  input.value?.$el?.querySelector('input')?.focus()
})
</script>
