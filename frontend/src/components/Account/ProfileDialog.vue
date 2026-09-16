<template>
  <Dialog v-model:open="open" size="xl" bare>
    <template #default>
      <div class="overflow-hidden rounded-4">
       
        <div class="relative h-20 bg-gradient-to-br from-blue-600 via-indigo-500 to-purple-600">
          <Button
            class="absolute right-2 top-2"
            variant="ghost"
            icon="lucide-x"
            :label="__('Close')"
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
              <Badge
                v-for="team in teams"
                :key="team.name"
                variant="subtle"
                size="sm"
              >{{ team.name }}</Badge>
            </div>

            <p v-if="profile.data?.member_since" class="mt-3 text-sm text-ink-gray-5">
              Here since {{ shortDate(profile.data.member_since) }}
            </p>

            <div class="mt-4">
              <FormLabel :label="__('Language')" />
              <Select
                class="mt-1.5"
                :options="languageOptions"
                :modelValue="language"
                :disabled="switching.loading"
                @update:modelValue="pickLanguage"
              />
              <p class="mt-1.5 text-sm text-ink-gray-5">{{ __('The app reloads when you change it.') }}</p>
            </div>

            <div class="mt-4 flex flex-wrap items-center gap-1">
              <Tooltip :text="__('Settings')">
                <Button
                  variant="ghost"
                  icon="lucide-settings"
                  :label="__('Settings')"
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
              <Tooltip :text="__('Open the desk')">
                <Button
                  variant="ghost"
                  icon="lucide-layout-grid"
                  :label="__('Open the desk')"
                  @click="openDesk"
                />
              </Tooltip>
              <Tooltip :text="__('Log out')">
                <Button
                  variant="ghost"
                  icon="lucide-log-out"
                  :label="__('Log out')"
                  @click="session.logout()"
                />
              </Tooltip>
            </div>
          </div>

          
          <div class="min-w-0 pt-3">
          
            <div class="mb-4 flex gap-1 border-b border-outline-gray-2">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                type="button"
                class="profile-tab"
                :class="{ 'profile-tab--active': activeTab === tab.id }"
                @click="activeTab = tab.id"
              >
                {{ __(tab.label) }}
              </button>
            </div>

           
            <div v-if="activeTab === 'about'" class="space-y-3">
              <div v-if="profile.data?.bio" class="text-sm text-ink-gray-7 leading-relaxed">
                {{ profile.data.bio }}
              </div>
              <div v-else class="text-sm text-ink-gray-4 italic">{{ __('No bio yet.') }}</div>

              <div class="grid gap-2.5">
                <div
                  v-if="profile.data?.email"
                  class="flex items-center gap-2.5 text-sm"
                >
                  <span class="lucide-mail size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
                  <span class="text-ink-gray-5 w-16 shrink-0">{{ __('Email') }}</span>
                  <span class="truncate text-ink-gray-8">{{ profile.data.email }}</span>
                </div>
                <div
                  v-if="profile.data?.phone"
                  class="flex items-center gap-2.5 text-sm"
                >
                  <span class="lucide-phone size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
                  <span class="text-ink-gray-5 w-16 shrink-0">{{ __('Phone') }}</span>
                  <span class="truncate text-ink-gray-8">{{ profile.data.phone }}</span>
                </div>
                <div
                  v-if="profile.data?.mobile_no"
                  class="flex items-center gap-2.5 text-sm"
                >
                  <span class="lucide-smartphone size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
                  <span class="text-ink-gray-5 w-16 shrink-0">{{ __('Mobile') }}</span>
                  <span class="truncate text-ink-gray-8">{{ profile.data.mobile_no }}</span>
                </div>
                <div
                  v-if="profile.data?.location"
                  class="flex items-center gap-2.5 text-sm"
                >
                  <span class="lucide-map-pin size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
                  <span class="text-ink-gray-5 w-16 shrink-0">{{ __('Location') }}</span>
                  <span class="truncate text-ink-gray-8">{{ profile.data.location }}</span>
                </div>
                <div
                  v-if="profile.data?.username"
                  class="flex items-center gap-2.5 text-sm"
                >
                  <span class="lucide-at-sign size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
                  <span class="text-ink-gray-5 w-16 shrink-0">{{ __('Username') }}</span>
                  <span class="truncate text-ink-gray-8">{{ profile.data.username }}</span>
                </div>
                <div
                  v-if="profile.data?.member_since"
                  class="flex items-center gap-2.5 text-sm"
                >
                  <span class="lucide-calendar size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
                  <span class="text-ink-gray-5 w-16 shrink-0">{{ __('Joined') }}</span>
                  <span class="truncate text-ink-gray-8">{{ shortDate(profile.data.member_since) }}</span>
                </div>
                <div
                  v-if="profile.data?.last_active"
                  class="flex items-center gap-2.5 text-sm"
                >
                  <span class="lucide-clock size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
                  <span class="text-ink-gray-5 w-16 shrink-0">{{ __('Last seen') }}</span>
                  <span class="truncate text-ink-gray-8">{{ shortDate(profile.data.last_active) }}</span>
                </div>
              </div>
            </div>

           
            <div v-else-if="activeTab === 'teams'">
              <div v-if="teams.length" class="space-y-2">
                <div
                  v-for="team in teams"
                  :key="team.name"
                  class="flex items-center gap-3 rounded-3 border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5"
                >
                  <span class="lucide-users size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
                  <div class="min-w-0 flex-1">
                    <p class="truncate text-sm font-medium text-ink-gray-8">{{ team.name }}</p>
                    <p v-if="team.role" class="truncate text-xs text-ink-gray-5">{{ team.role }}</p>
                  </div>
                </div>
              </div>
              <p v-else class="text-sm text-ink-gray-4 italic">{{ __('Not a member of any team.') }}</p>
            </div>

          
            <div v-else-if="activeTab === 'activity'">
              <div class="grid grid-cols-2 gap-2">
                <div
                  v-for="stat in activityStats"
                  :key="stat.label"
                  class="flex flex-col gap-1 rounded-3 border border-outline-gray-2 bg-surface-gray-1 px-3 py-2.5"
                >
                  <span
                    :class="[stat.icon, stat.tone || 'text-ink-gray-5']"
                    class="size-4 shrink-0"
                    aria-hidden="true"
                  />
                  <span
                    class="text-xl font-bold tabular-nums"
                    :class="stat.tone || 'text-ink-gray-8'"
                  >{{ stat.value }}</span>
                  <span class="text-xs text-ink-gray-5 leading-tight">{{ stat.label }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
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
import { translate as __ } from '@/translation'

const open = defineModel('open', { type: Boolean, default: false })

const ui = useUI()
const { colorScheme, setColorScheme } = useColorScheme()

const profile = createResource({ url: 'sop.api.session.profile' })
const stats   = createResource({ url: 'sop.api.session.stats' })

const languages = createResource({ url: 'sop.api.i18n.languages' })
const chosen    = createResource({ url: 'sop.api.i18n.current' })

const switching = createResource({
  url: 'sop.api.i18n.set_language',
  onSuccess: () => window.location.reload(),
})

const language        = computed(() => chosen.data || 'en')
const languageOptions = computed(() => languages.data || [{ label: 'English', value: 'en' }])

function pickLanguage(value) {
  if (!value || value === language.value) return
  switching.submit({ language: value })
}

const dark  = computed(() => colorScheme.value === 'dark')
const teams = computed(() => profile.data?.teams || [])

const role = computed(() => {
  if (session.user.is_manager) return 'Manager'
  if (session.user.is_author)  return 'Author'
  return 'Reader'
})

const tabs = [
  { id: 'about',    label: 'About'    },
  { id: 'teams',    label: 'Teams'    },
  { id: 'activity', label: 'Activity' },
]
const activeTab = ref('about')


const activityStats = computed(() => {
  const data = stats.data || {}
  return [
    { label: __('Waiting on you'),     value: data.waiting          ?? 0, icon: 'lucide-inbox' },
    { label: __('Procedures you own'), value: data.owned            ?? 0, icon: 'lucide-file-text' },
    { label: __('Drafts started'),     value: data.drafts           ?? 0, icon: 'lucide-pencil-line' },
    { label: __('Signed off'),         value: data.signed           ?? 0, icon: 'lucide-check-check' },
    { label: __('Training open'),      value: data.training_open    ?? 0, icon: 'lucide-graduation-cap' },
    {
      label: __('Training overdue'),
      value: data.training_overdue ?? 0,
      icon: 'lucide-calendar-clock',
      tone: data.training_overdue ? 'text-ink-red-3' : null,
    },
  ]
})

function openDesk() {
  window.open('/app/sop', '_blank')
}

function openSettings() {
  open.value = false
  ui.openSettings('preferences')
}

watch(open, (value) => {
  if (!value) return
  profile.reload()
  stats.reload()
  languages.reload()
  chosen.reload()
})
</script>


<style scoped>
.profile-tab {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--ink-gray-5, #6b7280);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
  background: none;
  cursor: pointer;
}
.profile-tab:hover {
  color: var(--ink-gray-8, #1f2937);
}
.profile-tab--active {
  color: var(--ink-gray-9, #111827);
  border-bottom-color: var(--ink-gray-9, #111827);
  font-weight: 600;
}
</style>
