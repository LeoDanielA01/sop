<template>
  <PageHeader class="sop-no-print">
    <AppBreadcrumbs :tail="[{ label: sign.data?.sop_no || route.params.name, route: `/${route.params.name}` }, { label: __('Sign') }]" />
    <Button variant="solid" icon-left="lucide-printer" :label="__('Print sign')" :disabled="!sign.data" @click="print" />
  </PageHeader>

  <div class="flex justify-center bg-surface-gray-1 px-3 py-6 print:block print:bg-white print:p-0">
    <ErrorMessage :message="sign.error?.messages?.[0] || sign.error?.message" />

    <article v-if="sign.data" class="sop-sign">
      <header class="sop-sign-head">
        <div class="min-w-0">
          <p class="sop-sign-id">{{ sign.data.sop_no }} · v{{ sign.data.version || 0 }}.0</p>
          <h1 class="sop-sign-title">{{ sign.data.title }}</h1>
          <p v-if="sign.data.summary" class="sop-sign-summary">{{ sign.data.summary }}</p>
        </div>
        <figure v-if="sign.data.qr" class="sop-sign-qr">
          <img :src="sign.data.qr" :alt="__('QR code to the live procedure')" />
          <figcaption>{{ __('Scan for the current procedure') }}</figcaption>
        </figure>
      </header>

      <section v-for="(item, index) in sign.data.criticals" :key="index" class="sop-sign-critical">
        <p class="sop-sign-critical-title">⚠ {{ item.title || __('CRITICAL') }}</p>
        <p v-if="item.text">{{ item.text }}</p>
      </section>

      <section v-if="sign.data.gear.length" class="sop-sign-gear">
        <h2>{{ __('Required before you start') }}</h2>
        <ul>
          <li v-for="item in sign.data.gear" :key="item.label">
            <span :class="item.icon || 'lucide-shield-check'" class="size-6 shrink-0" aria-hidden="true" />
            <span>
              <b>{{ item.label }}</b>
              <small v-if="item.type">{{ item.type }}</small>
            </span>
          </li>
        </ul>
      </section>

      <footer class="sop-sign-foot">
        <span>{{ __('Printed {0}. Always follow the live procedure — scan the code.').format(today) }}</span>
        <span class="truncate">{{ sign.data.url }}</span>
      </footer>
    </article>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { Button, ErrorMessage, PageHeader, createResource } from 'frappe-ui'
import AppBreadcrumbs from '@/components/Layouts/AppBreadcrumbs.vue'
import { translate as __ } from '@/translation'

const route = useRoute()
const today = new Date().toLocaleDateString()

const sign = createResource({
  url: 'sop.api.signs.sign',
  params: { sop: route.params.name },
  auto: true,
})

function print() {
  window.print()
}
</script>

<style scoped>
.sop-sign {
  display: flex;
  width: 210mm;
  min-height: 297mm;
  flex-direction: column;
  gap: 8mm;
  background: #fff;
  padding: 14mm;
  color: #111;
  box-shadow: 0 1px 4px rgb(0 0 0 / 0.12);
}
.sop-sign-head {
  display: flex;
  align-items: flex-start;
  gap: 8mm;
  border-bottom: 3px solid #111;
  padding-bottom: 6mm;
}
.sop-sign-head > div {
  flex: 1;
}
.sop-sign-id {
  font-family: ui-monospace, monospace;
  font-size: 13pt;
  color: #444;
}
.sop-sign-title {
  margin-top: 2mm;
  font-size: 30pt;
  font-weight: 800;
  line-height: 1.1;
}
.sop-sign-summary {
  margin-top: 3mm;
  font-size: 13pt;
  color: #333;
}
.sop-sign-qr {
  width: 42mm;
  text-align: center;
  font-size: 9pt;
  color: #444;
}
.sop-sign-qr img {
  width: 42mm;
  height: 42mm;
}
.sop-sign-critical {
  border: 4px solid #c00;
  border-radius: 4mm;
  background: #fff1f1;
  padding: 6mm;
  font-size: 15pt;
  line-height: 1.4;
}
.sop-sign-critical-title {
  margin-bottom: 2mm;
  font-size: 20pt;
  font-weight: 800;
  color: #c00;
}
.sop-sign-gear h2 {
  margin-bottom: 4mm;
  font-size: 18pt;
  font-weight: 700;
}
.sop-sign-gear ul {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4mm;
}
.sop-sign-gear li {
  display: flex;
  align-items: center;
  gap: 4mm;
  border: 2px solid #1d4ed8;
  border-radius: 3mm;
  padding: 3mm 4mm;
  font-size: 13pt;
}
.sop-sign-gear small {
  display: block;
  font-size: 9pt;
  color: #555;
}
.sop-sign-foot {
  display: flex;
  margin-top: auto;
  justify-content: space-between;
  gap: 6mm;
  border-top: 1px solid #999;
  padding-top: 3mm;
  font-size: 9pt;
  color: #555;
}
@media print {
  .sop-sign {
    width: auto;
    min-height: 0;
    box-shadow: none;
    padding: 0;
  }
  * {
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }
}
@page {
  size: A4;
  margin: 12mm;
}
</style>
