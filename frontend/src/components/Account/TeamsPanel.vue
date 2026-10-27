<template>
  <div class="pt-4">
    <ErrorMessage :message="error" class="mb-3" />

    <div class="flex flex-col gap-3">
      <div v-for="team in rows" :key="team.key" class="rounded-4 border border-outline-gray-2">
        <div class="flex flex-wrap items-center gap-2 border-b border-outline-gray-1 px-3 py-2.5">
          <span class="lucide-users size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          <TextInput v-model="team.team_name" class="w-48" :placeholder="__('Team name')" :aria-label="__('Team name')" />
          <TextInput
            v-model="team.description"
            class="min-w-0 flex-1"
            :placeholder="__('What this team does')"
            :aria-label="__('Description')"
          />
          <Button
            variant="ghost"
            icon="lucide-trash-2"
            :label="__('Delete team')"
            :loading="removing.loading && removing.params?.name === team.name"
            @click="remove(team)"
          />
        </div>

        <div class="px-3 py-2.5">
          <p class="mb-2 text-sm text-ink-gray-5">
            <template v-if="team.spaces?.length">
              {{ __('Approves procedures in {0}.').format(team.spaces.map((space) => space.title).join(', ')) }}
            </template>
            <template v-else>{{ __('Not linked to a space yet. Pick it for a space under Spaces.') }}</template>
          </p>

          <div class="flex flex-col divide-y divide-outline-gray-1">
            <div v-for="(member, index) in team.members" :key="member.user" class="flex items-center gap-2 py-1.5">
              <Avatar :image="member.user_image" :label="member.full_name" size="md" />
              <div class="min-w-0 flex-1">
                <div class="truncate text-base text-ink-gray-8">
                  {{ member.full_name }}
                  <Badge v-if="!member.enabled" theme="gray" variant="subtle" size="sm">{{ __('Disabled') }}</Badge>
                </div>
                <div class="truncate text-sm text-ink-gray-5">{{ member.user }}</div>
              </div>
              <Select v-model="member.team_role" :options="ROLES" size="sm" class="w-32" />
              <Button
                variant="ghost"
                icon="lucide-x"
                :label="__('Remove from team')"
                @click="team.members.splice(index, 1)"
              />
            </div>
          </div>

          <div class="mt-2 flex items-center gap-2">
            <Combobox
              class="w-64"
              :options="peopleFor(team)"
              :modelValue="null"
              :loading="people.loading"
              :placeholder="__('Add a person')"
              @update:modelValue="(value) => addMember(team, value)"
            />
            <span class="text-sm text-ink-gray-5">
              {{ __('Reviewers and Approvers sign off every procedure in the team’s spaces.') }}
            </span>
            <Button
              variant="solid"
              class="ml-auto"
              :label="__('Save')"
              :loading="saving.loading && saving.params?.name === (team.name || undefined)"
              :disabled="!dirty(team)"
              @click="save(team)"
            />
          </div>
        </div>
      </div>
    </div>

    <p v-if="!rows.length && !list.loading" class="py-6 text-center text-base text-ink-gray-5">
      {{ __('No teams yet. A team says who reviews and approves the procedures in a space.') }}
    </p>

    <div class="mt-4">
      <Button icon-left="lucide-plus" :label="__('New team')" @click="addTeam" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  Avatar,
  Badge,
  Button,
  Combobox,
  ErrorMessage,
  Select,
  TextInput,
  createResource,
  toast,
} from 'frappe-ui'
import { spacesResource } from '@/data/navigation'
import { translate as __ } from '@/translation'

const ROLES = ['Reader', 'Author', 'Reviewer', 'Approver']

const emit = defineEmits(['changed'])

const rows = ref([])
let counter = 0

function adopt(data) {
  rows.value = (data || []).map((team) => ({
    ...team,
    description: team.description || '',
    key: team.name,
    members: team.members.map((member) => ({ ...member })),
    saved: snapshot(team),
  }))
}

const list = createResource({ url: 'sop.api.teams.teams', auto: true, onSuccess: adopt })
const people = createResource({ url: 'sop.api.team.team_directory', auto: true })

const saving = createResource({
  url: 'sop.api.teams.save_team',
  onSuccess() {
    toast.success(__('Team saved'))
    list.reload()
    spacesResource.reload()
    emit('changed')
  },
})

const removing = createResource({
  url: 'sop.api.teams.delete_team',
  onSuccess() {
    toast.success(__('Team deleted'))
    list.reload()
    emit('changed')
  },
})

const error = computed(
  () =>
    saving.error?.messages?.[0] ||
    removing.error?.messages?.[0] ||
    list.error?.messages?.[0],
)

function snapshot(team) {
  return JSON.stringify([
    team.team_name,
    team.description || '',
    team.members.map((member) => [member.user, member.team_role]),
  ])
}

function dirty(team) {
  return !team.name || snapshot(team) !== team.saved
}

function peopleFor(team) {
  const taken = new Set(team.members.map((member) => member.user))
  return (people.data || [])
    .filter((person) => !taken.has(person.name))
    .map((person) => ({ label: person.full_name || person.name, value: person.name }))
}

function addMember(team, user) {
  if (!user) return
  const person = (people.data || []).find((row) => row.name === user) || {}
  team.members.push({
    user,
    team_role: 'Reviewer',
    full_name: person.full_name || user,
    user_image: person.user_image,
    enabled: 1,
  })
}

function addTeam() {
  rows.value.push({ key: `new-${++counter}`, name: null, team_name: '', description: '', members: [], spaces: [] })
}

function save(team) {
  saving.submit({
    name: team.name || undefined,
    team_name: team.team_name,
    description: team.description,
    members: team.members.map((member) => ({ user: member.user, team_role: member.team_role })),
  })
}

function remove(team) {
  if (!team.name) {
    rows.value = rows.value.filter((row) => row !== team)
    return
  }
  removing.submit({ name: team.name })
}
</script>
