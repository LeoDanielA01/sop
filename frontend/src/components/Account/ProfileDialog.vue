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

        <div class="px-5 pb-5">
          <div class="flex items-end gap-4">
            <Avatar
              :image="session.user.image"
              :label="session.user.full_name"
              size="3xl"
              class="-mt-8 shrink-0 ring-4 ring-surface-base"
            />
            <div class="min-w-0 flex-1 pb-0.5">
              <p class="truncate text-lg font-semibold text-ink-gray-9">{{ session.user.full_name }}</p>
              <p class="truncate text-sm text-ink-gray-5">{{ data.email || session.user.name }}</p>
            </div>
            <Badge v-if="data.role" variant="subtle" size="sm" class="mb-1 shrink-0">
              {{ __(data.role) }}
            </Badge>
          </div>

          <div v-if="profile.loading && !profile.data" class="mt-6 flex flex-col gap-3">
            <Skeleton class="h-4 w-2/3 rounded-2" />
            <Skeleton class="h-4 w-1/2 rounded-2" />
            <Skeleton class="h-16 w-full rounded-3" />
          </div>

          <ErrorMessage v-else-if="profile.error" class="mt-6" :message="profile.error.messages?.[0]" />

          <div v-else class="mt-5 grid gap-6 sm:grid-cols-2">
            <section class="sm:col-span-2">
              <h3 class="mb-1.5 text-sm font-medium text-ink-gray-5">{{ __('About') }}</h3>
              <p v-if="data.bio" class="whitespace-pre-line text-base leading-relaxed text-ink-gray-8">
                {{ data.bio }}
              </p>
              <p v-else class="text-base italic text-ink-gray-4">{{ __('No bio yet.') }}</p>
            </section>

            <section>
              <h3 class="mb-2 text-sm font-medium text-ink-gray-5">{{ __('Contact') }}</h3>
              <dl class="flex flex-col gap-2">
                <div v-for="row in contact" :key="row.label" class="flex items-center gap-2.5 text-base">
                  <span :class="row.icon" class="size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
                  <dt class="sr-only">{{ __(row.label) }}</dt>
                  <dd class="min-w-0 truncate text-ink-gray-8">{{ row.value }}</dd>
                </div>
                <p v-if="!contact.length" class="text-base italic text-ink-gray-4">
                  {{ __('No contact details yet.') }}
                </p>
              </dl>
            </section>

            <section>
              <h3 class="mb-2 text-sm font-medium text-ink-gray-5">{{ __('Account') }}</h3>
              <dl class="flex flex-col gap-2">
                <div v-for="row in account" :key="row.label" class="flex items-baseline gap-2.5 text-base">
                  <dt class="w-20 shrink-0 text-sm text-ink-gray-5">{{ __(row.label) }}</dt>
                  <dd class="min-w-0 truncate text-ink-gray-8">{{ row.value }}</dd>
                </div>
              </dl>
            </section>

            <section>
              <h3 class="mb-2 text-sm font-medium text-ink-gray-5">{{ __('What you can do here') }}</h3>
              <ul v-if="roles.length" class="flex flex-col gap-2">
                <li v-for="row in roles" :key="row.name" class="flex items-start gap-2.5">
                  <span :class="row.icon" class="mt-0.5 size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
                  <span class="min-w-0">
                    <span class="block text-base text-ink-gray-8">{{ __(row.name) }}</span>
                    <span class="block text-sm text-ink-gray-5">{{ __(row.hint) }}</span>
                  </span>
                </li>
              </ul>
              <p v-else class="text-base italic text-ink-gray-4">{{ __('No roles in this app yet.') }}</p>
            </section>

            <section>
              <h3 class="mb-2 text-sm font-medium text-ink-gray-5">{{ __('Teams') }}</h3>
              <ul v-if="teams.length" class="flex flex-col gap-2">
                <li
                  v-for="team in teams"
                  :key="team.name"
                  class="flex items-center gap-3 rounded-3 border border-outline-gray-2 bg-surface-gray-1 px-3 py-2"
                >
                  <span class="lucide-users size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
                  <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">{{ team.name }}</span>
                  <span v-if="team.role" class="shrink-0 text-sm text-ink-gray-5">{{ __(team.role) }}</span>
                </li>
              </ul>
              <p v-else class="text-base italic text-ink-gray-4">{{ __('Not a member of any team.') }}</p>
            </section>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, watch } from 'vue'
import { Avatar, Badge, Button, Dialog, ErrorMessage, Skeleton, createResource } from 'frappe-ui'
import { session } from '@/data/session'
import { shortDate } from '@/utils/format'
import { translate as __ } from '@/translation'

const ROLES = {
  Manager: { icon: 'lucide-shield-check', hint: 'Runs spaces, publishes and retires procedures' },
  Author: { icon: 'lucide-pencil-line', hint: 'Writes and revises procedures' },
  Approver: { icon: 'lucide-stamp', hint: 'Signs procedures off before they go live' },
  Reviewer: { icon: 'lucide-message-square-text', hint: 'Comments on procedures in review' },
  Trainer: { icon: 'lucide-graduation-cap', hint: 'Assigns training and signs people off' },
  Reader: { icon: 'lucide-book-open', hint: 'Reads and acknowledges procedures' },
}

const open = defineModel('open', { type: Boolean, default: false })

const profile = createResource({ url: 'sop.api.session.profile' })

const data = computed(() => profile.data || {})
const teams = computed(() => data.value.teams || [])

const roles = computed(() =>
  (data.value.roles || [])
    .filter((name) => ROLES[name])
    .map((name) => ({ name, ...ROLES[name] })),
)

const contact = computed(() =>
  [
    { label: 'Email', icon: 'lucide-mail', value: data.value.email },
    { label: 'Phone', icon: 'lucide-phone', value: data.value.phone },
    { label: 'Mobile', icon: 'lucide-smartphone', value: data.value.mobile_no },
    { label: 'Location', icon: 'lucide-map-pin', value: data.value.location },
  ].filter((row) => row.value),
)

const account = computed(() =>
  [
    { label: 'Username', value: data.value.username },
    { label: 'Joined', value: data.value.member_since && shortDate(data.value.member_since) },
    { label: 'Last seen', value: data.value.last_active && shortDate(data.value.last_active) },
    { label: 'Time zone', value: data.value.time_zone },
  ].filter((row) => row.value),
)

watch(open, (value) => {
  if (value) profile.reload()
})
</script>
