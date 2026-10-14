# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe

from sop.api.mentions import most_mentioned, type_label
from sop.api.settings import record_types


@frappe.whitelist()
def types():
	configured = {row.reference_doctype: row for row in record_types()}
	counts = most_mentioned()
	doctypes = list(configured) + sorted(
		(doctype for doctype in counts if doctype not in configured), key=lambda doctype: -counts[doctype]
	)

	return [
		{
			"value": doctype,
			"label": type_label(doctype),
			"icon": configured[doctype].icon if doctype in configured else None,
			"count": counts.get(doctype, 0),
		}
		for doctype in doctypes
		if frappe.db.exists("DocType", doctype) and frappe.has_permission(doctype, "read")
	]


@frappe.whitelist()
def find(doctype, name):
	references = frappe.get_all(
		"SOP Reference",
		filters={"parenttype": "SOP", "reference_doctype": doctype, "reference_name": name},
		fields=["parent", "mention_kind", "context_snippet"],
		limit_page_length=0,
	)
	if not references:
		return []

	snippets = {}
	for row in references:
		snippets.setdefault(row.parent, row.context_snippet)

	rows = frappe.get_list(
		"SOP",
		filters={"name": ("in", list(snippets))},
		fields=["name", "sop_no", "title", "status", "version", "space", "process_owner", "modified"],
		order_by="sop_no asc",
		limit_page_length=0,
	)
	for row in rows:
		row.snippet = snippets.get(row.name)

	return rows
