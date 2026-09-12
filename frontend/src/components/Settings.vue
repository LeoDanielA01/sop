<script setup>
import { ref, watch } from 'vue'
import {
  Avatar,
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
} from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { spaces } from '@/data/navigation'
import { pageLength } from '@/data/procedures'
import { setTheme, theme } from '@/composables/useTheme'

const open = defineModel('open', { type: Boolean, default: false })
const tab = ref('spaces')

const rowsPerPage = ref(String(pageLength.value))
watch(rowsPerPage, (value) => (pageLength.value = Number(value)))

const emailOnApproval = ref(true)
const emailOnPublish = ref(true)
const digest = ref('Weekly')
</script>

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
              <Select
                :modelValue="theme"
                :options="[
                  { label: 'Light', value: 'light' },
                  { label: 'Dark', value: 'dark' },
                  { label: 'System Default', value: 'system' },
                ]"
                @update:modelValue="setTheme"
              >
                <template #item-prefix="{ item }">
                  <div
                    v-if="item.value === 'system'"
                    class="flex size-3 overflow-hidden rounded-full border border-outline-gray-2"
                  >
                    <div class="w-1/2 bg-white" />
                    <div class="w-1/2 bg-gray-950" />
                  </div>
                  <div
                    v-else
                    class="size-3 rounded-full border"
                    :class="
                      item.value === 'light'
                        ? 'border-outline-gray-2 bg-white'
                        : 'bg-gray-950'
                    "
                  />
                </template>
              </Select>
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
        <SettingsHeader title="Notifications" />
        <SettingsBody>
          <div class="divide-y divide-outline-gray-1 pt-6">
            <SettingsRow
              title="Approval requests"
              description="Email me when a procedure is waiting for my sign-off"
            >
              <Switch v-model="emailOnApproval" />
            </SettingsRow>
            <SettingsRow
              title="Newly effective procedures"
              description="Email me when a procedure I must follow comes into force"
            >
              <Switch v-model="emailOnPublish" />
            </SettingsRow>
            <SettingsRow title="Review digest" description="A summary of what is due for review">
              <Select v-model="digest" :options="['Off', 'Weekly', 'Monthly']" />
            </SettingsRow>
          </div>
        </SettingsBody>
      </SettingsPanel>

      <SettingsPanel value="spaces">
        <SettingsHeader title="Spaces">
          <template #actions>
            <Button icon-left="lucide-plus" label="New space" />
          </template>
        </SettingsHeader>
        <SettingsBody>
          <List class="-mx-3 pt-4" :columns="['minmax(0,1fr)', '8rem', '3rem']" :row-height="56">
            <ListHeader>
              <ListHeaderCell>Space</ListHeaderCell>
              <ListHeaderCell>Visibility</ListHeaderCell>
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
                <ListCell class="justify-end">
                  <Button variant="ghost" icon="lucide-ellipsis" label="Space options" />
                </ListCell>
              </ListRow>
            </ListRows>
          </List>
        </SettingsBody>
      </SettingsPanel>

      <SettingsPanel value="mentions">
        <SettingsHeader
          title="Mention chips"
          description="Choose what a mentioned record shows inside a procedure"
        >
          <template #actions>
            <Button icon-left="lucide-plus" label="Add doctype" />
          </template>
        </SettingsHeader>
        <SettingsBody>
          <p class="pt-6 text-base text-ink-gray-5">
            Phase 3 fills this: pick a doctype, a status field and up to three badges, and every
            mention of that record shows them — without a developer.
          </p>
        </SettingsBody>
      </SettingsPanel>
    </SettingsContent>
  </SettingsDialog>
</template>
