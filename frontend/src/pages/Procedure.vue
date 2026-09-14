<template>
  <PageHeader>
    <div class="flex min-w-0 items-center gap-2">
      <AppBreadcrumbs :tail="[{ label: doc.sop_no || route.params.name }]" />
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
      <Tooltip :text="fullWidth ? 'Narrow the page' : 'Use the full width'">
        <Button
          variant="ghost"
          :icon="fullWidth ? 'lucide-minimize-2' : 'lucide-maximize-2'"
          :label="fullWidth ? 'Narrow the page' : 'Use the full width'"
          @click="toggleWidth"
        />
      </Tooltip>
      <Dropdown :options="actions">
        <Button variant="ghost" icon="lucide-ellipsis" label="More" />
      </Dropdown>
    </div>
  </PageHeader>

  <div :class="readingWidth" class="mx-auto mt-5 w-full px-3 pb-24 sm:px-5">
    <ErrorMessage :message="lastError" class="mb-4" />

    <div
      v-if="doc.status && !isEffective"
      role="status"
      class="mb-5 flex items-start gap-3 rounded-lg border px-4 py-3.5 text-base"
      :class="
        doc.status === 'Retired'
          ? 'border-outline-red-2 bg-surface-red-1 text-ink-red-6'
          : 'border-outline-amber-1 bg-surface-amber-1 text-ink-amber-6'
      "
    >
      <span
        class="lucide-triangle-alert mt-0.5 size-4 shrink-0"
        aria-hidden="true"
      />
      <div class="min-w-0">
        <p class="font-medium">Not the version in force</p>
        <p class="mt-0.5 text-ink-gray-7">
          You are reading the <b>{{ doc.status?.toLowerCase() }}</b> version.
          <template v-if="doc.effective_revision">
            Rev {{ doc.effective_revision }} is what applies on the floor.
          </template>
        </p>
        <Button
          v-if="doc.effective_revision"
          class="mt-2"
          variant="subtle"
          size="sm"
          icon-left="lucide-badge-check"
          :label="`Read Rev ${doc.effective_revision}`"
          @click="revision = doc.effective_revision"
        />
      </div>
    </div>

    <div
      v-if="doc.approvals?.length && !isEffective"
      class="mb-5 rounded-lg border border-outline-gray-2 bg-surface-gray-1"
    >
      <div class="flex items-center justify-between px-4 pb-2 pt-3">
        <span class="text-sm text-ink-gray-5">Sign-off</span>
        <span class="text-sm text-ink-gray-5">{{ signedOff }} of {{ doc.approvals.length }}</span>
      </div>

      <div
        v-for="row in doc.approvals"
        :key="row.approver"
        class="flex items-center gap-2.5 border-t border-outline-gray-1 px-4 py-2.5"
      >
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

    <h1 class="text-2xl font-semibold tracking-tight text-ink-gray-9">{{ doc.title }}</h1>

    <p v-if="doc.summary" class="mb-5 mt-1.5 text-lg text-ink-gray-7">{{ doc.summary }}</p>

    <div v-if="!doc.summary" class="mb-5" />

    <dl
      class="mb-8 grid grid-cols-2 gap-x-5 gap-y-4 rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-4 sm:grid-cols-3"
    >
      <div class="flex min-w-0 items-center gap-2.5">
        <Avatar :image="doc.owner_image" :label="ownerName" size="lg" />
        <div class="min-w-0">
          <dt class="text-sm text-ink-gray-5">Owner</dt>
          <dd class="truncate text-base text-ink-gray-8">{{ ownerName }}</dd>
        </div>
      </div>

      <div class="flex min-w-0 items-center gap-2.5">
        <span
          class="grid size-8 shrink-0 place-content-center rounded-md border border-outline-gray-2 bg-surface-base"
        >
          <span class="lucide-calendar-check size-4 text-ink-gray-6" aria-hidden="true" />
        </span>
        <div class="min-w-0">
          <dt class="text-sm text-ink-gray-5">In force since</dt>
          <dd class="truncate text-base text-ink-gray-8">
            {{ doc.effective_from ? shortDate(doc.effective_from) : 'Not yet' }}
          </dd>
        </div>
      </div>

      <div class="flex min-w-0 items-center gap-2.5">
        <span
          class="grid size-8 shrink-0 place-content-center rounded-md border border-outline-gray-2 bg-surface-base"
        >
          <span
            class="lucide-calendar-clock size-4"
            :class="overdue ? 'text-ink-red-3' : 'text-ink-gray-6'"
            aria-hidden="true"
          />
        </span>
        <div class="min-w-0">
          <dt class="text-sm text-ink-gray-5">{{ overdue ? 'Review overdue' : 'Next review' }}</dt>
          <dd
            class="truncate text-base"
            :class="overdue ? 'text-ink-red-3' : 'text-ink-gray-8'"
          >
            {{ doc.review_due ? shortDate(doc.review_due) : 'Not scheduled' }}
          </dd>
        </div>
      </div>

      <div class="flex min-w-0 items-center gap-2.5">
        <span
          class="grid size-8 shrink-0 place-content-center rounded-md border border-outline-gray-2 bg-surface-base"
        >
          <span class="lucide-git-commit-horizontal size-4 text-ink-gray-6" aria-hidden="true" />
        </span>
        <div class="min-w-0">
          <dt class="text-sm text-ink-gray-5">Version</dt>
          <dd class="truncate text-base text-ink-gray-8">
            Rev {{ doc.version || 1 }}
            <span v-if="doc.revisions?.length > 1" class="text-ink-gray-5">
              of {{ doc.revisions.length }}
            </span>
          </dd>
        </div>
      </div>

      <div class="flex min-w-0 items-center gap-2.5">
        <span
          class="grid size-8 shrink-0 place-content-center rounded-md border border-outline-gray-2 bg-surface-base"
        >
          <span
            class="size-4"
            :class="
              doc.acknowledged_on ? 'lucide-check-check text-ink-green-3' : 'lucide-circle-dashed text-ink-gray-6'
            "
            aria-hidden="true"
          />
        </span>
        <div class="min-w-0">
          <Tooltip
            text="Sign-off is per revision, not per reading. When a new revision comes into force you are asked again."
          >
            <dt class="w-fit text-sm text-ink-gray-5">Read &amp; understood</dt>
          </Tooltip>
          <dd class="truncate text-base text-ink-gray-8">
            <template v-if="doc.acknowledged_on">
              Rev {{ doc.acknowledged_version }} · {{ shortDate(doc.acknowledged_on) }}
            </template>
            <template v-else-if="isEffective">Not signed off</template>
            <template v-else>—</template>
          </dd>
        </div>
      </div>

      <div v-if="doc.risk_level" class="flex min-w-0 items-center gap-2.5">
        <span
          class="grid size-8 shrink-0 place-content-center rounded-md border border-outline-gray-2 bg-surface-base"
        >
          <span class="lucide-shield-alert size-4 text-ink-gray-6" aria-hidden="true" />
        </span>
        <div class="min-w-0">
          <dt class="text-sm text-ink-gray-5">Risk</dt>
          <dd class="truncate">
            <Badge :theme="RISK_THEME[doc.risk_level]" variant="subtle" size="sm">
              {{ doc.risk_level }}
            </Badge>
          </dd>
        </div>
      </div>

      <div
        v-if="doc.tags?.length"
        class="col-span-2 flex flex-wrap items-center gap-1.5 border-t border-outline-gray-1 pt-3 sm:col-span-3"
      >
        <span class="lucide-tags size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
        <Badge v-for="tag in doc.tags" :key="tag" variant="subtle" size="sm">{{ tag }}</Badge>
      </div>
    </dl>

    <article
      ref="body"
      class="prose-sop max-w-[68ch] text-base leading-relaxed text-ink-gray-8"
      v-html="doc.content"
    />

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
    <div :class="readingWidth" class="mx-auto flex items-center justify-between gap-4">
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
    <div :class="readingWidth" class="mx-auto flex items-center justify-between gap-4">
      <p class="text-sm text-ink-gray-6">
        Confirm you have read and understood <b>Rev {{ doc.version }}</b>. You will be asked again
        when a new revision comes into force — not every time you open it.
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
    :class="readingWidth"
    class="mx-auto px-3 pb-10 text-sm text-ink-gray-5 sm:px-5"
  >
    You signed off Rev {{ doc.acknowledged_version }} on {{ shortDate(doc.acknowledged_on) }}. The
    next revision will ask again.
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
  Select,
  Tooltip,
  createResource,
} from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import ApproversDialog from '@/components/ApproversDialog.vue'
import MentionChip from '@/components/MentionChip.vue'
import { acknowledge, procedure } from '@/data/procedures'
import { fullWidth, readingWidth, toggleWidth } from '@/data/preferences'
import { refreshCounts } from '@/data/navigation'
import { STATUS_THEME, reviewTone, shortDate, today } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const RISK_THEME = { High: 'red', Medium: 'orange', Low: 'green' }

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
const ownerName = computed(() => doc.value.process_owner_name || doc.value.process_owner)
const overdue = computed(() => reviewTone(doc.value.review_due) === 'red')
const signedOff = computed(
  () => (doc.value.approvals || []).filter((row) => row.decision === 'Approved').length,
)
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
