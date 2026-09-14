<template>
  <PageHeader>
    <div class="flex min-w-0 items-center gap-2">
      <PageHeaderTitle>
        <span class="font-mono text-sm text-ink-gray-5">{{ doc.sop_no }}</span>
        <span class="ml-2">{{ doc.title }}</span>
      </PageHeaderTitle>
      <Badge :theme="STATUS_THEME[doc.status]" variant="subtle" size="sm">
        {{ doc.status }}
      </Badge>
      <Badge v-if="doc.version" variant="subtle" size="sm">Rev {{ doc.version }}</Badge>
    </div>

    <div class="flex items-center gap-2">
      <Select
        v-if="doc.revisions?.length > 1"
        v-model="revision"
        :options="doc.revisions.map((r) => ({ label: `Rev ${r.version}`, value: r.version }))"
      />
      <Button
        v-if="doc.can_edit"
        variant="ghost"
        icon-left="lucide-pencil"
        label="Edit"
        @click="router.push(`/${route.params.name}/edit`)"
      />
      <Button
        v-if="primary"
        variant="solid"
        :icon-left="primary.icon"
        :label="primary.label"
        :loading="primary.loading"
        @click="primary.onClick"
      />
      <Dropdown :options="actions">
        <Button variant="ghost" icon="lucide-ellipsis" label="More" />
      </Dropdown>
    </div>
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[740px] px-3 pb-24 sm:px-5">
    <ErrorMessage :message="lastError" class="mb-4" />

    <div
      v-if="doc.status && !isEffective"
      class="mb-5 rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-base text-ink-gray-7"
    >
      This is a <b>{{ doc.status?.toLowerCase() }}</b> version and is not in force.
      <template v-if="doc.effective_revision">
        The one in force is
        <Button
          variant="ghost"
          size="sm"
          :label="`Rev ${doc.effective_revision}`"
          @click="revision = doc.effective_revision"
        />
      </template>
    </div>

    <div
      v-if="doc.approvals?.length && !isEffective"
      class="mb-5 flex flex-col gap-2.5 rounded-lg border border-outline-gray-2 px-4 py-3"
    >
      <span class="text-sm text-ink-gray-5">Approval</span>
      <div v-for="row in doc.approvals" :key="row.approver" class="flex items-center gap-2.5">
        <Avatar :image="row.approver_image" :label="row.approver_name" size="sm" />
        <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
          {{ row.approver_name }}
          <span class="text-ink-gray-5">· {{ row.approval_role }}</span>
        </span>
        <span v-if="row.comment" class="truncate text-sm text-ink-gray-5">{{ row.comment }}</span>
        <Badge :theme="DECISION_THEME[row.decision]" variant="subtle" size="sm">
          {{ row.decision }}
        </Badge>
      </div>
    </div>

    <div class="mb-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-ink-gray-5">
      <span class="flex items-center gap-1.5">
        <Avatar
          :image="doc.owner_image"
          :label="doc.process_owner_name || doc.process_owner"
          size="sm"
        />
        {{ doc.process_owner_name || doc.process_owner }}
      </span>
      <span v-if="doc.process_trail?.length" class="flex min-w-0 items-center gap-1">
        <span class="lucide-workflow size-3.5 shrink-0" aria-hidden="true" />
        <span class="truncate">{{ doc.process_trail.map((step) => step.title).join(' › ') }}</span>
      </span>
      <span v-if="doc.effective_from">Effective {{ shortDate(doc.effective_from) }}</span>
      <span
        v-if="doc.review_due"
        :class="reviewTone(doc.review_due) === 'red' ? 'text-ink-red-3' : ''"
      >
        Review due {{ shortDate(doc.review_due) }}
      </span>
      <span v-for="tag in doc.tags || []" :key="tag">#{{ tag }}</span>
    </div>

    <article ref="body" class="prose-sop text-base text-ink-gray-8" v-html="doc.content" />

    <MentionChip
      v-for="reference in doc.references || []"
      :key="reference.key"
      :reference="reference"
      :root="body"
    />

    <section v-if="doc.steps?.length" class="mt-10">
      <h2 class="text-lg-semibold text-ink-gray-8">Steps</h2>
      <ol class="mt-3 space-y-3">
        <li v-for="step in doc.steps" :key="step.step_no" class="flex gap-3">
          <span
            class="mt-0.5 grid size-6 shrink-0 place-content-center rounded-full bg-surface-gray-2 text-sm text-ink-gray-7"
          >
            {{ step.step_no }}
          </span>
          <div class="min-w-0">
            <div class="text-base text-ink-gray-8" v-html="step.instruction" />
            <div
              v-if="step.responsible_role || step.record_to_capture"
              class="mt-1 flex flex-wrap gap-x-4 text-sm text-ink-gray-5"
            >
              <span v-if="step.responsible_role">{{ step.responsible_role }}</span>
              <span v-if="step.record_to_capture">Records: {{ step.record_to_capture }}</span>
            </div>
          </div>
        </li>
      </ol>
    </section>
  </div>

  <div
    v-if="doc.actions?.decide"
    class="sticky bottom-0 border-t border-outline-gray-1 bg-surface-base px-4 py-3 sm:px-6"
  >
    <div class="mx-auto flex max-w-[740px] items-center justify-between gap-4">
      <p class="text-sm text-ink-gray-6">Your approval is what this one is waiting on.</p>
      <div class="flex items-center gap-2">
        <Button variant="subtle" label="Request changes" @click="changes.open = true" />
        <Button
          variant="solid"
          label="Approve"
          :loading="decide.loading"
          @click="decide.submit({ sop: doc.name, decision: 'Approved' })"
        />
      </div>
    </div>
  </div>

  <div
    v-else-if="needsAcknowledgement"
    class="sticky bottom-0 border-t border-outline-gray-1 bg-surface-base px-4 py-3 sm:px-6"
  >
    <div class="mx-auto flex max-w-[740px] items-center justify-between gap-4">
      <p class="text-sm text-ink-gray-6">
        Confirm you have read and understood Rev {{ doc.version }}.
      </p>
      <Button
        variant="solid"
        label="I have read this"
        :loading="acknowledge.loading"
        @click="acknowledge.submit({ sop: doc.name, version: doc.version })"
      />
    </div>
  </div>

  <div
    v-else-if="isEffective && doc.acknowledged_on"
    class="mx-auto max-w-[740px] px-3 pb-10 text-sm text-ink-gray-5 sm:px-5"
  >
    You acknowledged Rev {{ doc.acknowledged_version }} on {{ shortDate(doc.acknowledged_on) }}.
  </div>

  <ApproversDialog
    v-model:open="showApprovers"
    :current="doc.approvals || []"
    :loading="send.loading"
    :error="send.error?.messages?.[0] || ''"
    @submit="(rows) => send.submit({ sop: doc.name, approvers: rows })"
  />

  <Dialog v-model:open="showPublish" title="Bring into force" size="sm">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="release.error?.messages?.[0]" />
        <FormControl type="date" label="Effective from" v-model="publishOn" />
        <FormControl
          type="textarea"
          label="What changed"
          placeholder="Shown in the revision history"
          v-model="changeSummary"
        />
        <FormControl
          type="checkbox"
          label="Material change — everyone has to be trained again"
          v-model="isMaterial"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          :label="`Publish Rev ${(doc.version || 0) + 1}`"
          :loading="release.loading"
          @click="publish"
        />
      </div>
    </template>
  </Dialog>

  <Dialog v-model:open="changes.open" title="Request changes" size="sm">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="decide.error?.messages?.[0]" />
        <FormControl type="textarea" label="What has to change" v-model="changes.comment" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          theme="red"
          label="Send it back"
          :loading="decide.loading"
          :disabled="!changes.comment"
          @click="decide.submit({ sop: doc.name, decision: 'Rejected', comment: changes.comment })"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Avatar,
  Badge,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  PageHeader,
  PageHeaderTitle,
  Select,
  createResource,
} from 'frappe-ui'
import ApproversDialog from '@/components/ApproversDialog.vue'
import MentionChip from '@/components/MentionChip.vue'
import { acknowledge, procedure } from '@/data/procedures'
import { refreshCounts } from '@/data/navigation'
import { STATUS_THEME, reviewTone, shortDate, today } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const DECISION_THEME = { Approved: 'green', Rejected: 'red', Pending: 'gray' }

const revision = ref(null)
const body = ref(null)
const showApprovers = ref(false)
const showPublish = ref(false)
const publishOn = ref(today())
const changeSummary = ref('')
const isMaterial = ref(true)
const changes = reactive({ open: false, comment: '' })

const doc = computed(() => procedure.data || {})
const isEffective = computed(() => doc.value.status === 'Effective')
const needsAcknowledgement = computed(() => isEffective.value && !doc.value.acknowledged)

function load() {
  procedure.submit({ name: route.params.name, revision: revision.value })
}

function afterAction() {
  showApprovers.value = false
  showPublish.value = false
  changes.open = false
  changes.comment = ''
  load()
  refreshCounts()
}

const send = createResource({
  url: 'sop.api.lifecycle.send_for_approval',
  onSuccess: afterAction,
})

const decide = createResource({
  url: 'sop.api.lifecycle.decide',
  onSuccess: afterAction,
})

const release = createResource({
  url: 'sop.api.lifecycle.publish',
  onSuccess: afterAction,
})

const revise = createResource({
  url: 'sop.api.lifecycle.start_revision',
  onSuccess() {
    afterAction()
    router.push(`/${route.params.name}/edit`)
  },
})

const withdraw = createResource({
  url: 'sop.api.lifecycle.retire',
  onSuccess: afterAction,
})

const lastError = computed(
  () =>
    send.error?.messages?.[0] ||
    release.error?.messages?.[0] ||
    revise.error?.messages?.[0] ||
    withdraw.error?.messages?.[0] ||
    '',
)

const primary = computed(() => {
  const allowed = doc.value.actions || {}

  if (allowed.send_for_approval) {
    return {
      label: 'Send for approval',
      icon: 'lucide-send',
      loading: send.loading,
      onClick: () => (showApprovers.value = true),
    }
  }

  if (allowed.publish) {
    return {
      label: 'Bring into force',
      icon: 'lucide-badge-check',
      loading: release.loading,
      onClick: () => (showPublish.value = true),
    }
  }

  if (allowed.start_revision) {
    return {
      label: 'Start a revision',
      icon: 'lucide-git-branch',
      loading: revise.loading,
      onClick: () => revise.submit({ sop: doc.value.name }),
    }
  }

  return null
})

const actions = computed(() =>
  [
    {
      label: 'Revision history',
      icon: 'lucide-history',
      onClick: () => router.push(`/${route.params.name}/history`),
    },
    { label: 'Print controlled copy', icon: 'lucide-printer', onClick: () => window.print() },
    doc.value.actions?.retire && {
      label: 'Retire',
      icon: 'lucide-archive',
      onClick: () => withdraw.submit({ sop: doc.value.name }),
    },
  ].filter(Boolean),
)

function publish() {
  release.submit({
    sop: doc.value.name,
    effective_from: publishOn.value,
    change_summary: changeSummary.value,
    is_material: isMaterial.value ? 1 : 0,
  })
}

onMounted(load)
watch(() => [route.params.name, revision.value], load)
</script>
