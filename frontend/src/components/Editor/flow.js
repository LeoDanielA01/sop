import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import AskView from './AskView.vue'
import WhenView from './WhenView.vue'
import { SEPARATOR, answersOf, parseCondition } from '@/data/flow'

function attribute(name, key) {
  return {
    default: '',
    parseHTML: (element) => element.getAttribute(name) || '',
    renderHTML: (attrs) => (attrs[key] ? { [name]: attrs[key] } : {}),
  }
}

export const WhenBlock = Node.create({
  name: 'sopWhen',
  group: 'block',
  content: 'block+',
  defining: true,
  priority: 60,

  addAttributes() {
    return {
      when: attribute('data-sop-when', 'when'),
      label: attribute('data-sop-label', 'label'),
    }
  },

  parseHTML() {
    return [{ tag: 'div[data-sop-when]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, { class: 'sop-when' }), 0]
  },

  addNodeView() {
    return VueNodeViewRenderer(WhenView)
  },

  addCommands() {
    return {
      wrapInWhen:
        (attrs) =>
        ({ chain }) =>
          chain().wrapIn(this.name, attrs).run(),

      insertWhen:
        (attrs) =>
        ({ chain }) =>
          chain()
            .insertContent({ type: this.name, attrs, content: [{ type: 'paragraph' }] })
            .run(),
    }
  },
})

export const AskBlock = Node.create({
  name: 'sopAsk',
  group: 'block',
  content: 'inline*',
  defining: true,
  priority: 60,

  addAttributes() {
    return {
      ask: attribute('data-sop-ask', 'ask'),
      options: attribute('data-sop-options', 'options'),
    }
  },

  parseHTML() {
    return [{ tag: 'div[data-sop-ask]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['div', mergeAttributes(HTMLAttributes, { class: 'sop-ask' }), 0]
  },

  addNodeView() {
    return VueNodeViewRenderer(AskView)
  },

  addCommands() {
    return {
      insertAsk:
        (attrs) =>
        ({ chain }) =>
          chain()
            .insertContent({
              type: this.name,
              attrs,
              content: [{ type: 'text', text: 'What happened?' }],
            })
            .run(),
    }
  },
})

export function asksOf(editor) {
  const found = []
  if (!editor) return found

  editor.state.doc.descendants((node, pos) => {
    if (node.type.name !== 'sopAsk') return true

    found.push({
      id: node.attrs.ask,
      question: node.textContent.trim(),
      options: answersOf(node.attrs.options),
      pos,
      size: node.nodeSize,
    })

    return true
  })

  return found
}

function whensOf(editor) {
  const found = []

  editor.state.doc.descendants((node, pos) => {
    if (node.type.name !== 'sopWhen') return true

    found.push({
      spec: parseCondition(node.attrs.when),
      raw: node.attrs.when,
      label: node.attrs.label,
      empty: node.textContent.trim() === '',
      pos,
      size: node.nodeSize,
    })

    return true
  })

  return found
}

function issue(kind, text, message, node) {
  return {
    kind,
    group: 'procedure',
    text,
    message,
    pos: Math.max(node.pos - 1, 0),
    index: 0,
    length: node.size,
  }
}

export function flowIssues(editor) {
  if (!editor) return []

  const asks = asksOf(editor)
  const whens = whensOf(editor)
  const found = []
  const seen = []

  for (const ask of asks) {
    if (!ask.options.length) {
      found.push(
        issue('branch', ask.question, `Give this question some answers, split by “${SEPARATOR}”.`, ask),
      )
      continue
    }

    if (seen.includes(ask.id)) {
      found.push(issue('branch', ask.question, 'Two questions share the same id.', ask))
    }
    seen.push(ask.id)

    for (const option of ask.options) {
      const answered = whens.some(
        (when) => when.spec?.kind === 'ask' && when.spec.ask === ask.id && when.spec.target === option,
      )

      if (!answered) {
        found.push(issue('branch', ask.question, `Nothing happens when the answer is “${option}”.`, ask))
      }
    }
  }

  for (const when of whens) {
    if (!when.spec) {
      found.push(issue('condition', when.label || when.raw, 'This condition cannot be read.', when))
      continue
    }

    if (when.empty) {
      found.push(issue('condition', when.label || when.raw, 'This branch is empty.', when))
    }

    if (when.spec.kind !== 'ask') continue

    const ask = asks.find((row) => row.id === when.spec.ask)

    if (!ask) {
      found.push(issue('condition', when.label || when.raw, 'There is no question to answer this.', when))
    } else if (ask.options.length && !ask.options.includes(when.spec.target)) {
      found.push(
        issue('condition', when.label || when.raw, `“${when.spec.target}” is not one of the answers.`, when),
      )
    } else if (ask.pos > when.pos) {
      found.push(issue('condition', when.label || when.raw, 'The question comes after this branch.', when))
    }
  }

  return found
}
