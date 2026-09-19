import {
  AlignCenter,
  AlignLeft,
  AlignRight,
  Blockquote,
  Bold,
  BulletList,
  FontColor,
  HeadingGroup,
  HorizontalRule,
  InlineCode,
  InsertImage,
  InsertLink,
  InsertTable,
  Italic,
  OrderedList,
  Redo,
  Separator,
  Strike,
  Undo,
} from 'frappe-ui/editor'

import { translate as __ } from '@/translation'

export const CONTEXTS = {
  TEXT: 'text',
  EMPTY: 'empty',
  TABLE: 'table',
  IMAGE: 'image',
}

function codeBlockItem() {
  return {
    icon: 'lucide-square-code',
    label: __('Code block'),
    action: (editor) => editor.chain().focus().toggleCodeBlock().run(),
    isActive: (editor) => editor.isActive('codeBlock'),
  }
}

function checklistItem() {
  return {
    icon: 'lucide-list-todo',
    label: __('Checklist'),
    action: (editor) => editor.chain().focus().toggleTaskList().run(),
    isActive: (editor) => editor.isActive('taskList'),
  }
}

function clearFormatItem() {
  return {
    icon: 'lucide-remove-formatting',
    label: __('Clear formatting'),
    action: (editor) => editor.chain().focus().unsetAllMarks().clearNodes().run(),
  }
}

function procedureItems(api) {
  return {
    step: {
      icon: 'lucide-list-checks',
      label: __('Step'),
      action: () => api.insertStep(),
    },
    warning: {
      icon: 'lucide-triangle-alert',
      label: __('Warning'),
      action: () => api.insertCallout('warning'),
    },
    note: {
      icon: 'lucide-info',
      label: __('Note'),
      action: () => api.insertCallout('note'),
    },
    record: {
      icon: 'lucide-at-sign',
      label: __('Mention a record'),
      action: () => api.pickRecord(),
    },
    person: {
      icon: 'lucide-user',
      label: __('Mention a person'),
      action: () => api.pickPerson(),
    },
    live: {
      icon: 'lucide-activity',
      label: __('Live value'),
      action: () => api.insertLive(),
    },
    check: {
      icon: 'lucide-circle-check',
      label: __('Check'),
      action: () => api.insertCheck(),
    },
  }
}

export function fixedItems(api) {
  const sop = procedureItems(api)

  return [
    HeadingGroup,
    Separator,
    Bold,
    Italic,
    Strike,
    InlineCode,
    FontColor,
    InsertLink,
    Separator,
    BulletList,
    OrderedList,
    checklistItem(),
    Separator,
    Blockquote,
    codeBlockItem(),
    HorizontalRule,
    Separator,
    InsertTable,
    InsertImage,
    Separator,
    sop.step,
    sop.warning,
    sop.note,
    sop.record,
    sop.person,
    sop.live,
    sop.check,
    Separator,
    AlignLeft,
    AlignCenter,
    AlignRight,
    Separator,
    clearFormatItem(),
    Undo,
    Redo,
  ]
}

export function bubbleItems() {
  return [
    HeadingGroup,
    Separator,
    Bold,
    Italic,
    Strike,
    InlineCode,
    Separator,
    InsertLink,
    FontColor,
    Separator,
    BulletList,
    OrderedList,
    Separator,
    Blockquote,
    codeBlockItem(),
  ]
}

export function contextAt(editor) {
  if (!editor) return { kind: CONTEXTS.EMPTY }

  if (editor.isActive('table')) return { kind: CONTEXTS.TABLE }
  if (editor.isActive('image')) return { kind: CONTEXTS.IMAGE }
  if (editor.state.selection.empty) return { kind: CONTEXTS.EMPTY }

  return { kind: CONTEXTS.TEXT }
}

const MOD = navigator.platform?.toLowerCase().includes('mac') ? '⌘' : 'Ctrl'

function heading(level) {
  return {
    key: `h${level}`,
    icon: `lucide-heading-${level}`,
    label: `Heading ${level}`,
    hint: `${MOD} ⌥ ${level}`,
    run: (editor) => editor.chain().focus().toggleHeading({ level }).run(),
    active: (editor) => editor.isActive('heading', { level }),
  }
}

const FORMAT = [
  {
    key: 'bold',
    icon: 'lucide-bold',
    label: 'Bold',
    hint: `${MOD} B`,
    run: (editor) => editor.chain().focus().toggleBold().run(),
    active: (editor) => editor.isActive('bold'),
  },
  {
    key: 'italic',
    icon: 'lucide-italic',
    label: 'Italic',
    hint: `${MOD} I`,
    run: (editor) => editor.chain().focus().toggleItalic().run(),
    active: (editor) => editor.isActive('italic'),
  },
  {
    key: 'underline',
    icon: 'lucide-underline',
    label: 'Underline',
    hint: `${MOD} U`,
    needs: 'toggleUnderline',
    run: (editor) => editor.chain().focus().toggleUnderline().run(),
    active: (editor) => editor.isActive('underline'),
  },
  {
    key: 'strike',
    icon: 'lucide-strikethrough',
    label: 'Strikethrough',
    run: (editor) => editor.chain().focus().toggleStrike().run(),
    active: (editor) => editor.isActive('strike'),
  },
  {
    key: 'code',
    icon: 'lucide-code',
    label: 'Inline code',
    run: (editor) => editor.chain().focus().toggleCode().run(),
    active: (editor) => editor.isActive('code'),
  },
  {
    key: 'highlight',
    icon: 'lucide-highlighter',
    label: 'Highlight',
    needs: 'toggleHighlight',
    run: (editor) => editor.chain().focus().toggleHighlight().run(),
    active: (editor) => editor.isActive('highlight'),
  },
  {
    key: 'link',
    icon: 'lucide-link',
    label: 'Link',
    hint: `${MOD} K`,
    needs: 'setLink',
    run: (editor) => {
      const href = window.prompt('Link to')
      if (!href) return

      editor.chain().focus().setLink({ href }).run()
    },
    active: (editor) => editor.isActive('link'),
  },
  {
    key: 'clear',
    icon: 'lucide-remove-formatting',
    label: 'Clear formatting',
    run: (editor) => editor.chain().focus().unsetAllMarks().run(),
  },
]

const TURN_INTO = [
  {
    key: 'paragraph',
    icon: 'lucide-type',
    label: 'Text',
    run: (editor) => editor.chain().focus().setParagraph().run(),
    active: (editor) => editor.isActive('paragraph'),
  },
  heading(2),
  heading(3),
  heading(4),
  {
    key: 'bullet',
    icon: 'lucide-list',
    label: 'Bulleted list',
    run: (editor) => editor.chain().focus().toggleBulletList().run(),
    active: (editor) => editor.isActive('bulletList'),
  },
  {
    key: 'ordered',
    icon: 'lucide-list-ordered',
    label: 'Numbered list',
    run: (editor) => editor.chain().focus().toggleOrderedList().run(),
    active: (editor) => editor.isActive('orderedList'),
  },
  {
    key: 'task',
    icon: 'lucide-list-todo',
    label: 'Checklist',
    needs: 'toggleTaskList',
    run: (editor) => editor.chain().focus().toggleTaskList().run(),
    active: (editor) => editor.isActive('taskList'),
  },
  {
    key: 'quote',
    icon: 'lucide-quote',
    label: 'Quote',
    run: (editor) => editor.chain().focus().toggleBlockquote().run(),
    active: (editor) => editor.isActive('blockquote'),
  },
  {
    key: 'codeblock',
    icon: 'lucide-square-code',
    label: 'Code block',
    run: (editor) => editor.chain().focus().toggleCodeBlock().run(),
    active: (editor) => editor.isActive('codeBlock'),
  },
]

function insertGroup(api) {
  return [
    {
      key: 'step',
      icon: 'lucide-list-checks',
      label: 'Step',
      hint: 'Numbered, with owner and record',
      run: () => api.insertStep(),
    },
    {
      key: 'warning',
      icon: 'lucide-triangle-alert',
      label: 'Warning',
      hint: 'A hazard people must not miss',
      run: () => api.insertCallout('warning'),
    },
    {
      key: 'note',
      icon: 'lucide-info',
      label: 'Note',
      hint: 'Worth knowing, not a hazard',
      run: () => api.insertCallout('note'),
    },
    {
      key: 'record',
      icon: 'lucide-at-sign',
      label: 'Mention a record',
      hint: 'Another procedure, a form, an item',
      run: () => api.pickRecord(),
    },
    {
      key: 'person',
      icon: 'lucide-user',
      label: 'Mention a person',
      run: () => api.pickPerson(),
    },
    {
      key: 'live',
      icon: 'lucide-activity',
      label: 'Live value',
      hint: 'A number or date that stays current',
      run: () => api.insertLive(),
    },
    {
      key: 'check',
      icon: 'lucide-circle-check',
      label: 'Check',
      hint: 'A green tick or red cross from live data',
      run: () => api.insertCheck(),
    },
    {
      key: 'table',
      icon: 'lucide-table',
      label: 'Table',
      needs: 'insertTable',
      run: (editor) =>
        editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
    },
    {
      key: 'image',
      icon: 'lucide-image',
      label: 'Image',
      needs: 'setImage',
      run: (editor) => {
        const src = window.prompt('Image address')
        if (!src) return

        editor.chain().focus().setImage({ src }).run()
      },
    },
    {
      key: 'divider',
      icon: 'lucide-minus',
      label: 'Divider',
      run: (editor) => editor.chain().focus().setHorizontalRule().run(),
    },
    {
      key: 'date',
      icon: 'lucide-calendar',
      label: "Today's date",
      run: (editor) =>
        editor
          .chain()
          .focus()
          .insertContent(
            new Date().toLocaleDateString(undefined, {
              day: '2-digit',
              month: 'short',
              year: 'numeric',
            }),
          )
          .run(),
    },
  ]
}

const TABLE = [
  {
    key: 'row-above',
    icon: 'lucide-between-vertical-start',
    label: 'Row above',
    run: (editor) => editor.chain().focus().addRowBefore().run(),
  },
  {
    key: 'row-below',
    icon: 'lucide-between-vertical-end',
    label: 'Row below',
    run: (editor) => editor.chain().focus().addRowAfter().run(),
  },
  {
    key: 'col-left',
    icon: 'lucide-between-horizontal-start',
    label: 'Column left',
    run: (editor) => editor.chain().focus().addColumnBefore().run(),
  },
  {
    key: 'col-right',
    icon: 'lucide-between-horizontal-end',
    label: 'Column right',
    run: (editor) => editor.chain().focus().addColumnAfter().run(),
  },
  {
    key: 'header-row',
    icon: 'lucide-table-columns-split',
    label: 'Header row',
    run: (editor) => editor.chain().focus().toggleHeaderRow().run(),
  },
  {
    key: 'merge',
    icon: 'lucide-table-cells-merge',
    label: 'Merge cells',
    run: (editor) => editor.chain().focus().mergeCells().run(),
  },
  {
    key: 'split',
    icon: 'lucide-table-cells-split',
    label: 'Split cell',
    run: (editor) => editor.chain().focus().splitCell().run(),
  },
  {
    key: 'del-row',
    icon: 'lucide-rows-3',
    label: 'Delete row',
    run: (editor) => editor.chain().focus().deleteRow().run(),
  },
  {
    key: 'del-col',
    icon: 'lucide-columns-3',
    label: 'Delete column',
    run: (editor) => editor.chain().focus().deleteColumn().run(),
  },
  {
    key: 'del-table',
    icon: 'lucide-trash-2',
    label: 'Delete table',
    run: (editor) => editor.chain().focus().deleteTable().run(),
  },
]

const ALIGN = [
  {
    key: 'align-left',
    icon: 'lucide-align-left',
    label: 'Align left',
    needs: 'setTextAlign',
    run: (editor) => editor.chain().focus().setTextAlign('left').run(),
    active: (editor) => editor.isActive({ textAlign: 'left' }),
  },
  {
    key: 'align-center',
    icon: 'lucide-align-center',
    label: 'Align centre',
    needs: 'setTextAlign',
    run: (editor) => editor.chain().focus().setTextAlign('center').run(),
    active: (editor) => editor.isActive({ textAlign: 'center' }),
  },
  {
    key: 'align-right',
    icon: 'lucide-align-right',
    label: 'Align right',
    needs: 'setTextAlign',
    run: (editor) => editor.chain().focus().setTextAlign('right').run(),
    active: (editor) => editor.isActive({ textAlign: 'right' }),
  },
]

const EDIT = [
  {
    key: 'indent',
    icon: 'lucide-indent',
    label: 'Indent',
    hint: 'Tab',
    needs: 'sinkListItem',
    run: (editor) => editor.chain().focus().sinkListItem('listItem').run(),
  },
  {
    key: 'outdent',
    icon: 'lucide-outdent',
    label: 'Outdent',
    hint: 'Shift Tab',
    needs: 'liftListItem',
    run: (editor) => editor.chain().focus().liftListItem('listItem').run(),
  },
  {
    key: 'clear-block',
    icon: 'lucide-eraser',
    label: 'Reset this block',
    run: (editor) => editor.chain().focus().unsetAllMarks().clearNodes().run(),
  },
  {
    key: 'undo',
    icon: 'lucide-undo-2',
    label: 'Undo',
    hint: `${MOD} Z`,
    run: (editor) => editor.chain().focus().undo().run(),
  },
  {
    key: 'redo',
    icon: 'lucide-redo-2',
    label: 'Redo',
    hint: `${MOD} ⇧ Z`,
    run: (editor) => editor.chain().focus().redo().run(),
  },
]

function translated(items) {
  return items.map((item) => ({
    ...item,
    label: __(item.label),
    hint: item.hint ? __(item.hint) : item.hint,
  }))
}

function usable(items, editor) {
  return items.filter((item) => !item.needs || typeof editor?.commands?.[item.needs] === 'function')
}

export function paletteGroups(context, api, editor) {
  const groups = []

  if (context.kind === CONTEXTS.TABLE) groups.push({ name: 'Table', items: TABLE })
  if (context.kind === CONTEXTS.TEXT) groups.push({ name: 'Format', items: FORMAT })

  groups.push({ name: 'Turn into', items: TURN_INTO })
  groups.push({ name: 'Insert', items: insertGroup(api) })

  if (context.kind !== CONTEXTS.TABLE) groups.push({ name: 'Align', items: ALIGN })

  groups.push({ name: 'Edit', items: EDIT })

  return groups
    .map((group) => ({ name: __(group.name), items: translated(usable(group.items, editor)) }))
    .filter((group) => group.items.length)
}
