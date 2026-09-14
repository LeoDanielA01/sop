import { createResource } from 'frappe-ui'

const RETRIES = 3

export function createRetryingResource(options) {
  let attempts = 0

  const resource = createResource({
    ...options,
    onSuccess(data) {
      attempts = 0
      options.onSuccess?.(data)
    },
    onError(error) {
      options.onError?.(error)

      if (attempts >= RETRIES) return

      attempts += 1
      setTimeout(() => resource.reload(), 300 * attempts)
    },
  })

  return resource
}
