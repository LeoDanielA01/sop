import { onBeforeUnmount, ref } from 'vue'

/** Matches Tailwind's `sm`. Below it the rail and sidebar are replaced by a
 *  bottom bar, because neither fits a phone held one-handed on a shop floor. */
const query = window.matchMedia('(min-width: 640px)')

export function useBreakpoint() {
  const isDesktop = ref(query.matches)

  const update = (event) => (isDesktop.value = event.matches)
  query.addEventListener('change', update)
  onBeforeUnmount(() => query.removeEventListener('change', update))

  return { isDesktop }
}
