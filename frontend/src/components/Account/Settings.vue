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
        <SettingsNavItem value="mentions">
          <template #prefix>
            <span class="lucide-at-sign size-4 shrink-0 text-ink-gray-6" />
          </template>
          {{ __('Mention chips') }}
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

      <SettingsPanel value="mentions">
        <SettingsHeader
          :title="__('Mention chips')"
          :description="__('What a mentioned record shows to whoever reads the procedure')"
        >
          <template #actions>
            <Button icon-left="lucide-plus" :label="__('Add doctype')" @click="addMentionConfig" />
          </template>
        </SettingsHeader>
        <SettingsBody>
          <List
            v-if="configs.length"
            class="-mx-3 pt-4"
            :columns="['minmax(0,1fr)', '10rem', '6rem']"
            :row-height="52"
          >
            <ListHeader>
              <ListHeaderCell>{{ __('Doctype') }}</ListHeaderCell>
              <ListHeaderCell>{{ __('Status field') }}</ListHeaderCell>
              <ListHeaderCell>{{ __('State') }}</ListHeaderCell>
            </ListHeader>
            <ListRows :items="configs" v-slot="{ item: config }">
              <ListRow @click="editMentionConfig(config)">
                <ListCell>
                  <span class="truncate text-base text-ink-gray-8">{{ config.document_type }}</span>
                </ListCell>
                <ListCell>
                  <span class="truncate text-base text-ink-gray-6">
                    {{ config.status_field || 'None' }}
                  </span>
                </ListCell>
                <ListCell>
                  <Badge :theme="config.enabled ? 'green' : 'gray'" variant="subtle" size="sm">
                    {{ config.enabled ? 'On' : 'Off' }}
                  </Badge>
                </ListCell>
              </ListRow>
            </ListRows>
          </List>

          <p v-else class="px-3 py-10 text-center text-base text-ink-gray-5">
            {{ __('Nothing configured. Until a doctype is set up here, a mention reads as plain text.') }}
          </p>
        </SettingsBody>
      </SettingsPanel>
    </SettingsContent>
  </SettingsDialog>
</template>

<script setup>
import { computed, watch } from 'vue'
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

const mentionConfigs = createResource({
  url: 'frappe.client.get_list',
  makeParams: () => ({
    doctype: 'SOP Mention Config',
    fields: ['name', 'document_type', 'status_field', 'enabled'],
    limit_page_length: 50,
  }),
})

const configs = computed(() => mentionConfigs.data || [])

function newSpace() {
  open.value = false
  ui.spaceDialog = true
}

function addMentionConfig() {
  window.open('/app/sop-mention-config/new', '_blank')
}

function editMentionConfig(config) {
  window.open(`/app/sop-mention-config/${encodeURIComponent(config.name)}`, '_blank')
}

watch(open, (value) => {
  if (value) mentionConfigs.reload()
})
</script>
