import { createRouter, createWebHistory } from 'vue-router'
import { session } from '@/data/session'

const routes = [
  { path: '/', redirect: (to) => ({ path: '/procedures', query: to.query, hash: to.hash }) },
  { path: '/procedures', name: 'Procedures', component: () => import('@/pages/Procedures.vue') },
  { path: '/new', name: 'NewProcedure', component: () => import('@/pages/Editor.vue') },
  { path: '/import', name: 'ImportProcedures', component: () => import('@/pages/Import.vue') },
  { path: '/training', name: 'Training', component: () => import('@/pages/Training.vue') },
  { path: '/training/matrix', name: 'TrainingMatrix', component: () => import('@/pages/TrainingMatrix.vue') },
  { path: '/training/sessions', name: 'TrainingSessions', component: () => import('@/pages/TrainingSessions.vue') },
  { path: '/training/rules', name: 'TrainingRules', component: () => import('@/pages/TrainingRules.vue') },
  {
    path: '/training/certificate/:name',
    name: 'Certificate',
    component: () => import('@/pages/Certificate.vue'),
  },
  { path: '/insights', name: 'Insights', component: () => import('@/pages/Insights.vue') },
  { path: '/where-used', name: 'WhereUsed', component: () => import('@/pages/WhereUsed.vue') },
  { path: '/issue', name: 'IssueResource', component: () => import('@/pages/IssueResource.vue') },
  { path: '/issue-ppe', redirect: '/issue' },
  { path: '/records/:doctype', name: 'RecordList', component: () => import('@/pages/RecordList.vue') },
  { path: '/records/:doctype/:name(.*)', name: 'Record', component: () => import('@/pages/Record.vue') },
  {
    path: '/:name',
    name: 'Procedure',
    component: () => import('@/pages/Procedure.vue'),
    meta: { fixed: true },
  },
  { path: '/:name/edit', name: 'EditProcedure', component: () => import('@/pages/Editor.vue') },
  { path: '/:name/history', name: 'History', component: () => import('@/pages/History.vue') },
  { path: '/:name/sign', name: 'Sign', component: () => import('@/pages/Sign.vue') },
]

const router = createRouter({
  history: createWebHistory('/sop'),
  routes,
})

router.beforeEach((to) => {
  if (['NewProcedure', 'ImportProcedures'].includes(to.name) && !session.user.is_author) return { name: 'Procedures' }
})

export default router
