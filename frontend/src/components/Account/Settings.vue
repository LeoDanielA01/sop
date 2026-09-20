<template>
  <SettingsDialog v-model:open="open" v-model:tab="ui.settingsTab" size="5xl">
    <SettingsSidebar>
      <SettingsNavGroup :label="__('My settings')">
        <SettingsNavItem value="preferences">
          <template #prefix>
            <span class="lucide-sliders-horizontal size-4 shrink-0 text-ink-gray-6" />
          </template>
          {{ __('Preferences') }}
        </SettingsNavItem>
        <SettingsNavItem value="shortcuts">
          <template #prefix>
            <span class="lucide-keyboard size-4 shrink-0 text-ink-gray-6" />
          </template>
          {{ __('Shortcuts') }}
        </SettingsNavItem>
        <SettingsNavItem value="notifications">
          <template #prefix>
            <span class="lucide-bell size-4 shrink-0 text-ink-gray-6" />
          </template>
          {{ __('Notifications') }}
        </SettingsNavItem>
      </SettingsNavGroup>

      <SettingsNavGroup :label="__('Administration')">
        <SettingsNavItem value="spaces">
          <template #prefix>
            <span class="lucide-book-text size-4 shrink-0 text-ink-gray-6" />
          </template>
          {{ __('Spaces') }}
        </SettingsNavItem>
        <SettingsNavItem v-if="session.user.is_manager" value="organisation">
          <template #prefix>
            <span class="lucide-building-2 size-4 shrink-0 text-ink-gray-6" />
          </template>
          {{ __('Organisation') }}
        </SettingsNavItem>
        <SettingsNavItem v-if="session.user.is_admin" value="demo">
          <template #prefix>
            <span class="lucide-flask-conical size-4 shrink-0 text-ink-gray-6" />
          </template>
          {{ __('Demo data') }}
        </SettingsNavItem>
      </SettingsNavGroup>
    </SettingsSidebar>

    <SettingsContent>
      <SettingsPanel value="preferences">
        <SettingsHeader :title="__('Preferences')" />
        <SettingsBody>
          <ErrorMessage :message="preferencesError" class="pt-4" />

          <div class="divide-y divide-outline-gray-1 pt-6">
            <SettingsRow
              :title="__('Appearance')"
              :description="__('Choose a light, dark, or system-matched interface')"
            >
              <TabButtons
                :options="[
                  { label: 'Light', value: 'light' },
                  { label: 'Dark', value: 'dark' },
                  { label: 'System', value: 'system' },
                ]"
                :model-value="colorScheme"
                @update:model-value="setColorScheme"
              />
            </SettingsRow>
            <SettingsRow
              :title="__('Save as you type')"
              :description="__('Keep a draft saved a couple of seconds after you stop typing')"
            >
              <Switch
                :model-value="!!preferences.autosave"
                @update:model-value="(value) => setPreference('autosave', value ? 1 : 0)"
              />
            </SettingsRow>
            <SettingsRow
              :title="__('Rows per page')"
              :description="__('How many procedures a list page shows before it pages')"
            >
              <Select
                :model-value="String(preferences.rows_per_page)"
                :options="['10', '20', '50', '100']"
                @update:model-value="(value) => setPreference('rows_per_page', Number(value))"
              />
            </SettingsRow>
          </div>
        </SettingsBody>
      </SettingsPanel>

      <SettingsPanel value="shortcuts">
        <SettingsHeader
          :title="__('Shortcuts')"
          :description="__('Press Ctrl and / anywhere to bring this list up')"
        />
        <SettingsBody>
          <div class="divide-y divide-outline-gray-1 pt-6">
            <SettingsRow
              :title="__('Creating and jumping around')"
              :description="__('The Ctrl combinations under Do and Go to. Search, sidebar and save always work.')"
            >
              <Switch
                :model-value="!!preferences.shortcuts"
                @update:model-value="(value) => setPreference('shortcuts', value ? 1 : 0)"
              />
            </SettingsRow>
          </div>

          <div class="mt-6 flex flex-col gap-5">
            <div v-for="group in groups" :key="group.name">
              <p class="mb-2 text-sm text-ink-gray-5">{{ __(group.name) }}</p>

              <div class="divide-y divide-outline-gray-1 rounded-4 border border-outline-gray-2">
                <div
                  v-for="row in group.rows"
                  :key="row.label"
                  class="flex items-center justify-between gap-4 px-3 py-2"
                >
                  <span class="min-w-0 truncate text-base text-ink-gray-7">{{ __(row.label) }}</span>

                  <span class="flex shrink-0 items-center gap-1">
                    <kbd
                      v-for="key in row.keys"
                      :key="key"
                      class="rounded-3 bg-surface-gray-2 px-1.5 py-0.5 font-mono text-xs text-ink-gray-7"
                    >
                      {{ KEYS[key] || key }}
                    </kbd>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </SettingsBody>
      </SettingsPanel>

      <SettingsPanel value="notifications">
        <SettingsHeader
          :title="__('Notifications')"
          :description="__('What reaches your inbox. Everything still shows in the app.')"
        />
        <SettingsBody>
          <div class="divide-y divide-outline-gray-1 pt-6">
            <SettingsRow
              :title="__('Approval requests')"
              :description="__('When a procedure is waiting for your sign-off')"
            >
              <Switch
                :model-value="!!preferences.email_on_approval"
                @update:model-value="(value) => setPreference('email_on_approval', value ? 1 : 0)"
              />
            </SettingsRow>
            <SettingsRow
              :title="__('Newly effective procedures')"
              :description="__('When a procedure you have to follow comes into force')"
            >
              <Switch
                :model-value="!!preferences.email_on_publish"
                @update:model-value="(value) => setPreference('email_on_publish', value ? 1 : 0)"
              />
            </SettingsRow>
            <SettingsRow
              :title="__('Training reminders')"
              :description="__('Before training of yours falls overdue')"
            >
              <Switch
                :model-value="!!preferences.email_on_training"
                @update:model-value="(value) => setPreference('email_on_training', value ? 1 : 0)"
              />
            </SettingsRow>
            <SettingsRow :title="__('Review digest')" :description="__('A summary of what is due for review')">
              <Select
                :model-value="preferences.digest"
                :options="['Off', 'Weekly', 'Monthly']"
                @update:model-value="(value) => setPreference('digest', value)"
              />
            </SettingsRow>
          </div>
        </SettingsBody>
      </SettingsPanel>

      <SettingsPanel value="spaces">
        <SettingsHeader
          :title="__('Spaces')"
          :description="__('A space is a binder, and it numbers everything inside it')"
        >
          <template #actions>
            <Button variant="solid" icon-left="lucide-plus" :label="__('New space')" @click="newSpace" />
          </template>
        </SettingsHeader>
        <SettingsBody>
          <List
            v-if="spaces.length"
            class="-mx-3 pt-4"
            :columns="['minmax(0,1fr)', '8rem', '8rem', '3rem']"
            :row-height="56"
          >
            <ListHeader>
              <ListHeaderCell>{{ __('Space') }}</ListHeaderCell>
              <ListHeaderCell>{{ __('Visibility') }}</ListHeaderCell>
              <ListHeaderCell>{{ __('Needs review') }}</ListHeaderCell>
              <ListHeaderCell />
            </ListHeader>
            <ListRows :items="spaces" v-slot="{ item: space }">
              <ListRow>
                <ListCell>
                  <Avatar :label="space.title" size="xl" shape="square" />
                  <div class="ml-3 min-w-0">
                    <div class="truncate text-base text-ink-gray-8">{{ space.title }}</div>
                    <div class="mt-0.5 truncate text-sm text-ink-gray-5">
                      {{ space.space_code }} · {{ space.total }} procedures
                    </div>
                  </div>
                </ListCell>
                <ListCell>
                  <span class="text-base text-ink-gray-7">{{ space.visibility }}</span>
                </ListCell>
                <ListCell>
                  <Badge v-if="space.overdue" theme="red" variant="subtle" size="sm">
                    {{ space.overdue }} overdue
                  </Badge>
                  <span v-else class="text-base text-ink-gray-5">{{ __('Up to date') }}</span>
                </ListCell>
                <ListCell>
                  <Button
                    v-if="session.user.is_manager"
                    variant="ghost"
                    icon="lucide-trash-2"
                    :label="__('Delete space')"
                    @click="ui.removeSpace = { name: space.name }"
                  />
                </ListCell>
              </ListRow>
            </ListRows>
          </List>

          <p v-else class="px-3 py-10 text-center text-base text-ink-gray-5">
            {{ __('No spaces yet. Create one and its code — QA, PROD, HR — becomes the procedure number.') }}
          </p>
        </SettingsBody>
      </SettingsPanel>

      <SettingsPanel value="organisation">
        <SettingsHeader
          :title="__('Organisation')"
          :description="__('Rules that fit how your organisation must work. Start from a profile, then adjust.')"
        />
        <SettingsBody>
          <ErrorMessage class="mt-4" :message="organisationError" />

          <div class="divide-y divide-outline-gray-1 pt-6">
            <SettingsRow
              :title="__('Profile')"
              :description="__('A starting point. Picking one fills in the settings below.')"
            >
              <Select
                class="w-56"
                :options="profileOptions"
                :modelValue="org.profile"
                @update:modelValue="applyProfile"
              />
            </SettingsRow>
            <SettingsRow
              :title="__('Writing language')"
              :description="__('Which rules the clarity check uses. Automatic follows each person’s language.')"
            >
              <Select
                class="w-56"
                :options="languageOptions"
                :modelValue="org.writing_language || ''"
                @update:modelValue="(value) => saveOrganisation({ writing_language: value })"
              />
            </SettingsRow>
            <SettingsRow
              :title="__('Allow permanent deletion')"
              :description="__('Switch off if every record must be kept, for example by a public body with archiving duties.')"
            >
              <Switch
                :model-value="!!org.allow_permanent_delete"
                @update:model-value="(value) => saveOrganisation({ allow_permanent_delete: value ? 1 : 0 })"
              />
            </SettingsRow>
            <SettingsRow
              :title="__('Show week numbers')"
              :description="__('Adds the week to dates, for example 16 Sep 2026 · wk 38.')"
            >
              <Switch
                :model-value="!!org.show_week_numbers"
                @update:model-value="(value) => saveOrganisation({ show_week_numbers: value ? 1 : 0 })"
              />
            </SettingsRow>
          </div>
        </SettingsBody>
      </SettingsPanel>
      <SettingsPanel value="demo">
        <SettingsHeader
          :title="__('Demo data')"
          :description="__('A worked example — two spaces of procedures about this app, with people, training and history. Safe to remove once you have your own.')"
        />
        <SettingsBody>
          <ErrorMessage class="mt-4" :message="demoError" />

          <div class="mt-6 rounded-4 border border-outline-gray-2">
            <div class="flex items-center gap-3 border-b border-outline-gray-1 px-4 py-3">
              <span
                :class="demo.installed ? 'lucide-circle-check text-ink-green-3' : 'lucide-circle-dashed text-ink-gray-4'"
                class="size-4 shrink-0"
                aria-hidden="true"
              />
              <span class="min-w-0 flex-1 text-base text-ink-gray-8">
                {{ demo.installed ? __('Demo data is installed') : __('No demo data on this site') }}
              </span>
              <Button
                variant="ghost"
                icon-left="lucide-refresh-cw"
                :label="__('Refresh')"
                :loading="demoOverview.loading"
                @click="demoOverview.reload()"
              />
            </div>

            <dl v-if="demo.installed" class="grid grid-cols-2 gap-px bg-surface-gray-2 sm:grid-cols-4">
              <div v-for="row in demoCounts" :key="row.label" class="bg-surface-base px-4 py-3">
                <dt class="text-sm text-ink-gray-5">{{ __(row.label) }}</dt>
                <dd class="mt-0.5 text-lg font-medium text-ink-gray-9">{{ row.value }}</dd>
              </div>
            </dl>

            <p v-if="demo.installed" class="border-t border-outline-gray-1 px-4 py-3 text-sm text-ink-gray-6">
              {{ __('Spaces') }}: <span class="text-ink-gray-8">{{ demoSpaceList }}</span>
            </p>
          </div>

          <div class="divide-y divide-outline-gray-1 pt-2">
            <SettingsRow
              v-if="!demo.installed"
              :title="__('Insert the demo data')"
              :description="__('Creates the two spaces, four example people, and fourteen procedures at every stage from draft to retired.')"
            >
              <Button
                variant="solid"
                icon-left="lucide-plus"
                :label="__('Insert demo data')"
                :loading="seeding.loading"
                @click="seeding.submit()"
              />
            </SettingsRow>

            <SettingsRow
              v-if="demo.installed"
              :title="__('Rebuild it')"
              :description="__('Removes the demo data and creates it again from the current version. Use this after an update to pick up new example content.')"
            >
              <Button
                icon-left="lucide-refresh-ccw"
                :label="__('Rebuild')"
                :loading="rebuilding.loading"
                @click="rebuilding.submit()"
              />
            </SettingsRow>

            <SettingsRow
              v-if="demo.installed"
              :title="__('Remove it')"
              :description="__('Deletes the demo spaces and everything filed in them. Your own spaces are untouched.')"
            >
              <Button
                v-if="!confirmingRemoval"
                theme="red"
                icon-left="lucide-trash-2"
                :label="__('Remove demo data')"
                @click="confirmingRemoval = true"
              />
              <div v-else class="flex items-center gap-2">
                <Button :label="__('Cancel')" @click="confirmingRemoval = false" />
                <Button
                  variant="solid"
                  theme="red"
                  :label="__('Yes, remove it')"
                  :loading="removing.loading"
                  @click="removing.submit()"
                />
              </div>
            </SettingsRow>
          </div>

          <div
            v-if="confirmingRemoval"
            class="mt-4 rounded-3 border border-outline-red-2 bg-surface-red-1 px-4 py-3 text-sm text-ink-red-6"
          >
            <p class="font-medium">{{ __('This cannot be undone.') }}</p>
            <p class="mt-1">
              {{
                __(
                  'It deletes {0} procedures in the demo spaces, with their revisions, approvals, comments, acknowledgements and training. It leaves the four example user accounts and the All Staff team in place.',
                ).format(demo.procedures || 0)
              }}
            </p>
            <p v-if="demo.other_spaces" class="mt-1">
              {{ __('Your other {0} spaces are not touched.').format(demo.other_spaces) }}
            </p>
          </div>

          <p class="mt-4 text-sm text-ink-gray-5">
            {{ __('Inserting or rebuilding walks every procedure through its full lifecycle, so it can take a minute. Leave the dialog open until it finishes.') }}
          </p>
        </SettingsBody>
      </SettingsPanel>
    </SettingsContent>
  </SettingsDialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import {
  Avatar,
  Badge,
  Button,
  ErrorMessage,
  Select,
  SettingsBody,
  SettingsContent,
  SettingsDialog,
  SettingsHeader,
  SettingsNavGroup,
  SettingsNavItem,
  SettingsPanel,
  SettingsRow,
  SettingsSidebar,
  Switch,
  TabButtons,
  createResource,
  useColorScheme,
} from 'frappe-ui'

import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { spaces } from '@/data/navigation'
import { session } from '@/data/session'
import { useUI } from '@/stores/ui'
import { preferences, preferencesError, setPreference } from '@/data/preferences'
import { SHORTCUTS } from '@/composables/useShortcuts'

const open = defineModel('open', { type: Boolean, default: false })
const ui = useUI()

const org = ref({})
const demo = ref({})
const confirmingRemoval = ref(false)

function adopt(data) {
  org.value = data || {}
  Object.assign(session.user, data?.resolved || {})
}

function adoptDemo(data) {
  demo.value = data || {}
  confirmingRemoval.value = false
}

const demoOverview = createResource({ url: 'sop.api.demo.overview', onSuccess: adoptDemo })
const seeding = createResource({ url: 'sop.api.demo.seed', onSuccess: adoptDemo })
const removing = createResource({ url: 'sop.api.demo.remove', onSuccess: adoptDemo })
const rebuilding = createResource({ url: 'sop.api.demo.rebuild', onSuccess: adoptDemo })

const demoError = computed(
  () =>
    seeding.error?.messages?.[0] ||
    removing.error?.messages?.[0] ||
    rebuilding.error?.messages?.[0] ||
    demoOverview.error?.messages?.[0],
)

const demoSpaceList = computed(() =>
  (demo.value.spaces || []).map((space) => `${space.title} (${space.space_code})`).join(', '),
)

const demoCounts = computed(() => [
  { label: 'Procedures', value: demo.value.procedures || 0 },
  { label: 'Processes', value: demo.value.processes || 0 },
  { label: 'Training assignments', value: demo.value.assignments || 0 },
  { label: 'Example people', value: (demo.value.people || []).length },
])

const organisation = createResource({ url: 'sop.api.settings.get', onSuccess: adopt })
const saving = createResource({ url: 'sop.api.settings.save', onSuccess: adopt })
const applying = createResource({ url: 'sop.api.settings.apply_profile', onSuccess: adopt })

const organisationError = computed(
  () =>
    saving.error?.messages?.[0] ||
    applying.error?.messages?.[0] ||
    organisation.error?.messages?.[0],
)

const profileOptions = computed(() =>
  (org.value.profiles || []).map((name) => ({ label: __(name), value: name })),
)

const languageOptions = computed(() => [
  { label: __('Automatic'), value: '' },
  ...(org.value.languages || []),
])

function saveOrganisation(values) {
  saving.submit({ values })
}

function applyProfile(profile) {
  if (profile && profile !== org.value.profile) applying.submit({ profile })
}

watch(open, (value) => {
  if (!value) {
    confirmingRemoval.value = false
    return
  }

  if (session.user.is_manager) organisation.reload()
  if (session.user.is_admin) demoOverview.reload()
})

const onMac = navigator.platform.toLowerCase().includes('mac')

const KEYS = {
  mod: onMac ? '⌘' : 'Ctrl',
  alt: onMac ? '⌥' : 'Alt',
  shift: onMac ? '⇧' : 'Shift',
}

const groups = computed(() => {
  const names = [...new Set(SHORTCUTS.map((row) => row.group))]

  return names.map((name) => ({
    name,
    rows: SHORTCUTS.filter((row) => row.group === name),
  }))
})

const { colorScheme, setColorScheme } = useColorScheme()

function newSpace() {
  open.value = false
  ui.spaceDialog = true
}

</script>
