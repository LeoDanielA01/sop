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
        v-if="isDesktop && doc.revisions?.length > 1"
        v-model="revision"
        :options="doc.revisions.map((r) => ({ label: `Rev ${r.version}`, value: r.version }))"
      />

      <Button
        v-if="isDesktop && doc.can_edit"
        variant="ghost"
        icon-left="lucide-pencil"
        label="Edit"
        @click="router.push(`/${route.params.name}/edit`)"
      />

      <Button
        v-if="primary"
        variant="solid"
        :icon-left="primary.icon"
        :label="isDesktop ? primary.label : ''"
        :loading="primary.loading"
        @click="primary.onClick"
      />

      <Tooltip :text="ui.fullScreen ? 'Leave full screen (esc)' : 'Read full screen'">
        <Button
          variant="ghost"
          :icon="ui.fullScreen ? 'lucide-shrink' : 'lucide-expand'"
          :label="ui.fullScreen ? 'Leave full screen' : 'Read full screen'"
          @click="ui.toggleFullScreen"
        />
      </Tooltip>

      <Dropdown :options="actions">
        <Button variant="ghost" icon="lucide-ellipsis" label="More" />
      </Dropdown>
    </div>
  </PageHeader>

  <div class="w-full px-4 pb-24 pt-5 sm:px-6">
    <ErrorMessage :message="lastError" class="mb-4" />

    <div class="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,1fr)_18rem] lg:items-start lg:gap-7">
      <aside
        class="order-first min-w-0 lg:sticky lg:top-[4.25rem] lg:order-last lg:h-[calc(100vh-5.5rem)]"
      >
        <div class="flex h-full flex-col overflow-hidden rounded-4 border border-outline-gray-2">
          <div
            v-if="!isEffective"
            role="status"
            class="flex shrink-0 items-center gap-2 px-4 py-2.5 text-sm font-medium"
            :class="
              doc.status === 'Retired'
                ? 'bg-surface-red-1 text-ink-red-6'
                : 'bg-surface-amber-1 text-ink-amber-6'
            "
          >
            <span class="lucide-triangle-alert size-4 shrink-0" aria-hidden="true" />
            {{ doc.status }} — not in force
          </div>

          <div class="shrink-0 border-b border-outline-gray-1 px-4 py-3">
            <div class="flex items-start gap-2">
              <p class="min-w-0 flex-1 text-base font-semibold text-ink-gray-9">
                {{ doc.title }}
              </p>

              <div class="flex shrink-0 items-center">
                <Tooltip v-if="doc.can_edit" text="Edit">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon="lucide-pencil"
                    label="Edit"
                    @click="router.push(`/${route.params.name}/edit`)"
                  />
                </Tooltip>
                <Tooltip text="Print a controlled copy">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon="lucide-printer"
                    label="Print"
                    @click="printCopy"
                  />
                </Tooltip>
                <Tooltip text="Revision history">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon="lucide-history"
                    label="Revision history"
                    @click="router.push(`/${route.params.name}/history`)"
                  />
                </Tooltip>
              </div>
            </div>

            <p class="mt-0.5 font-mono text-sm text-ink-gray-5">{{ doc.sop_no }}</p>
          </div>

          <div class="shrink-0 divide-y divide-outline-gray-1 border-b border-outline-gray-1">
            <button
              v-for="row in quick"
              :key="row.label"
              type="button"
              class="flex w-full items-center gap-2.5 px-4 py-2.5 text-left hover:bg-surface-gray-1"
              @click="row.onClick"
            >
              <span :class="row.icon" class="size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
              <span class="min-w-0 flex-1 truncate text-base text-ink-gray-7">{{ row.label }}</span>
              <Badge v-if="row.count" variant="subtle" size="sm">{{ row.count }}</Badge>
              <span class="lucide-plus size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
            </button>
          </div>

          <dl class="min-h-0 flex-1 divide-y divide-outline-gray-1 overflow-y-auto">
            <div v-for="row in facts" :key="row.label" class="px-4 py-2.5">
              <dt class="text-sm text-ink-gray-5">{{ row.label }}</dt>
              <dd class="mt-0.5 flex min-w-0 items-center gap-1.5 text-base" :class="row.tone || 'text-ink-gray-8'">
                <Avatar
                  v-if="row.avatar !== undefined"
                  :image="row.avatar"
                  :label="row.value"
                  size="sm"
                />
                <Badge v-else-if="row.badge" :theme="row.badge" variant="subtle" size="sm">
                  {{ row.value }}
                </Badge>
                <span v-else class="truncate">{{ row.value }}</span>
              </dd>
            </div>

            <div v-if="doc.tags?.length" class="flex flex-wrap items-center gap-1.5 px-4 py-2.5">
              <span class="lucide-tags size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
              <Badge v-for="tag in doc.tags" :key="tag" variant="subtle" size="sm">{{ tag }}</Badge>
            </div>
          </dl>
        </div>
      </aside>

      <div class="min-w-0">
      <h1 class="text-2xl font-semibold tracking-tight text-ink-gray-9">{{ doc.title }}</h1>

      <p v-if="doc.summary" class="mb-5 mt-1.5 text-lg text-ink-gray-7">{{ doc.summary }}</p>

      <div v-else class="mb-5" />

      <article
        ref="body"
        class="prose-sop max-w-[68ch] text-base leading-relaxed text-ink-gray-8 lg:max-w-none"
        v-html="doc.content"
      />

      <MentionChip
        v-for="reference in doc.references || []"
        :key="reference.key"
        :reference="reference"
        :root="body"
      />

      <nav
        v-if="around.previous || around.next"
        class="mt-10 grid gap-3 border-t border-outline-gray-1 pt-5 sm:grid-cols-2"
      >
        <button
          v-if="around.previous"
          type="button"
          class="flex items-center gap-3 rounded-4 border border-outline-gray-2 px-3 py-2.5 text-left hover:border-outline-gray-3"
          @click="router.push(`/${around.previous.name}`)"
        >
          <span class="lucide-chevron-left size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
          <span class="min-w-0">
            <span class="block text-sm text-ink-gray-5">Previous</span>
            <span class="block truncate text-base text-ink-gray-8">
              {{ around.previous.title }}
            </span>
          </span>
        </button>
        <span v-else class="hidden sm:block" />

        <button
          v-if="around.next"
          type="button"
          class="flex items-center justify-end gap-3 rounded-4 border border-outline-gray-2 px-3 py-2.5 text-right hover:border-outline-gray-3"
          @click="router.push(`/${around.next.name}`)"
        >
          <span class="min-w-0">
            <span class="block text-sm text-ink-gray-5">Next</span>
            <span class="block truncate text-base text-ink-gray-8">{{ around.next.title }}</span>
          </span>
          <span class="lucide-chevron-right size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
        </button>
      </nav>

      <ReviewComments
        v-if="doc.name"
        ref="comments"
        :sop="doc.name"
        :version="doc.version"
        :body="body"
        @count="(value) => (openComments = value)"
      />

      </div>
    </div>
  </div>

  <div
    v-if="doc.actions?.decide"
    class="sticky bottom-0 border-t border-outline-gray-1 bg-surface-base px-4 py-3 sm:px-6"
  >
    <div class="flex w-full items-center justify-between gap-4">
      <p class="text-sm text-ink-gray-6">Your approval is what this one is waiting on.</p>
      <div class="flex items-center gap-2">
        <Button
          variant="subtle"
          :label="openComments ? `Request changes (${openComments})` : 'Request changes'"
          @click="changes.open = true"
        />
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
    <div class="mx-auto flex max-w-[1400px] items-center justify-between gap-4">
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
    class="mx-auto max-w-[1400px] px-3 pb-10 text-sm text-ink-gray-5 sm:px-5"
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
        <p v-if="openComments" class="text-sm text-ink-gray-6">
          {{ openComments }} comment{{ openComments === 1 ? '' : 's' }} on the text
          {{ openComments === 1 ? 'is' : 'are' }} already on this revision. This note goes with them.
        </p>
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
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
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
import ReviewComments from '@/components/ReviewComments.vue'
import MentionChip from '@/components/MentionChip.vue'
import { acknowledge, procedure } from '@/data/procedures'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { useUI } from '@/stores/ui'
import { refreshCounts } from '@/data/navigation'
import { STATUS_THEME, reviewTone, shortDate, today } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const { isDesktop } = useBreakpoint()
const ui = useUI()

const RISK_THEME = { High: 'red', Medium: 'orange', Low: 'green' }

const openComments = ref(0)

const nearby = createResource({ url: 'sop.api.procedures.neighbours' })

const around = computed(() => nearby.data || { previous: null, next: null })

function onKeydown(event) {
  if (event.key === 'Escape' && ui.fullScreen) ui.toggleFullScreen()
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  if (ui.fullScreen) ui.toggleFullScreen()
})
const RING = {
  Approved: 'ring-outline-green-3',
  Rejected: 'ring-outline-red-3',
  Pending: 'ring-outline-gray-3',
}


const revision = ref(null)
const body = ref(null)
const showApprovers = ref(false)
const comments = ref(null)
const showPublish = ref(false)
const publishOn = ref(today())
const changeSummary = ref('')
const isMaterial = ref(true)
const changes = reactive({ open: false, comment: '' })

const doc = computed(() => procedure.data || {})
const isEffective = computed(() => doc.value.status === 'Effective')
const ownerName = computed(() => doc.value.process_owner_name || doc.value.process_owner)
const overdue = computed(() => reviewTone(doc.value.review_due) === 'red')
const quick = computed(() => [
  {
    label: 'Approvers',
    icon: 'lucide-user-check',
    count: doc.value.approvals?.length,
    onClick: () => (showApprovers.value = true),
  },
  {
    label: 'Review comments',
    icon: 'lucide-message-square',
    count: openComments.value,
    onClick: () => comments.value?.$el?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
  },
  {
    label: 'Training',
    icon: 'lucide-graduation-cap',
    onClick: () => router.push('/training/matrix'),
  },
])

const facts = computed(() => {
  const rows = [
    { label: 'Owner', value: ownerName.value, avatar: doc.value.owner_image || null },
    {
      label: 'In force since',
      value: doc.value.effective_from ? shortDate(doc.value.effective_from) : 'Not yet',
    },
    {
      label: overdue.value ? 'Review overdue' : 'Next review',
      value: doc.value.review_due ? shortDate(doc.value.review_due) : 'Not scheduled',
      tone: overdue.value ? 'text-ink-red-3' : null,
    },
    { label: 'Version', value: `Rev ${doc.value.version || 1}` },
    {
      label: 'Read & understood',
      value: doc.value.acknowledged_on
        ? `Rev ${doc.value.acknowledged_version} · ${shortDate(doc.value.acknowledged_on)}`
        : isEffective.value
          ? 'Not signed off'
          : '—',
    },
  ]

  if (doc.value.risk_level) {
    rows.push({
      label: 'Risk',
      value: doc.value.risk_level,
      badge: RISK_THEME[doc.value.risk_level],
    })
  }

  if (doc.value.edited) {
    rows.push({ label: `Last edited by ${doc.value.edited_by}`, value: doc.value.edited })
  }

  if (doc.value.created) {
    rows.push({ label: `Created by ${doc.value.created_by}`, value: doc.value.created })
  }

  return rows
})

const signedOff = computed(
  () => (doc.value.approvals || []).filter((row) => row.decision === 'Approved').length,
)
const needsAcknowledgement = computed(() => isEffective.value && !doc.value.acknowledged)

function load() {
  procedure.submit({ name: route.params.name, revision: revision.value })
  nearby.submit({ name: route.params.name })
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
    !isDesktop.value &&
      doc.value.can_edit && {
        label: 'Edit',
        icon: 'lucide-pencil',
        onClick: () => router.push(`/${route.params.name}/edit`),
      },
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

function printCopy() {
  window.print()
}

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
