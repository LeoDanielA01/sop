import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import StepView from './StepView.vue'

export const TONES = ['critical', 'warning', 'note']
export const HUES = 8

function attribute(name, key, fallback = '') {
  return {
    default: fallback,
    parseHTML: (element) => element.getAttribute(name) || fallback,
    renderHTML: (attrs) => (attrs[key] ? { [name]: attrs[key] } : {}),
  }
}

export function hueOf(editor, phase) {
  const key = (phase || '').trim().toUpperCase()
  if (!key) return ''

  const seen = []
  editor?.state.doc.descendants((node) => {
    if (node.type.name !== 'sopStep') return true
    const known = (node.attrs.phase || '').toUpperCase()
    if (known && !seen.includes(known)) seen.push(known)
    return true
  })

  const index = seen.includes(key) ? seen.indexOf(key) : seen.length
  return String((index % HUES) + 1)
}

export const StepBlock = Node.create({
  name: 'sopStep',
  group: 'block',
  content: 'block+',
  defining: true,
  priority: 60,

  addAttributes() {
    return {
      phase: attribute('data-phase', 'phase'),
      hue: attribute('data-hue', 'hue'),
    }
  },

  parseHTML() {
    return [{ tag: 'div[data-sop="step"]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, { 'data-sop': 'step' }), 0]
  },

  addNodeView() {
    return VueNodeViewRenderer(StepView)
  },

  addCommands() {
    return {
      insertSopStep:
        (phase = '') =>
        ({ chain, editor }) =>
          chain()
            .insertContent({
              type: this.name,
              attrs: { phase: phase.toUpperCase(), hue: hueOf(editor, phase) },
              content: [
                { type: 'paragraph', content: [{ type: 'text', marks: [{ type: 'bold' }], text: 'What is done' }] },
                { type: 'paragraph', content: [{ type: 'text', marks: [{ type: 'italic' }], text: 'Why it matters' }] },
                {
                  type: 'orderedList',
                  content: [{ type: 'listItem', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'First action' }] }] }],
                },
                { type: 'sopStepMeta', content: [{ type: 'text', text: 'Equipment / location' }] },
              ],
            })
            .run(),
    }
  },
})

export const StepMeta = Node.create({
  name: 'sopStepMeta',
  group: 'block',
  content: 'inline*',
  priority: 1100,

  parseHTML() {
    return [{ tag: 'p[data-sop="step-meta"]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['p', mergeAttributes(HTMLAttributes, { 'data-sop': 'step-meta' }), 0]
  },
})

export const CalloutBlock = Node.create({
  name: 'sopCallout',
  group: 'block',
  content: 'block+',
  defining: true,
  priority: 60,

  addAttributes() {
    return {
      tone: attribute('data-tone', 'tone', 'warning'),
    }
  },

  parseHTML() {
    return [{ tag: 'div[data-sop="callout"]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, { 'data-sop': 'callout' }), 0]
  },

  addCommands() {
    return {
      insertSopCallout:
        (tone = 'warning', title = '', body = '') =>
        ({ chain }) =>
          chain()
            .insertContent({
              type: this.name,
              attrs: { tone },
              content: [
                { type: 'paragraph', content: [{ type: 'text', marks: [{ type: 'bold' }], text: title }] },
                { type: 'paragraph', content: [{ type: 'text', text: body }] },
              ],
            })
            .run(),
    }
  },
})
