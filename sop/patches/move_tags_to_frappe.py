# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe


def execute():
	if not frappe.db.table_exists("SOP Tag"):
		return

	rows = frappe.db.sql(
		"""
		select parent, tag
		from `tabSOP Tag`
		where parenttype = 'SOP' and ifnull(tag, '') != ''
		""",
		as_dict=True,
	)

	if not rows:
		return

	from frappe.desk.doctype.tag.tag import add_tag

	for row in rows:
		if not frappe.db.exists("SOP", row.parent):
			continue

		try:
			add_tag(row.tag, "SOP", row.parent)
		except Exception:
			frappe.log_error(title=f"Could not carry tag {row.tag} to {row.parent}")

	frappe.db.commit()
