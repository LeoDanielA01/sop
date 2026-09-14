# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import pretty_date

KINDS = {"SOP": "procedure", "SOP Training Assignment": "training"}


@frappe.whitelist()
def feed(kind=None, limit=30, unread_only=0):
	filters = {"for_user": frappe.session.user, "document_type": ("in", list(KINDS))}

	if kind:
		wanted = [doctype for doctype, name in KINDS.items() if name == kind]
		filters["document_type"] = ("in", wanted or [""])

	if frappe.utils.cint(unread_only):
		filters["read"] = 0

	rows = frappe.get_all(
		"Notification Log",
		filters=filters,
		fields=[
			"name",
			"subject",
			"document_type",
			"document_name",
			"from_user",
			"read",
			"creation",
		],
		order_by="creation desc",
		limit_page_length=frappe.utils.cint(limit) or 30,
	)
	if not rows:
		return []

	procedures = details([row.document_name for row in rows if row.document_type == "SOP"])
	assignments = training_details(
		[row.document_name for row in rows if row.document_type == "SOP Training Assignment"]
	)
	actors = people([row.from_user for row in rows])

	out = []
	for row in rows:
		about = (
			procedures.get(row.document_name)
			if row.document_type == "SOP"
			else assignments.get(row.document_name)
		) or {}

		out.append(
			{
				"name": row.name,
				"subject": frappe.utils.strip_html(row.subject or ""),
				"kind": KINDS.get(row.document_type, "procedure"),
				"read": row.read,
				"creation": row.creation,
				"when": pretty_date(row.creation),
				"actor": actors.get(row.from_user, {}).get("full_name"),
				"actor_image": actors.get(row.from_user, {}).get("user_image"),
				"sop_no": about.get("sop_no"),
				"title": about.get("title"),
				"status": about.get("status"),
				"due_on": about.get("due_on"),
				"route": route_for(row, about),
			}
		)

	return out


def details(names):
	names = [name for name in names if name]
	if not names:
		return {}

	rows = frappe.get_all(
		"SOP",
		filters={"name": ("in", names)},
		fields=["name", "sop_no", "title", "status"],
		limit_page_length=0,
	)
	return {row.name: row for row in rows}


def training_details(names):
	names = [name for name in names if name]
	if not names:
		return {}

	rows = frappe.get_all(
		"SOP Training Assignment",
		filters={"name": ("in", names)},
		fields=["name", "sop", "status", "due_on"],
		limit_page_length=0,
	)

	procedures = details([row.sop for row in rows])

	return {
		row.name: frappe._dict(
			sop_no=procedures.get(row.sop, {}).get("sop_no"),
			title=procedures.get(row.sop, {}).get("title"),
			status=row.status,
			due_on=row.due_on,
		)
		for row in rows
	}


def people(users):
	users = [user for user in users if user]
	if not users:
		return {}

	rows = frappe.get_all(
		"User",
		filters={"name": ("in", list(set(users)))},
		fields=["name", "full_name", "user_image"],
		limit_page_length=0,
	)
	return {row.name: row for row in rows}


def route_for(row, about):
	if row.document_type == "SOP Training Assignment":
		return "/training"

	return f"/{row.document_name}"


@frappe.whitelist()
def unread():
	rows = frappe.get_all(
		"Notification Log",
		filters={"for_user": frappe.session.user, "read": 0, "document_type": ("in", list(KINDS))},
		pluck="document_type",
		limit_page_length=0,
	)

	counts = {"total": len(rows), "procedure": 0, "training": 0}
	for doctype in rows:
		counts[KINDS.get(doctype, "procedure")] += 1

	return counts


@frappe.whitelist()
def mark_read(name=None, kind=None):
	filters = {"for_user": frappe.session.user, "read": 0, "document_type": ("in", list(KINDS))}

	if name:
		filters["name"] = name
	elif kind:
		wanted = [doctype for doctype, value in KINDS.items() if value == kind]
		filters["document_type"] = ("in", wanted or [""])

	names = frappe.get_all("Notification Log", filters=filters, pluck="name", limit_page_length=0)

	for row in names:
		frappe.db.set_value("Notification Log", row, "read", 1, update_modified=False)

	return {"read": len(names)}
