<template>
  <SettingsDialog v-model:open="open" v-model:tab="tab" size="5xl">
    <SettingsSidebar>
      <SettingsNavGroup label="My settings">
        <SettingsNavItem value="preferences">
          <template #prefix>
            <span class="lucide-sliders-horizontal size-4 shrink-0 text-ink-gray-6" />
          </template>
          Preferences
        </SettingsNavItem>
        <SettingsNavItem value="notifications">
          <template #prefix>
            <span class="lucide-bell size-4 shrink-0 text-ink-gray-6" />
          </template>
          Notifications
        </SettingsNavItem>
      </SettingsNavGroup>

      <SettingsNavGroup label="Administration">
        <SettingsNavItem value="spaces">
          <template #prefix>
            <span class="lucide-library size-4 shrink-0 text-ink-gray-6" />
          </template>
          Spaces
        </SettingsNavItem>
        <SettingsNavItem value="mentions">
          <template #prefix>
            <span class="lucide-at-sign size-4 shrink-0 text-ink-gray-6" />
          </template>
          Mention chips
        </SettingsNavItem>
      </SettingsNavGroup>
    </SettingsSidebar>

    <SettingsContent>
      <SettingsPanel value="preferences">
        <SettingsHeader title="Preferences" />
        <SettingsBody>
          <div class="divide-y divide-outline-gray-1 pt-6">
            <SettingsRow
              title="Appearance"
              description="Choose a light, dark, or system-matched interface"
            >
              <TabButtons
                :buttons="[
                  { label: 'Light', value: 'light' },
                  { label: 'Dark', value: 'dark' },
                  { label: 'System', value: 'system' },
                ]"
                :model-value="colorScheme"
                @update:model-value="setColorScheme"
              />
            </SettingsRow>
            <SettingsRow
              title="Reading width"
              description="How wide a procedure runs when you read it"
            >
              <TabButtons
                :buttons="[
                  { label: 'Comfortable', value: 'Comfortable' },
                  { label: 'Full', value: 'Full' },
                ]"
                :model-value="preferences.reading_width"
                @update:model-value="(value) => setPreference('reading_width', value)"
              />
            </SettingsRow>
            <SettingsRow
              title="Rows per page"
              description="How many procedures a list page shows before it pages"
            >
              <Select v-model="rowsPerPage" :options="['10', '20', '50', '100']" />
            </SettingsRow>
          </div>
        </SettingsBody>
      </SettingsPanel>

      <SettingsPanel value="notifications">
        <SettingsHeader
          title="Notifications"
          description="What reaches your inbox. Everything still shows in the app."
        />
        <SettingsBody>
          <div class="divide-y divide-outline-gray-1 pt-6">
            <SettingsRow
              title="Approval requests"
              description="When a procedure is waiting for your sign-off"
            >
              <Switch
                :model-value="!!preferences.email_on_approval"
                @update:model-value="(value) => setPreference('email_on_approval', value ? 1 : 0)"
              />
            </SettingsRow>
            <SettingsRow
              title="Newly effective procedures"
              description="When a procedure you have to follow comes into force"
            >
              <Switch
                :model-value="!!preferences.email_on_publish"
                @update:model-value="(value) => setPreference('email_on_publish', value ? 1 : 0)"
              />
            </SettingsRow>
            <SettingsRow
              title="Training reminders"
              description="Before training of yours falls overdue"
            >
              <Switch
                :model-value="!!preferences.email_on_training"
                @update:model-value="(value) => setPreference('email_on_training', value ? 1 : 0)"
              />
            </SettingsRow>
            <SettingsRow title="Review digest" description="A summary of what is due for review">
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
          title="Spaces"
          description="A space is a binder, and it numbers everything inside it"
        >
          <template #actions>
            <Button variant="solid" icon-left="lucide-plus" label="New space" @click="newSpace" />
          </template>
        </SettingsHeader>
        <SettingsBody>
          <List
            v-if="spaces.length"
            class="-mx-3 pt-4"
            :columns="['minmax(0,1fr)', '8rem', '8rem']"
            :row-height="56"
          >
            <ListHeader>
              <ListHeaderCell>Space</ListHeaderCell>
              <ListHeaderCell>Visibility</ListHeaderCell>
              <ListHeaderCell>Needs review</ListHeaderCell>
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
                  <span v-else class="text-base text-ink-gray-5">Up to date</span>
                </ListCell>
              </ListRow>
            </ListRows>
          </List>

          <p v-else class="px-3 py-10 text-center text-base text-ink-gray-5">
            No spaces yet. Create one and its code — QA, PROD, HR — becomes the procedure number.
          </p>
        </SettingsBody>
      </SettingsPanel>

      <SettingsPanel value="mentions">
        <SettingsHeader
          title="Mention chips"
          description="What a mentioned record shows to whoever reads the procedure"
        >
          <template #actions>
            <Button icon-left="lucide-plus" label="Add doctype" @click="addMentionConfig" />
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
              <ListHeaderCell>Doctype</ListHeaderCell>
              <ListHeaderCell>Status field</ListHeaderCell>
              <ListHeaderCell>State</ListHeaderCell>
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
            Nothing configured. Until a doctype is set up here, a mention reads as plain text.
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
import { useUI } from '@/stores/ui'
import { pageLength } from '@/data/procedures'
import { preferences, setPreference } from '@/data/preferences'

const open = defineModel('open', { type: Boolean, default: false })
const tab = ref('preferences')
const ui = useUI()

const { colorScheme, setColorScheme } = useColorScheme()

const rowsPerPage = computed({
  get: () => String(pageLength.value),
  set: (value) => (pageLength.value = Number(value)),
})

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
