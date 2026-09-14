<template>
  <PageHeader>
    <AppBreadcrumbs :tail="[{ label: 'Rules' }]" />
    <Button variant="solid" icon-left="lucide-plus" label="New rule" @click="edit(null)" />
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[940px] px-3 pb-10 sm:px-5">
    <p class="mb-4 text-sm text-ink-gray-5">
      A rule decides who has to be trained on what. It runs whenever a procedure comes into force
      and again when training expires.
    </p>

    <List class="-mx-3 sm:list-gap-4">
      <ListRow v-for="row in rows" :key="row.name" class="h-15" @click="edit(row)">
        <ListCell>
          <div class="min-w-0 flex-1">
            <div class="truncate leading-none text-ink-gray-8">
              <span class="text-base">{{ row.who }}</span>
              <span class="text-ink-gray-5"> must train on </span>
              <span class="text-base">{{ row.covers }}</span>
            </div>
            <div class="mt-1.5 flex min-w-0 items-center gap-2 text-base text-ink-gray-5">
              <span class="shrink-0">{{ row.method }}</span>
              <span class="shrink-0">· due in {{ row.due_days }} days</span>
              <span v-if="row.refresher_months" class="shrink-0">
                · repeats every {{ row.refresher_months }} months
              </span>
            </div>
          </div>
        </ListCell>

        <ListCell class="hidden w-32 sm:flex">
          <Badge v-if="row.assignments" variant="subtle" size="sm">
            {{ row.assignments }} assigned
          </Badge>
        </ListCell>

        <ListCell class="justify-end gap-2">
          <Tooltip :text="row.enabled ? 'Switch the rule off' : 'Switch the rule on'">
            <Switch
              :model-value="!!row.enabled"
              @update:model-value="(value) => flip(row, value)"
              @click.stop
            />
          </Tooltip>
          <Tooltip text="Assign it now to everyone it covers">
            <Button
              variant="ghost"
              icon="lucide-play"
              label="Run now"
              :loading="run.loading && running === row.name"
              @click.stop="trigger(row)"
            />
          </Tooltip>
        </ListCell>
      </ListRow>
    </List>

    <ListSkeleton v-if="requirements.loading && !rows.length" :avatar="false" />

    <div
      v-if="!requirements.loading && !rows.length"
      class="mt-10 flex flex-col items-center gap-2 rounded-4 border border-dashed border-outline-gray-2 px-4 py-10 text-center"
    >
      <span class="lucide-scroll-text size-6 text-ink-gray-4" aria-hidden="true" />
      <p class="text-base text-ink-gray-7">No rules yet</p>
      <p class="max-w-[26rem] text-sm text-ink-gray-5">
        Without a rule, training only happens when somebody assigns it by hand. A rule says
        something like "everyone on the Plant Floor team trains on every Manufacturing procedure".
      </p>
      <Button variant="subtle" icon-left="lucide-plus" label="New rule" @click="edit(null)" />
    </div>
  </div>

  <Dialog v-model:open="showForm" :title="draft.name ? 'Edit rule' : 'New rule'" size="md">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="save.error?.messages?.[0]" />

        <div class="grid gap-3 sm:grid-cols-2">
          <FormControl
            type="select"
            label="Applies to"
            :options="['Role', 'Team', 'User', 'Designation', 'Department']"
            v-model="draft.applies_to"
          />
          <div class="flex flex-col gap-1.5">
            <FormLabel :label="draft.applies_to" />
            <Combobox
              :options="targetOptions"
              :modelValue="draft.target"
              :loading="targets.loading"
              :placeholder="`Search ${draft.applies_to.toLowerCase()}`"
              @update:modelValue="(value) => (draft.target = value)"
              @update:query="searchTargets"
            />
          </div>
          <FormControl
            type="select"
            label="Covers"
            :options="['Space', 'Procedure']"
            v-model="draft.scope"
          />
          <FormControl
            v-if="draft.scope === 'Space'"
            type="select"
            label="Space"
            :options="spaceOptions"
            v-model="draft.space"
          />
          <div v-else class="flex flex-col gap-1.5">
            <FormLabel label="Procedure" />
            <Combobox
              :options="procedureOptions"
              :modelValue="draft.sop"
              :loading="picks.loading"
              placeholder="Search procedures"
              @update:modelValue="(value) => (draft.sop = value)"
              @update:query="searchProcedures"
            />
          </div>
          <FormControl
            type="select"
            label="How they train"
            :options="METHODS"
            v-model="draft.method"
          />
          <FormControl type="number" label="Due within (days)" v-model="draft.due_days" />
          <FormControl
            type="number"
            label="Repeat every (months)"
            v-model="draft.refresher_months"
          />
          <FormControl type="number" label="Pass mark %" v-model="draft.pass_mark" />
        </div>

        <FormControl
          type="checkbox"
          label="An assessment decides whether they passed"
          v-model="draft.requires_assessment"
        />
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          v-if="draft.name"
          variant="ghost"
          theme="red"
          label="Delete"
          :loading="remove.loading"
          @click="remove.submit({ name: draft.name })"
        />
        <Button
          variant="solid"
          label="Save rule"
          :loading="save.loading"
          :disabled="!draft.target || (draft.scope === 'Space' ? !draft.space : !draft.sop)"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  Badge,
  Button,
  Combobox,
  Dialog,
  ErrorMessage,
  FormControl,
  FormLabel,
  PageHeader,
  Switch,
  Tooltip,
  createResource,
  toast,
} from 'frappe-ui'
import { List, ListCell, ListRow } from 'frappe-ui/list'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import ListSkeleton from '@/components/ListSkeleton.vue'
import { spaces } from '@/data/navigation'

const METHODS = ['Read & Understand', 'Classroom', 'On the Job', 'Assessment']
const TARGET_DOCTYPE = {
  Role: 'Role',
  Team: 'SOP Team',
  User: 'User',
  Designation: 'Designation',
  Department: 'Department',
}
const TARGETS = { Role: 'role', Team: 'team', User: 'user', Designation: 'designation', Department: 'department' }

const showForm = ref(false)
const running = ref(null)

const draft = reactive({
  name: null,
  applies_to: 'Team',
  target: '',
  scope: 'Space',
  space: null,
  sop: null,
  method: 'Read & Understand',
  due_days: 14,
  refresher_months: 12,
  pass_mark: 80,
  requires_assessment: false,
  enabled: 1,
})

const requirements = createResource({ url: 'sop.api.requirements.requirements', auto: true })

const targets = createResource({ url: 'sop.api.mentions.find' })
const picks = createResource({ url: 'sop.api.mentions.find' })

const targetOptions = computed(() =>
  (targets.data || []).map((row) => ({
    label: row.label,
    value: row.name,
    description: row.label === row.name ? null : row.name,
  })),
)

const procedureOptions = computed(() =>
  (picks.data || []).map((row) => ({ label: row.label, value: row.name, description: row.name })),
)

function searchTargets(text) {
  targets.submit({ doctype: TARGET_DOCTYPE[draft.applies_to] || 'Role', text: text || '' })
}

function searchProcedures(text) {
  picks.submit({ doctype: 'SOP', text: text || '' })
}

const save = createResource({
  url: 'sop.api.requirements.save_requirement',
  onSuccess() {
    showForm.value = false
    requirements.reload()
  },
})

const remove = createResource({
  url: 'sop.api.requirements.delete_requirement',
  onSuccess() {
    showForm.value = false
    requirements.reload()
  },
})

const toggle = createResource({
  url: 'sop.api.requirements.toggle_requirement',
  onSuccess: () => requirements.reload(),
})

const run = createResource({
  url: 'sop.api.requirements.run_requirement',
  onSuccess(data) {
    running.value = null
    requirements.reload()
    toast.success(data.created ? `${data.created} people assigned` : 'Everyone is already assigned')
  },
})

const rows = computed(() => requirements.data || [])

const spaceOptions = computed(() =>
  spaces.value.map((space) => ({ label: space.title, value: space.name })),
)

function edit(row) {
  Object.assign(draft, {
    name: row?.name || null,
    applies_to: row?.applies_to || 'Team',
    target: row ? row[TARGETS[row.applies_to]] || '' : '',
    scope: row?.scope || 'Space',
    space: row?.space || spaces.value[0]?.name || null,
    sop: row?.sop || null,
    method: row?.method || 'Read & Understand',
    due_days: row?.due_days ?? 14,
    refresher_months: row?.refresher_months ?? 12,
    pass_mark: row?.pass_mark ?? 80,
    requires_assessment: !!row?.requires_assessment,
    enabled: row ? row.enabled : 1,
  })

  searchTargets('')
  searchProcedures('')
  showForm.value = true
}

watch(
  () => draft.applies_to,
  () => {
    draft.target = ''
    searchTargets('')
  },
)

function submit() {
  save.submit({
    name: draft.name,
    applies_to: draft.applies_to,
    [TARGETS[draft.applies_to]]: draft.target,
    scope: draft.scope,
    space: draft.scope === 'Space' ? draft.space : null,
    sop: draft.scope === 'Procedure' ? draft.sop : null,
    method: draft.method,
    due_days: draft.due_days,
    refresher_months: draft.refresher_months,
    pass_mark: draft.pass_mark,
    requires_assessment: draft.requires_assessment ? 1 : 0,
    enabled: draft.enabled,
  })
}

function flip(row, value) {
  toggle.submit({ name: row.name, enabled: value ? 1 : 0 })
}

function trigger(row) {
  running.value = row.name
  run.submit({ name: row.name })
}

onMounted(() => requirements.reload())
</script>
