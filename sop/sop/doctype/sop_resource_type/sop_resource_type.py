# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SOPResourceType(Document):
	def validate(self):
		seen = set()
		for row in self.attributes:
			key = (row.label or "").strip().lower()
			if key in seen:
				frappe.throw(_("Row {0}: {1} is listed twice.").format(row.idx, frappe.bold(row.label)))
			seen.add(key)

			if row.fieldtype == "Select" and not (row.options or "").strip():
				frappe.throw(_("Row {0}: give {1} its choices, one per line.").format(row.idx, frappe.bold(row.label)))

	def on_update(self):
		frappe.cache().delete_keys("sop:mention")
