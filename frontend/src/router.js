import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: (to) => ({ path: '/procedures', query: to.query, hash: to.hash }) },
  { path: '/procedures', name: 'Procedures', component: () => import('@/pages/Procedures.vue') },
  { path: '/new', name: 'NewProcedure', component: () => import('@/pages/Editor.vue') },
  { path: '/training', name: 'Training', component: () => import('@/pages/Training.vue') },
  { path: '/training/matrix', name: 'TrainingMatrix', component: () => import('@/pages/TrainingMatrix.vue') },
  { path: '/training/sessions', name: 'TrainingSessions', component: () => import('@/pages/TrainingSessions.vue') },
  { path: '/training/rules', name: 'TrainingRules', component: () => import('@/pages/TrainingRules.vue') },
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

export default createRouter({
  history: createWebHistory('/sop'),
  routes,
})
