# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint, pretty_date


def can_see_notes(doc):
	return (
		"SOP Manager" in frappe.get_roles()
		or doc.process_owner == frappe.session.user
		or doc.has_permission("write")
	)


@frappe.whitelist()
def vote(sop, clear, note=None):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	version = cint(doc.version)
	clear = cint(clear)
	note = "" if clear else (note or "").strip()[:500]

	existing = frappe.db.get_value(
		"SOP Clarity Vote", {"sop": sop, "version": version, "user": frappe.session.user}, "name"
	)

	if existing:
		frappe.db.set_value("SOP Clarity Vote", existing, {"clear": clear, "note": note})
	else:
		frappe.get_doc(
			{
				"doctype": "SOP Clarity Vote",
				"sop": sop,
				"version": version,
				"user": frappe.session.user,
				"clear": clear,
				"note": note,
			}
		).insert(ignore_permissions=True)

	return summary(sop)


@frappe.whitelist()
def summary(sop):
	from sop.api.procedures import user_names

	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	version = cint(doc.version)
	rows = frappe.get_all(
		"SOP Clarity Vote",
		filters={"sop": sop, "version": version},
		fields=["user", "clear", "note", "modified"],
		order_by="modified desc",
		limit_page_length=0,
	)

	mine = next((row for row in rows if row.user == frappe.session.user), None)
	result = {
		"version": version,
		"mine": {"clear": cint(mine.clear), "note": mine.note} if mine else None,
		"can_see_notes": False,
	}

	if not can_see_notes(doc):
		return result

	total = len(rows)
	clear_count = len([row for row in rows if cint(row.clear)])
	unclear = [row for row in rows if not cint(row.clear) and row.note]
	names = user_names({row.user for row in unclear})

	result.update(
		{
			"can_see_notes": True,
			"total": total,
			"clear": clear_count,
			"percent": round(clear_count * 100 / total) if total else None,
			"notes": [
				{
					"note": row.note,
					"who": names.get(row.user, {}).get("full_name") or row.user,
					"when": pretty_date(row.modified),
				}
				for row in unclear[:20]
			],
		}
	)

	return result
