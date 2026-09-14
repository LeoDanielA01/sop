<template>
  <Dialog v-model:open="open" size="xl" bare>
    <template #default>
      <div class="overflow-hidden rounded-4">
        <div class="relative h-16 bg-surface-gray-2">
          <Button
            class="absolute right-2 top-2"
            variant="ghost"
            icon="lucide-x"
            label="Close"
            @click="open = false"
          />
        </div>

        <div class="grid gap-5 px-5 pb-5 sm:grid-cols-[14rem_minmax(0,1fr)]">
          <div class="min-w-0">
            <Avatar
              :image="session.user.image"
              :label="session.user.full_name"
              size="3xl"
              class="-mt-8 ring-4 ring-surface-base"
            />

            <p class="mt-2.5 truncate text-lg font-semibold text-ink-gray-9">
              {{ session.user.full_name }}
            </p>
            <p class="truncate text-sm text-ink-gray-5">{{ session.user.name }}</p>

            <div class="mt-3 flex flex-wrap gap-1.5">
              <Badge variant="subtle" size="sm">{{ role }}</Badge>
              <Badge v-for="team in teams" :key="team.name" variant="subtle" size="sm">
                {{ team.name }}
              </Badge>
            </div>

            <p v-if="stats.data?.member_since" class="mt-3 text-sm text-ink-gray-5">
              Here since {{ shortDate(stats.data.member_since) }}
            </p>

            <div class="mt-4">
              <FormLabel label="Language" />
              <Select
                class="mt-1.5"
                :options="languageOptions"
                :modelValue="language"
                :disabled="switching.loading"
                @update:modelValue="pickLanguage"
              />
              <p class="mt-1.5 text-sm text-ink-gray-5">The app reloads when you change it.</p>
            </div>

            <div class="mt-4 flex flex-wrap items-center gap-1">
              <Tooltip text="Settings">
                <Button
                  variant="ghost"
                  icon="lucide-settings"
                  label="Settings"
                  @click="openSettings"
                />
              </Tooltip>
              <Tooltip :text="dark ? 'Switch to light' : 'Switch to dark'">
                <Button
                  variant="ghost"
                  :icon="dark ? 'lucide-sun' : 'lucide-moon'"
                  :label="dark ? 'Switch to light' : 'Switch to dark'"
                  @click="setColorScheme(dark ? 'light' : 'dark')"
                />
              </Tooltip>
              <Tooltip text="Open the desk">
                <Button
                  variant="ghost"
                  icon="lucide-layout-grid"
                  label="Open the desk"
                  @click="openDesk"
                />
              </Tooltip>
              <Tooltip text="Log out">
                <Button
                  variant="ghost"
                  icon="lucide-log-out"
                  label="Log out"
                  @click="session.logout()"
                />
              </Tooltip>
            </div>
          </div>

          <div class="min-w-0 pt-3">
            <p class="mb-2 text-sm text-ink-gray-5">Your work — pick one to go there</p>

            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="row in lines"
                :key="row.label"
                type="button"
                class="flex items-center gap-2.5 rounded-4 border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5 text-left hover:border-outline-gray-3"
                @click="visit(row)"
              >
                <span
                  :class="[row.icon, row.tone || 'text-ink-gray-5']"
                  class="size-4 shrink-0"
                  aria-hidden="true"
                />
                <span class="min-w-0 flex-1">
                  <span
                    class="block text-lg font-semibold tabular-nums"
                    :class="row.tone || 'text-ink-gray-8'"
                  >
                    {{ row.value }}
                  </span>
                  <span class="block truncate text-sm text-ink-gray-5">{{ row.label }}</span>
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Avatar,
  Badge,
  Button,
  Dialog,
  FormLabel,
  Select,
  Tooltip,
  createResource,
  useColorScheme,
} from 'frappe-ui'
import { session } from '@/data/session'
import { useUI } from '@/stores/ui'
import { shortDate } from '@/utils/format'

const open = defineModel('open', { type: Boolean, default: false })

const router = useRouter()
const ui = useUI()
const { colorScheme, setColorScheme } = useColorScheme()

const stats = createResource({ url: 'sop.api.session.stats' })

const languages = createResource({ url: 'sop.api.i18n.languages' })
const chosen = createResource({ url: 'sop.api.i18n.current' })

const switching = createResource({
  url: 'sop.api.i18n.set_language',
  onSuccess: () => window.location.reload(),
})

const language = computed(() => chosen.data || 'en')

const languageOptions = computed(() => languages.data || [{ label: 'English', value: 'en' }])

function pickLanguage(value) {
  if (!value || value === language.value) return

  switching.submit({ language: value })
}

const dark = computed(() => colorScheme.value === 'dark')
const teams = computed(() => stats.data?.teams || [])

const role = computed(() => {
  if (session.user.is_manager) return 'Manager'
  if (session.user.is_author) return 'Author'

  return 'Reader'
})

const lines = computed(() => {
  const data = stats.data || {}

  return [
    {
      label: 'Waiting on you',
      value: data.waiting ?? 0,
      icon: 'lucide-inbox',
      route: '/?view=approval',
    },
    {
      label: 'Procedures you own',
      value: data.owned ?? 0,
      icon: 'lucide-file-text',
      route: '/',
    },
    {
      label: 'Drafts you started',
      value: data.drafts ?? 0,
      icon: 'lucide-pencil-line',
      route: '/?view=drafts',
    },
    {
      label: 'You signed off',
      value: data.signed ?? 0,
      icon: 'lucide-check-check',
      route: '/?view=unacknowledged',
    },
    {
      label: 'Training open',
      value: data.training_open ?? 0,
      icon: 'lucide-graduation-cap',
      route: '/training',
    },
    {
      label: 'Training overdue',
      value: data.training_overdue ?? 0,
      icon: 'lucide-calendar-clock',
      tone: data.training_overdue ? 'text-ink-red-3' : null,
      route: '/training',
    },
  ]
})

function visit(row) {
  if (!row.route) return

  open.value = false
  router.push(row.route)
}

function openDesk() {
  window.open('/app/sop', '_blank')
}

function openSettings() {
  open.value = false
  ui.openSettings('preferences')
}

watch(open, (value) => {
  if (!value) return

  stats.reload()
  languages.reload()
  chosen.reload()
})
</script>
