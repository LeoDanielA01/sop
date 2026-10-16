<template>
  <PageHeader>
    <AppBreadcrumbs />
    <Button
      variant="ghost"
      icon-left="lucide-refresh-cw"
      :label="__('Refresh')"
      :loading="directory.loading"
      @click="directory.reload()"
    />
  </PageHeader>

  <div class="mx-auto w-full max-w-[1200px] px-3 pb-12 pt-4 sm:px-5 space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <TabButtons
          v-model="roleFilter"
          :options="[
            { label: __('All Team'), value: 'all' },
            { label: __('Authors'), value: 'authors' },
            { label: __('Approvers'), value: 'approvers' },
            { label: __('Active Owners'), value: 'owners' },
          ]"
        />
      </div>

      <div class="relative w-full sm:w-64">
        <input
          v-model="search"
          type="text"
          :placeholder="__('Search team members...')"
          class="w-full rounded-3 border border-outline-gray-2 bg-surface-base py-1.5 pl-8 pr-3 text-sm text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-3 focus:outline-none"
        />
        <span class="lucide-search absolute left-2.5 top-2.5 size-4 text-ink-gray-4" aria-hidden="true" />
      </div>
    </div>

    <ErrorMessage v-if="directory.error" :message="directory.error.messages?.[0] || directory.error.message" />

    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <StatTile
        :label="__('Total Team Members')"
        icon="lucide-users"
        :value="stats.total"
        :detail="__('System users in organisation')"
        class="cursor-pointer"
        @click="roleFilter = 'all'"
      />
      <StatTile
        :label="__('SOP Authors')"
        icon="lucide-pencil-line"
        :value="stats.authors"
        :detail="__('Can write & edit procedures')"
        class="cursor-pointer"
        @click="roleFilter = 'authors'"
      />
      <StatTile
        :label="__('SOP Approvers')"
        icon="lucide-stamp"
        :value="stats.approvers"
        :detail="__('Can review & sign off revisions')"
        class="cursor-pointer"
        @click="roleFilter = 'approvers'"
      />
      <StatTile
        :label="__('Active Owners')"
        icon="lucide-book-user"
        :value="stats.owners"
        :detail="__('Currently owning procedures')"
        class="cursor-pointer"
        @click="roleFilter = 'owners'"
      />
    </div>

    <div v-if="directory.loading && !members.length" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Skeleton v-for="n in 6" :key="n" class="h-36 rounded-4" />
    </div>

    <div v-else-if="filteredMembers.length" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="member in filteredMembers"
        :key="member.name"
        class="flex flex-col justify-between rounded-4 border border-outline-gray-2 bg-surface-base p-4 transition-all hover:border-outline-gray-3 shadow-xs"
      >
        <div class="flex items-start gap-3">
          <Avatar
            :image="member.user_image"
            :label="member.full_name"
            size="xl"
            shape="circle"
            class="shrink-0"
          />

          <div class="min-w-0 flex-1">
            <h3 class="truncate text-base font-semibold text-ink-gray-9">
              {{ member.full_name }}
            </h3>
            <p class="truncate text-xs text-ink-gray-5">
              {{ member.email }}
            </p>

            <div class="mt-2 flex flex-wrap gap-1">
              <Badge
                v-for="role in member.roles"
                :key="role"
                variant="subtle"
                size="sm"
                :theme="role === 'SOP Approver' ? 'green' : role === 'SOP Author' ? 'blue' : 'gray'"
              >
                {{ role }}
              </Badge>
            </div>
          </div>
        </div>

        <div class="mt-4 flex items-center justify-between border-t border-outline-gray-1 pt-3 text-xs text-ink-gray-6">
          <span class="flex items-center gap-1.5">
            <span class="lucide-book-text size-3.5 text-ink-gray-5" aria-hidden="true" />
            <strong class="text-ink-gray-8">{{ member.sop_count }}</strong> {{ __('Procedures') }}
          </span>

          <span v-if="member.pending_approvals" class="flex items-center gap-1 text-ink-amber-6 font-medium">
            <span class="lucide-clock size-3.5" aria-hidden="true" />
            {{ member.pending_approvals }} {{ __('Pending reviews') }}
          </span>
          <span v-else class="text-ink-gray-4">
            {{ __('No pending reviews') }}
          </span>
        </div>
      </div>
    </div>

    <div
      v-else-if="!directory.loading"
      class="mt-12 flex flex-col items-center gap-2 py-12 text-center text-ink-gray-5"
    >
      <span class="lucide-users size-8 text-ink-gray-4" aria-hidden="true" />
      <p class="text-base font-medium text-ink-gray-7">{{ __('No team members found') }}</p>
      <p class="text-sm">{{ __('Try adjusting your filter or search criteria.') }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Badge,
  Button,
  ErrorMessage,
  PageHeader,
  Skeleton,
  TabButtons,
  createResource,
} from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import StatTile from '@/components/Insights/StatTile.vue'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()
const search = ref('')

const roleFilter = computed({
  get: () => route.query.role || 'all',
  set: (val) => {
    const query = { ...route.query }
    if (val === 'all') {
      delete query.role
    } else {
      query.role = val
    }
    router.replace({ query })
  },
})

const directory = createResource({
  url: 'sop.api.team.team_directory',
  auto: true,
})

const members = computed(() => directory.data || [])

const filteredMembers = computed(() => {
  let list = members.value

  if (roleFilter.value === 'authors') {
    list = list.filter((m) => m.is_author)
  } else if (roleFilter.value === 'approvers') {
    list = list.filter((m) => m.is_approver)
  } else if (roleFilter.value === 'owners') {
    list = list.filter((m) => m.sop_count > 0)
  }

  if (search.value.trim()) {
    const q = search.value.toLowerCase().trim()
    list = list.filter(
      (m) =>
        m.full_name?.toLowerCase().includes(q) ||
        m.email?.toLowerCase().includes(q) ||
        m.roles?.some((r) => r.toLowerCase().includes(q)),
    )
  }

  return list
})

const stats = computed(() => {
  const all = members.value
  return {
    total: all.length,
    authors: all.filter((m) => m.is_author).length,
    approvers: all.filter((m) => m.is_approver).length,
    owners: all.filter((m) => m.sop_count > 0).length,
  }
})
</script>
