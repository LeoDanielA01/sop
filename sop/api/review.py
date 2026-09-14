# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import pretty_date


@frappe.whitelist()
def comments(sop, version=None, status=None):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	filters = {"sop": sop}
	if version:
		filters["version"] = frappe.utils.cint(version)
	if status:
		filters["status"] = status

	rows = frappe.get_all(
		"SOP Review Comment",
		filters=filters,
		fields=["name", "quote", "comment", "status", "version", "owner", "creation"],
		order_by="creation asc",
		limit_page_length=0,
	)

	people = {
		row.name: row
		for row in frappe.get_all(
			"User",
			filters={"name": ("in", list({row.owner for row in rows}) or [""])},
			fields=["name", "full_name", "user_image"],
			limit_page_length=0,
		)
	}

	mine = frappe.session.user

	return [
		{
			"name": row.name,
			"quote": row.quote,
			"comment": row.comment,
			"status": row.status,
			"version": row.version,
			"author": people.get(row.owner, {}).get("full_name") or row.owner,
			"image": people.get(row.owner, {}).get("user_image"),
			"when": pretty_date(row.creation),
			"is_mine": row.owner == mine,
		}
		for row in rows
	]


@frappe.whitelist()
def add_comment(sop, comment, quote=None, version=None):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	comment = (comment or "").strip()
	if not comment:
		frappe.throw(_("Write what has to change."))

	row = frappe.get_doc(
		{
			"doctype": "SOP Review Comment",
			"sop": sop,
			"version": frappe.utils.cint(version) or doc.version,
			"quote": (quote or "").strip()[:500],
			"comment": comment,
			"status": "Open",
		}
	).insert(ignore_permissions=True)

	return {"name": row.name}


@frappe.whitelist()
def resolve_comment(name, status="Resolved"):
	row = frappe.get_doc("SOP Review Comment", name)
	frappe.get_doc("SOP", row.sop).check_permission("read")

	row.status = "Resolved" if status == "Resolved" else "Open"
	row.save(ignore_permissions=True)

	return {"name": row.name, "status": row.status}


@frappe.whitelist()
def delete_comment(name):
	row = frappe.get_doc("SOP Review Comment", name)

	if row.owner != frappe.session.user and not frappe.has_permission("SOP", "write", doc=row.sop):
		frappe.throw(_("You can only delete your own comments."), frappe.PermissionError)

	frappe.delete_doc("SOP Review Comment", name, ignore_permissions=True)

	return {"deleted": name}


def open_count(sop, version=None):
	filters = {"sop": sop, "status": "Open"}
	if version:
		filters["version"] = frappe.utils.cint(version)

	return frappe.db.count("SOP Review Comment", filters)
