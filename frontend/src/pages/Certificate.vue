<template>
  <PageHeader class="print:hidden">
    <AppBreadcrumbs :tail="[{ label: __('Certificate') }]" />
    <div class="flex items-center gap-2">
      <Button variant="ghost" icon-left="lucide-arrow-left" :label="__('Back')" @click="router.back()" />
      <Button variant="solid" icon-left="lucide-printer" :label="__('Print or save as PDF')" :disabled="!data" @click="print" />
    </div>
  </PageHeader>

  <div class="mx-auto w-full max-w-[860px] px-3 pb-12 pt-6 sm:px-5">
    <ErrorMessage v-if="record.error" :message="record.error.messages?.[0] || record.error.message" />

    <Skeleton v-else-if="!data" class="aspect-[1.414] w-full rounded-3" />

    <article
      v-else
      class="certificate relative flex aspect-[1.414] w-full flex-col items-center justify-center rounded-3 border-2 border-outline-gray-3 bg-surface-base px-10 py-10 text-center"
    >
      <div class="pointer-events-none absolute inset-3 rounded-2 border border-outline-gray-2" aria-hidden="true" />

      <span class="lucide-award size-12 text-ink-gray-7" aria-hidden="true" />

      <p class="mt-4 text-sm font-medium uppercase tracking-[0.2em] text-ink-gray-5">
        {{ data.is_refresher ? __('Certificate of refresher training') : __('Certificate of training') }}
      </p>

      <p class="mt-6 text-base text-ink-gray-6">{{ __('This certifies that') }}</p>
      <p class="mt-2 text-3xl font-semibold text-ink-gray-9">{{ data.trainee }}</p>

      <p class="mt-6 max-w-lg text-base text-ink-gray-6">
        {{ __('has been trained and assessed as competent in') }}
      </p>
      <p class="mt-2 text-xl font-semibold text-ink-gray-9">{{ data.title }}</p>
      <p class="mt-1 font-mono text-sm text-ink-gray-6">{{ data.sop_no }} · {{ __('Revision {0}').format(data.version) }}</p>

      <dl class="mt-8 grid w-full max-w-xl grid-cols-2 gap-x-6 gap-y-3 text-left text-sm sm:grid-cols-4">
        <div>
          <dt class="text-ink-gray-5">{{ __('Completed') }}</dt>
          <dd class="mt-0.5 text-ink-gray-9">{{ longDate(data.completed_on) }}</dd>
        </div>
        <div>
          <dt class="text-ink-gray-5">{{ __('Method') }}</dt>
          <dd class="mt-0.5 text-ink-gray-9">{{ data.method }}</dd>
        </div>
        <div>
          <dt class="text-ink-gray-5">{{ __('Score') }}</dt>
          <dd class="mt-0.5 text-ink-gray-9">{{ data.score ? `${data.score}%` : '—' }}</dd>
        </div>
        <div>
          <dt class="text-ink-gray-5">{{ __('Assessed by') }}</dt>
          <dd class="mt-0.5 text-ink-gray-9">{{ data.assessed_by || '—' }}</dd>
        </div>
      </dl>

      <p class="mt-8 font-mono text-xs text-ink-gray-5">
        {{ data.organisation ? `${data.organisation} · ` : '' }}{{ __('Record {0}').format(data.name) }}
      </p>
    </article>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, ErrorMessage, PageHeader, Skeleton, createResource } from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import { translate as __ } from '@/translation'

const route = useRoute()
const router = useRouter()

const record = createResource({
  url: 'sop.api.training.certificate',
  auto: true,
  makeParams: () => ({ name: route.params.name }),
})

const data = computed(() => record.data || null)

function longDate(value) {
  if (!value) return '—'
  return new Date(String(value).replace(' ', 'T')).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}

function print() {
  window.print()
}
</script>

<style>
@media print {
  @page {
    size: A4 landscape;
    margin: 12mm;
  }
  body * {
    visibility: hidden;
  }
  .certificate,
  .certificate * {
    visibility: visible;
  }
  .certificate {
    position: fixed;
    inset: 0;
    margin: auto;
    width: 100%;
    height: auto;
  }
}
</style>
