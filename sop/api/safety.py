# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe

from sop.api.mentions import card, type_label
from sop.api.settings import record_types


@frappe.whitelist()
def for_sop(sop):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	types = {row.reference_doctype: row for row in record_types() if row.in_safety}
	if not types:
		return {"records": [], "ppe": []}

	mentioned = []
	for row in doc.references:
		pair = (row.reference_doctype, row.reference_name)
		if row.reference_doctype in types and pair not in mentioned:
			mentioned.append(pair)

	records = []
	for doctype, name in mentioned:
		found = card(doctype, name)
		if found.get("missing") or found.get("blocked"):
			continue
		records.append({**found, "type_label": type_label(doctype), "icon": types[doctype].icon})

	return {"records": records, "ppe": required_ppe(mentioned)}


def required_ppe(mentioned):
	if not frappe.db.exists("DocType", "SOP PPE"):
		return []

	sources = {}
	for doctype, name in mentioned:
		if doctype == "SOP PPE":
			sources.setdefault(name, [])
		elif doctype == "SOP Chemical":
			for ppe in frappe.get_all(
				"SOP Chemical PPE",
				filters={"parent": name, "parenttype": "SOP Chemical"},
				pluck="ppe",
				order_by="idx asc",
			):
				sources.setdefault(ppe, []).append(name)

	out = []
	for name, chemicals in sources.items():
		row = frappe.db.get_value(
			"SOP PPE", name, ["name", "lft", "rgt", "standard", "is_consumable"], as_dict=True
		)
		if not row:
			continue

		trail = frappe.get_all(
			"SOP PPE",
			filters={"lft": ("<=", row.lft), "rgt": (">=", row.rgt)},
			pluck="ppe_name",
			order_by="lft asc",
		)
		out.append(
			{
				"name": row.name,
				"path": " › ".join(trail or [row.name]),
				"standard": row.standard,
				"is_consumable": row.is_consumable,
				"for": chemicals,
				"url": frappe.utils.get_url_to_form("SOP PPE", row.name),
			}
		)

	return out
