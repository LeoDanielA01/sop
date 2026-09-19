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
        :label="__('Edit')"
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
        <Button variant="ghost" icon="lucide-ellipsis" :label="__('More')" />
      </Dropdown>
    </div>
  </PageHeader>

  <div class="flex flex-col lg:min-h-0 lg:flex-1 lg:flex-row lg:overflow-hidden">
    <aside
      v-if="!ui.fullScreen"
      class="order-first w-full shrink-0 border-b border-outline-gray-1 lg:order-last lg:w-[17rem] lg:overflow-hidden lg:border-b-0 lg:border-l"
    >
      <div class="flex h-full flex-col">
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
          {{ doc.status }} not in "Force"
        </div>

        <div class="shrink-0 border-b border-outline-gray-1 px-4 py-3">
          <div class="flex items-start gap-2">
            <p class="min-w-0 flex-1 text-base font-semibold text-ink-gray-9">
              {{ doc.title }}
            </p>

            <div class="flex shrink-0 items-center">
              <Tooltip v-if="doc.can_edit" :text="__('Edit')">
                <Button
                  variant="ghost"
                  size="sm"
                  icon="lucide-pencil"
                  :label="__('Edit')"
                  @click="router.push(`/${route.params.name}/edit`)"
                />
              </Tooltip>
              <Tooltip :text="__('Print a controlled copy')">
                <Button
                  variant="ghost"
                  size="sm"
                  icon="lucide-printer"
                  :label="__('Print')"
                  @click="printCopy"
                />
              </Tooltip>
              <Tooltip :text="__('Revision history')">
                <Button
                  variant="ghost"
                  size="sm"
                  icon="lucide-history"
                  :label="__('Revision history')"
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
            <span
              :class="row.trailing || 'lucide-plus'"
              class="size-4 shrink-0 text-ink-gray-5"
              aria-hidden="true"
            />
          </button>
        </div>

        <ScrollArea class="min-h-0 flex-1">
          <dl class="divide-y divide-outline-gray-1">
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
        </ScrollArea>
      </div>
    </aside>

    <ScrollArea class="min-w-0 lg:min-h-0 lg:flex-1" viewport-class="px-4 pb-24 pt-5 sm:px-6">
    <ErrorMessage :message="lastError" class="mb-4" />

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

    <LiveBlocks :root="body" :sop="doc.name" :revision="revision" :content="doc.content" />

    <QuizEditor v-if="doc.can_quiz" v-model:open="showQuiz" :sop="doc.name" @update:open="(value) => !value && load()" />

    <ClarityFeedback
      v-if="doc.name && isEffective"
      :sop="doc.name"
      :version="doc.version"
      @summary="(value) => (clarity = value)"
    />

    <nav
      v-if="around.previous || around.next"
      class="mt-10 grid gap-3 border-t border-outline-gray-1 pt-5 sm:grid-cols-2"
    >
      <button
        v-if="around.previous"
        type="button"
        class="flex items-center gap-3 rounded-4 border border-outline-gray-2 px-3 py-2.5 text-left hover:border-outline-gray-3"
        :data-context-link="`/${around.previous.name}`"
        @click="router.push(`/${around.previous.name}`)"
      >
        <span class="lucide-chevron-left size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
        <span class="min-w-0">
          <span class="block text-sm text-ink-gray-5">{{ __('Previous') }}</span>
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
        :data-context-link="`/${around.next.name}`"
        @click="router.push(`/${around.next.name}`)"
      >
        <span class="min-w-0">
          <span class="block text-sm text-ink-gray-5">{{ __('Next') }}</span>
          <span class="block truncate text-base text-ink-gray-8">{{ around.next.title }}</span>
        </span>
        <span class="lucide-chevron-right size-4 shrink-0 text-ink-gray-5" aria-hidden="true" />
      </button>
    </nav>

    <ReviewComments
      v-if="doc.name && doc.review?.visible"
      ref="comments"
      :sop="doc.name"
      :version="doc.version"
      :body="body"
      :rights="doc.review || {}"
      @count="(value) => (openComments = value)"
    />
    </ScrollArea>
  </div>

  <div
    v-if="doc.actions?.decide"
    class="sticky bottom-0 shrink-0 border-t border-outline-gray-1 bg-surface-base px-4 py-3 sm:px-6"
  >
    <div class="flex w-full items-center justify-between gap-4">
      <p class="text-sm text-ink-gray-6">
        {{
          openComments
            ? __('Resolve the {0} open comments before approving.').format(openComments)
            : __('Your approval is what this one is waiting on.')
        }}
      </p>
      <div class="flex items-center gap-2">
        <Button
          variant="subtle"
          :label="openComments ? `Request changes (${openComments})` : 'Request changes'"
          @click="changes.open = true"
        />
        <Button
          variant="solid"
          :label="__('Approve')"
          :loading="decide.loading"
          :disabled="openComments > 0"
          :tooltip="openComments ? __('Every comment has to be resolved first') : undefined"
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
        {{ __('Confirm you have read and understood') }} <b>Rev {{ doc.version }}</b>{{ __('. You will be asked again when a new revision comes into force.') }}
      </p>
      <Button
        variant="solid"
        :label="__('I have read this')"
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

  <ReviewRouteDialog
    v-model:open="showRoute"
    :mode="routeMode"
    :sop="doc.name"
    :current="doc.approvals || []"
    :loading="send.loading"
    :error="send.error?.messages?.[0] || ''"
    @send="send.submit({ sop: doc.name })"
  />

  <Dialog v-model:open="showPublish" :title="__('Bring into force')" size="sm">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="release.error?.messages?.[0]" />
        <FormControl type="date" :label="__('Effective from')" v-model="publishOn" />
        <FormControl
          type="textarea"
          :label="__('What changed')"
          :placeholder="__('Shown in the revision history')"
          v-model="changeSummary"
        />
        <FormControl
          type="checkbox"
          :label="__('Material change — everyone has to be trained again')"
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

  <Dialog v-model:open="changes.open" :title="__('Request changes')" size="sm">
    <template #default>
      <div class="flex flex-col gap-3">
        <ErrorMessage :message="decide.error?.messages?.[0]" />
        <p v-if="openComments" class="text-sm text-ink-gray-6">
          {{ openComments }} comment{{ openComments === 1 ? '' : 's' }} on the text
          {{ openComments === 1 ? 'is' : 'are' }} already on this revision. This note goes with them.
        </p>
        <FormControl type="textarea" :label="__('What has to change')" v-model="changes.comment" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="solid"
          theme="red"
          :label="__('Send it back')"
          :loading="decide.loading"
          :disabled="!changes.comment"
          @click="decide.submit({ sop: doc.name, decision: 'Rejected', comment: changes.comment })"
        />
      </div>
    </template>
  </Dialog>

  <CompareRevisionsModal
    v-model="showCompareModal"
    :sop-name="doc.name || route.params.name"
  />
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
  ScrollArea,
  Select,
  Tooltip,
  createResource,
} from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import ClarityFeedback from '@/components/Procedure/ClarityFeedback.vue'
import ReviewComments from '@/components/Procedure/ReviewComments.vue'
import ReviewRouteDialog from '@/components/Procedure/ReviewRouteDialog.vue'
import MentionChip from '@/components/Procedure/MentionChip.vue'
import LiveBlocks from '@/components/Procedure/LiveBlocks.vue'
import QuizEditor from '@/components/Training/QuizEditor.vue'
import CompareRevisionsModal from '@/components/Procedure/CompareRevisionsModal.vue'
import { openRoom, roomUnread } from '@/data/chat'
import { acknowledge, procedure } from '@/data/procedures'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { useUI } from '@/stores/ui'
import { refreshCounts } from '@/data/navigation'
import { STATUS_THEME, reviewTone, shortDate, today } from '@/utils/format'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()
const { isDesktop } = useBreakpoint()
const ui = useUI()

const RISK_THEME = { High: 'red', Medium: 'orange', Low: 'green' }

const openComments = ref(0)
const clarity = ref(null)
const showCompareModal = ref(false)

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
const showQuiz = ref(false)
const body = ref(null)
const showRoute = ref(false)
const routeMode = ref('view')

function openRoute(mode) {
  routeMode.value = mode
  showRoute.value = true
}
const comments = ref(null)
const showPublish = ref(false)
const publishOn = ref(today())
const changeSummary = ref('')
const isMaterial = ref(true)
const changes = reactive({ open: false, comment: '' })

const doc = computed(() => procedure.data || {})

watch(
  () => doc.value.review?.visible,
  (visible) => {
    if (!visible) openComments.value = 0
  },
)

const isEffective = computed(() => doc.value.status === 'Effective')
const ownerName = computed(() => doc.value.process_owner_name || doc.value.process_owner)
const overdue = computed(() => reviewTone(doc.value.review_due) === 'red')
const quick = computed(() =>
  [
    {
      label: __('Reviewers'),
      icon: 'lucide-user-check',
      count: doc.value.approvals?.length,
      trailing: 'lucide-chevron-right',
      onClick: () => openRoute('view'),
    },
    {
      label: __('Review comments'),
      icon: 'lucide-message-square',
      count: openComments.value,
      trailing: 'lucide-chevron-right',
      hidden: !doc.value.review?.visible,
      onClick: () =>
        body.value
          ?.querySelector('mark[data-review]')
          ?.scrollIntoView({ behavior: 'smooth', block: 'center' }),
    },
    {
      label: __('Discussion'),
      icon: 'lucide-messages-square',
      count: roomUnread(doc.value.name),
      trailing: 'lucide-chevron-right',
      hidden: !doc.value.can_discuss,
      onClick: () => openRoom(doc.value.name),
    },
    {
      label: __('Quiz questions'),
      icon: 'lucide-clipboard-check',
      count: doc.value.quiz_questions,
      trailing: 'lucide-chevron-right',
      hidden: !doc.value.can_quiz,
      onClick: () => (showQuiz.value = true),
    },
    {
      label: __('Training'),
      icon: 'lucide-graduation-cap',
      onClick: () => router.push('/training/matrix'),
    },
  ].filter((row) => !row.hidden),
)

const facts = computed(() => {
  const rows = [
    { label: __('Owner'), value: ownerName.value, avatar: doc.value.owner_image || null },
    {
      label: __('In force since'),
      value: doc.value.effective_from ? shortDate(doc.value.effective_from) : 'Not yet',
    },
    {
      label: overdue.value ? 'Review overdue' : 'Next review',
      value: doc.value.review_due ? shortDate(doc.value.review_due) : 'Not scheduled',
      tone: overdue.value ? 'text-ink-red-3' : null,
    },
    { label: __('Version'), value: `Rev ${doc.value.version || 1}` },
    {
      label: __('Read & understood'),
      value: doc.value.acknowledged_on
        ? `Rev ${doc.value.acknowledged_version} · ${shortDate(doc.value.acknowledged_on)}`
        : isEffective.value
          ? 'Not signed off'
          : '—',
    },
  ]

  if (clarity.value?.can_see_notes && clarity.value.total) {
    const percent = clarity.value.percent

    rows.push({
      label: __('Clarity'),
      value: __('{0}% clear · {1} votes').format(percent, clarity.value.total),
      badge: percent >= 80 ? 'green' : percent >= 50 ? 'amber' : 'red',
    })
  }

  if (doc.value.risk_level) {
    rows.push({
      label: __('Risk'),
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
  showRoute.value = false
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
      label: __('Send for review'),
      icon: 'lucide-send',
      loading: send.loading,
      onClick: () => openRoute('send'),
    }
  }

  if (allowed.publish) {
    return {
      label: __('Bring into force'),
      icon: 'lucide-badge-check',
      loading: release.loading,
      onClick: () => (showPublish.value = true),
    }
  }

  if (allowed.start_revision) {
    return {
      label: __('Start a revision'),
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
        label: __('Edit'),
        icon: 'lucide-pencil',
        onClick: () => router.push(`/${route.params.name}/edit`),
      },
    {
      label: __('Revision history'),
      icon: 'lucide-history',
      onClick: () => router.push(`/${route.params.name}/history`),
    },
    {
      label: __('Compare revisions'),
      icon: 'lucide-git-compare',
      onClick: () => (showCompareModal.value = true),
    },
    { label: __('Print controlled copy'), icon: 'lucide-printer', onClick: () => window.print() },
    doc.value.actions?.retire && {
      label: __('Retire'),
      icon: 'lucide-archive',
      onClick: () => withdraw.submit({ sop: doc.value.name }),
    },
    doc.value.actions?.delete && {
      label: __('Delete draft'),
      icon: 'lucide-trash-2',
      theme: 'red',
      onClick: () =>
        (ui.removeProcedure = { name: doc.value.name, sop_no: doc.value.sop_no, mode: 'draft' }),
    },
    doc.value.actions?.purge && {
      label: __('Delete permanently'),
      icon: 'lucide-trash-2',
      theme: 'red',
      onClick: () =>
        (ui.removeProcedure = { name: doc.value.name, sop_no: doc.value.sop_no, mode: 'purge' }),
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
