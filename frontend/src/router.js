import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Procedures', component: () => import('@/pages/Procedures.vue') },
  { path: '/new', name: 'NewProcedure', component: () => import('@/pages/Editor.vue') },
  { path: '/training', name: 'Training', component: () => import('@/pages/Training.vue') },
  { path: '/training/matrix', name: 'TrainingMatrix', component: () => import('@/pages/TrainingMatrix.vue') },
  { path: '/:name', name: 'Procedure', component: () => import('@/pages/Procedure.vue') },
  { path: '/:name/edit', name: 'EditProcedure', component: () => import('@/pages/Editor.vue') },
  { path: '/:name/history', name: 'History', component: () => import('@/pages/History.vue') },
]

export default createRouter({
  history: createWebHistory('/sop'),
  routes,
})
