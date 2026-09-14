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

export const CONTEXTS = {
  TEXT: 'text',
  EMPTY: 'empty',
  TABLE: 'table',
  IMAGE: 'image',
}

const CodeBlockItem = {
  icon: 'lucide-square-code',
  label: 'Code block',
  action: (editor) => editor.chain().focus().toggleCodeBlock().run(),
  isActive: (editor) => editor.isActive('codeBlock'),
}

const ChecklistItem = {
  icon: 'lucide-list-todo',
  label: 'Checklist',
  action: (editor) => editor.chain().focus().toggleTaskList().run(),
  isActive: (editor) => editor.isActive('taskList'),
}

const ClearFormatItem = {
  icon: 'lucide-remove-formatting',
  label: 'Clear formatting',
  action: (editor) => editor.chain().focus().unsetAllMarks().clearNodes().run(),
}

const TABLE_ITEMS = [
  {
    icon: 'lucide-between-vertical-start',
    label: 'Row above',
    action: (editor) => editor.chain().focus().addRowBefore().run(),
  },
  {
    icon: 'lucide-between-vertical-end',
    label: 'Row below',
    action: (editor) => editor.chain().focus().addRowAfter().run(),
  },
  {
    icon: 'lucide-between-horizontal-start',
    label: 'Column left',
    action: (editor) => editor.chain().focus().addColumnBefore().run(),
  },
  {
    icon: 'lucide-between-horizontal-end',
    label: 'Column right',
    action: (editor) => editor.chain().focus().addColumnAfter().run(),
  },
  Separator,
  {
    icon: 'lucide-table-columns-split',
    label: 'Header row',
    action: (editor) => editor.chain().focus().toggleHeaderRow().run(),
  },
  {
    icon: 'lucide-table-cells-merge',
    label: 'Merge cells',
    action: (editor) => editor.chain().focus().mergeCells().run(),
  },
  {
    icon: 'lucide-table-cells-split',
    label: 'Split cell',
    action: (editor) => editor.chain().focus().splitCell().run(),
  },
  Separator,
  {
    icon: 'lucide-rows-3',
    label: 'Delete row',
    action: (editor) => editor.chain().focus().deleteRow().run(),
  },
  {
    icon: 'lucide-columns-3',
    label: 'Delete column',
    action: (editor) => editor.chain().focus().deleteColumn().run(),
  },
  {
    icon: 'lucide-trash-2',
    label: 'Delete table',
    action: (editor) => editor.chain().focus().deleteTable().run(),
  },
]

function procedureItems(api) {
  return {
    step: {
      icon: 'lucide-list-checks',
      label: 'Step',
      action: () => api.insertStep(),
    },
    warning: {
      icon: 'lucide-triangle-alert',
      label: 'Warning',
      action: () => api.insertCallout('warning'),
    },
    note: {
      icon: 'lucide-info',
      label: 'Note',
      action: () => api.insertCallout('note'),
    },
    record: {
      icon: 'lucide-at-sign',
      label: 'Mention a record',
      action: () => api.pickRecord(),
    },
    person: {
      icon: 'lucide-user',
      label: 'Mention a person',
      action: () => api.pickPerson(),
    },
  }
}

function procedureGroup(api) {
  const items = procedureItems(api)

  return [items.step, items.warning, items.note, Separator, items.record, items.person]
}

const FORMAT_ITEMS = [
  Bold,
  Italic,
  Strike,
  InlineCode,
  FontColor,
  Separator,
  InsertLink,
  ClearFormatItem,
]

const STRUCTURE_ITEMS = [
  HeadingGroup,
  Separator,
  BulletList,
  OrderedList,
  ChecklistItem,
  Separator,
  Blockquote,
  CodeBlockItem,
  HorizontalRule,
  Separator,
  InsertTable,
  InsertImage,
]

const LAYOUT_ITEMS = [AlignLeft, AlignCenter, AlignRight]

const HISTORY_ITEMS = [Undo, Redo]

export function fixedItems(api) {
  const sop = procedureItems(api)

  return [
    HeadingGroup,
    Separator,
    Bold,
    Italic,
    Strike,
    InsertLink,
    Separator,
    BulletList,
    OrderedList,
    ChecklistItem,
    Separator,
    Blockquote,
    InsertTable,
    InsertImage,
    Separator,
    sop.step,
    sop.warning,
    sop.record,
    sop.person,
    Separator,
    Undo,
    Redo,
  ]
}

export const BUBBLE_ITEMS = [
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
  CodeBlockItem,
]

export function contextAt(editor) {
  if (!editor) return { kind: CONTEXTS.EMPTY }

  if (editor.isActive('table')) return { kind: CONTEXTS.TABLE }
  if (editor.isActive('image')) return { kind: CONTEXTS.IMAGE }
  if (editor.state.selection.empty) return { kind: CONTEXTS.EMPTY }
  return { kind: CONTEXTS.TEXT }
}

export function paletteGroups(context, api) {
  const groups = []

  if (context.kind === CONTEXTS.TABLE) {
    groups.push({ name: 'Table', items: TABLE_ITEMS })
  }

  if (context.kind === CONTEXTS.IMAGE) {
    groups.push({ name: 'Image', items: LAYOUT_ITEMS })
  }

  if (context.kind === CONTEXTS.TEXT) {
    groups.push({ name: 'Format', items: FORMAT_ITEMS })
  }

  groups.push({ name: 'Insert', items: STRUCTURE_ITEMS })
  groups.push({ name: 'Procedure', items: procedureGroup(api) })

  if (context.kind === CONTEXTS.EMPTY) {
    groups.push({ name: 'Edit', items: [...HISTORY_ITEMS, ClearFormatItem] })
  }

  return groups
}
