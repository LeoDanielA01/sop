import { createRouter, createWebHistory } from 'vue-router'
import { session } from '@/data/session'

const routes = [
  { path: '/', redirect: (to) => ({ path: '/procedures', query: to.query, hash: to.hash }) },
  { path: '/procedures', name: 'Procedures', component: () => import('@/pages/Procedures.vue') },
  { path: '/new', name: 'NewProcedure', component: () => import('@/pages/Editor.vue') },
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
  {
    path: '/:name',
    name: 'Procedure',
    component: () => import('@/pages/Procedure.vue'),
    meta: { fixed: true },
  },
  { path: '/:name/edit', name: 'EditProcedure', component: () => import('@/pages/Editor.vue') },
  { path: '/:name/history', name: 'History', component: () => import('@/pages/History.vue') },
]

const router = createRouter({
  history: createWebHistory('/sop'),
  routes,
})

router.beforeEach((to) => {
  if (to.name === 'NewProcedure' && !session.user.is_author) return { name: 'Procedures' }
})

export default router
