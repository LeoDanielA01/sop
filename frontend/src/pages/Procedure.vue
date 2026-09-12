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
        variant="subtle"
        icon-left="lucide-pencil"
        label="Edit"
        @click="router.push(`/${route.params.name}/edit`)"
      />
      <Dropdown :options="actions">
        <Button variant="ghost" icon="lucide-ellipsis" label="Procedure actions" />
      </Dropdown>
    </div>
  </PageHeader>

  <div class="mx-auto mt-5 w-full max-w-[740px] px-3 pb-24 sm:px-5">
    <div
      v-if="doc.status && !isEffective"
      class="mb-5 rounded-lg border border-outline-amber-2 bg-surface-amber-1 px-4 py-3 text-base text-ink-amber-3"
    >
      This is a <b>{{ doc.status?.toLowerCase() }}</b> version and is not in force.
      <template v-if="doc.effective_revision">
        The effective one is
        <Button
          variant="ghost"
          size="sm"
          :label="`Rev ${doc.effective_revision}`"
          @click="revision = doc.effective_revision"
        />
      </template>
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
    v-if="needsAcknowledgement"
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
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Avatar, Badge, Button, Dropdown, PageHeader, PageHeaderTitle, Select } from 'frappe-ui'
import MentionChip from '@/components/MentionChip.vue'
import { acknowledge, procedure } from '@/data/procedures'
import { STATUS_THEME, reviewTone, shortDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const revision = ref(null)
const body = ref(null)

const doc = computed(() => procedure.data || {})
const isEffective = computed(() => doc.value.status === 'Effective')
const needsAcknowledgement = computed(() => isEffective.value && !doc.value.acknowledged)

const actions = computed(() =>
  [
    { label: 'Print controlled copy', icon: 'lucide-printer', onClick: () => window.print() },
    {
      label: 'Revision history',
      icon: 'lucide-history',
      onClick: () => router.push(`/${route.params.name}/history`),
    },
    doc.value.can_edit && {
      label: 'Edit',
      icon: 'lucide-pencil',
      onClick: () => router.push(`/${route.params.name}/edit`),
    },
  ].filter(Boolean),
)

function load() {
  procedure.submit({ name: route.params.name, revision: revision.value })
}

onMounted(load)
watch(() => [route.params.name, revision.value], load)
</script>
