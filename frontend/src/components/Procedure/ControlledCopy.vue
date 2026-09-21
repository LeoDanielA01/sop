<template>
  <Teleport to="body">
    <div id="sop-print">
      <div v-if="mark" class="sop-print-mark" aria-hidden="true">{{ mark }}</div>

      <header class="sop-print-head">
        <div class="sop-print-title">
          <p class="sop-print-no">{{ doc.sop_no }}</p>
          <h1>{{ doc.title }}</h1>
          <p v-if="doc.summary" class="sop-print-summary">{{ doc.summary }}</p>
        </div>

        <table class="sop-print-grid">
          <tbody>
            <tr v-for="(pair, index) in rows" :key="index">
              <template v-for="cell in pair" :key="cell.label">
                <th>{{ cell.label }}</th>
                <td>{{ cell.value || '—' }}</td>
              </template>
            </tr>
          </tbody>
        </table>
      </header>

      <div ref="copy" class="prose-sop sop-print-body" />

      <section class="sop-print-section">
        <h2>{{ __('Approval') }}</h2>
        <table v-if="signatures.length" class="sop-print-table">
          <thead>
            <tr>
              <th>{{ __('Name') }}</th>
              <th>{{ __('Role') }}</th>
              <th>{{ __('Decision') }}</th>
              <th>{{ __('Signed') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in signatures" :key="`${row.approver}-${row.approval_role}`">
              <td>{{ row.approver_name || row.approver }}</td>
              <td>{{ row.approval_role ? __(row.approval_role) : '—' }}</td>
              <td>{{ __(row.decision || 'Pending') }}</td>
              <td>{{ row.signed_at ? stamp(row.signed_at) : '—' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else>{{ __('Not yet approved.') }}</p>
      </section>

      <RevisionHistory :revisions="doc.revisions || []" :current="inForce" print />

      <section v-if="record.change_summary" class="sop-print-section">
        <h2>{{ __('What changed in this revision') }}</h2>
        <p>
          {{ record.change_summary }}
          <template v-if="record.is_material"> · {{ __('Material change — everyone retrained') }}</template>
        </p>
      </section>

      <p ref="note" class="sop-print-notice" />
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import RevisionHistory from '@/components/Procedure/RevisionHistory.vue'
import { session } from '@/data/session'
import { shortDate } from '@/utils/format'
import { translate as __ } from '@/translation'

const props = defineProps({
  doc: { type: Object, required: true },
  body: { type: [Object, null], default: null },
})

const MARKS = {
  superseded: 'Superseded',
  retired: 'Retired',
  draft: 'Not in force',
}

const copy = ref(null)
const note = ref(null)

const record = computed(() => props.doc.copy || {})
const signatures = computed(() => record.value.signatures || [])
const inForce = computed(() =>
  ['Effective', 'Under Revision'].includes(props.doc.status) ? props.doc.effective_revision : null,
)
const mark = computed(() => (MARKS[record.value.state] ? __(MARKS[record.value.state]) : ''))

const rows = computed(() => {
  const doc = props.doc
  const cells = [
    { label: __('Procedure no'), value: doc.sop_no },
    { label: __('Revision'), value: doc.version ? String(doc.version) : __('Draft') },
    { label: __('Status'), value: doc.status && __(doc.status) },
    { label: __('Effective from'), value: shortDate(record.value.effective_from) },
    { label: __('Next review'), value: shortDate(doc.review_due) },
    {
      label: __('Last reviewed'),
      value: doc.last_reviewed_on && `${shortDate(doc.last_reviewed_on)} · ${doc.last_reviewed_by}`,
    },
    { label: __('Owner'), value: doc.process_owner_name || doc.process_owner },
    { label: __('Space'), value: doc.space_title },
    {
      label: __('Process'),
      value: (doc.process_trail || []).map((step) => step.title).join(' › '),
    },
  ]

  const pairs = []
  for (let index = 0; index < cells.length; index += 2) pairs.push(cells.slice(index, index + 2))

  return pairs
})

function notice(at) {
  return __(
    'Printed by {0} on {1}. This copy is uncontrolled after the day it was printed — check the current version in the app before relying on it.',
  ).format(session.user.full_name, stamp(at))
}

function stamp(value) {
  return new Date(value).toLocaleString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function quoted(text) {
  return `"${String(text).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\s+/g, ' ')}"`
}

function pageRules(at) {
  const doc = props.doc
  const head = `${doc.sop_no || ''} · ${__('Rev')} ${doc.version || '—'}`
  const foot = __('Printed by {0} on {1} · uncontrolled after this date').format(
    session.user.full_name,
    shortDate(at),
  )

  return `@page {
  size: A4;
  margin: 18mm 16mm 20mm;
  @top-left { content: ${quoted(head)}; font-size: 8pt; color: #555; }
  @top-right { content: ${quoted(doc.title || '')}; font-size: 8pt; color: #555; }
  @bottom-left { content: ${quoted(foot)}; font-size: 8pt; color: #555; }
  @bottom-right { content: ${quoted(__('Page'))} " " counter(page) " / " counter(pages); font-size: 8pt; color: #555; }
}`
}

function before() {
  if (!copy.value || !props.body) return

  const at = new Date()
  copy.value.replaceChildren(props.body.cloneNode(true))
  for (const branch of copy.value.querySelectorAll('[data-sop-when]')) {
    const label = branch.getAttribute('data-sop-label')
    branch.setAttribute(
      'data-sop-print-label',
      label ? __('Only when {0}').format(label) : __('Conditional section'),
    )
  }
  if (note.value) note.value.textContent = notice(at)

  const style = document.createElement('style')
  style.id = 'sop-print-page'
  style.textContent = pageRules(at)
  document.head.appendChild(style)

  document.documentElement.classList.add('sop-printing')
}

function after() {
  copy.value?.replaceChildren()
  document.getElementById('sop-print-page')?.remove()
  document.documentElement.classList.remove('sop-printing')
}

onMounted(() => {
  window.addEventListener('beforeprint', before)
  window.addEventListener('afterprint', after)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeprint', before)
  window.removeEventListener('afterprint', after)
  after()
})
</script>
