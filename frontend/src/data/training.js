import { createResource } from 'frappe-ui'

export const trainingCounts = createResource({
  url: 'sop.api.training.training_counts',
  auto: true,
})

export const matrix = createResource({
  url: 'sop.api.training.matrix',
})
