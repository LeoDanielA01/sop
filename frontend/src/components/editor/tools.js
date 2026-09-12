/**
 * What the palette can do, and when each tool is worth offering.
 *
 * `when` decides whether a tool appears for the thing under the pointer, so a
 * right-click inside a table offers table tools and a right-click on an empty
 * line offers the blocks you would actually insert there. A palette that always
 * shows everything is just a toolbar in a worse position.
 */

export const CONTEXTS = {
  TEXT: 'text',
  EMPTY: 'empty',
  TABLE: 'table',
  IMAGE: 'image',
  MENTION: 'mention',
}

const always = () => true
const hasSelection = (ctx) => ctx.kind === CONTEXTS.TEXT
const isEmptyLine = (ctx) => ctx.kind === CONTEXTS.EMPTY
const inTable = (ctx) => ctx.kind === CONTEXTS.TABLE

export const GROUPS = [
  {
    name: 'Format',
    when: hasSelection,
    tools: [
      {
        label: 'Bold',
        icon: 'lucide-bold',
        run: (e) => e.chain().focus().toggleBold().run(),
        active: (e) => e.isActive('bold'),
      },
      {
        label: 'Italic',
        icon: 'lucide-italic',
        run: (e) => e.chain().focus().toggleItalic().run(),
        active: (e) => e.isActive('italic'),
      },
      {
        label: 'Underline',
        icon: 'lucide-underline',
        run: (e) => e.chain().focus().toggleUnderline().run(),
        active: (e) => e.isActive('underline'),
      },
      {
        label: 'Code',
        icon: 'lucide-code',
        run: (e) => e.chain().focus().toggleCode().run(),
        active: (e) => e.isActive('code'),
      },
      {
        label: 'Link',
        icon: 'lucide-link',
        run: (e, api) => api.promptLink(),
      },
    ],
  },
  {
    name: 'Structure',
    when: always,
    tools: [
      {
        label: 'Heading',
        icon: 'lucide-heading-2',
        run: (e) => e.chain().focus().toggleHeading({ level: 2 }).run(),
        active: (e) => e.isActive('heading', { level: 2 }),
      },
      {
        label: 'Bullets',
        icon: 'lucide-list',
        run: (e) => e.chain().focus().toggleBulletList().run(),
        active: (e) => e.isActive('bulletList'),
      },
      {
        label: 'Numbered',
        icon: 'lucide-list-ordered',
        run: (e) => e.chain().focus().toggleOrderedList().run(),
        active: (e) => e.isActive('orderedList'),
      },
      {
        label: 'Table',
        icon: 'lucide-table',
        run: (e) => e.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run(),
      },
      {
        label: 'Divider',
        icon: 'lucide-minus',
        run: (e) => e.chain().focus().setHorizontalRule().run(),
      },
    ],
  },
  {
    // The reason this editor exists rather than a generic one.
    name: 'Procedure',
    when: always,
    tools: [
      {
        label: 'Step',
        icon: 'lucide-list-checks',
        hint: 'A numbered step with an owner and the record it produces',
        run: (e, api) => api.insertStep(),
      },
      {
        label: 'Warning',
        icon: 'lucide-triangle-alert',
        hint: 'A hazard callout that prints in red on the controlled copy',
        run: (e, api) => api.insertCallout('warning'),
      },
      {
        label: 'Record',
        icon: 'lucide-at-sign',
        hint: 'Mention an item, asset or document — shows its live state to the reader',
        run: (e, api) => api.pickRecord(),
      },
      {
        label: 'Person',
        icon: 'lucide-user',
        hint: 'Mention a person by role, not by name in prose',
        run: (e, api) => api.pickPerson(),
      },
      {
        label: 'Shared block',
        icon: 'lucide-blocks',
        hint: 'Insert content maintained once and used in many procedures',
        run: (e, api) => api.pickBlock(),
      },
    ],
  },
  {
    name: 'Table',
    when: inTable,
    tools: [
      {
        label: 'Row above',
        icon: 'lucide-between-vertical-start',
        run: (e) => e.chain().focus().addRowBefore().run(),
      },
      {
        label: 'Row below',
        icon: 'lucide-between-vertical-end',
        run: (e) => e.chain().focus().addRowAfter().run(),
      },
      {
        label: 'Column left',
        icon: 'lucide-between-horizontal-start',
        run: (e) => e.chain().focus().addColumnBefore().run(),
      },
      {
        label: 'Column right',
        icon: 'lucide-between-horizontal-end',
        run: (e) => e.chain().focus().addColumnAfter().run(),
      },
      {
        label: 'Delete row',
        icon: 'lucide-trash-2',
        run: (e) => e.chain().focus().deleteRow().run(),
      },
    ],
  },
  {
    name: 'Edit',
    when: isEmptyLine,
    tools: [
      { label: 'Undo', icon: 'lucide-undo-2', run: (e) => e.chain().focus().undo().run() },
      { label: 'Redo', icon: 'lucide-redo-2', run: (e) => e.chain().focus().redo().run() },
      {
        label: 'Paste as plain text',
        icon: 'lucide-clipboard',
        hint: 'Strips the formatting Word brings with it',
        run: (e, api) => api.pastePlain(),
      },
    ],
  },
]

/** What is under the pointer decides which groups are offered. */
export function contextAt(editor) {
  if (!editor) return { kind: CONTEXTS.EMPTY }

  if (editor.isActive('table')) return { kind: CONTEXTS.TABLE }
  if (editor.isActive('image')) return { kind: CONTEXTS.IMAGE }
  if (editor.state.selection.empty) return { kind: CONTEXTS.EMPTY }
  return { kind: CONTEXTS.TEXT }
}

export function groupsFor(context) {
  return GROUPS.filter((group) => group.when(context) && group.tools.length)
}
