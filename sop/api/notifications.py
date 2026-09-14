# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import pretty_date

DOCTYPES = ("SOP", "SOP Training Assignment")


@frappe.whitelist()
def feed(limit=20, unread_only=0):
	filters = {"for_user": frappe.session.user, "document_type": ("in", DOCTYPES)}
	if frappe.utils.cint(unread_only):
		filters["read"] = 0

	rows = frappe.get_all(
		"Notification Log",
		filters=filters,
		fields=["name", "subject", "document_type", "document_name", "read", "creation"],
		order_by="creation desc",
		limit_page_length=frappe.utils.cint(limit) or 20,
	)

	return [
		{
			"name": row.name,
			"subject": frappe.utils.strip_html(row.subject or ""),
			"read": row.read,
			"when": pretty_date(row.creation),
			"route": route_for(row),
		}
		for row in rows
	]


def route_for(row):
	if row.document_type == "SOP Training Assignment":
		return "/training"

	return f"/{row.document_name}"


@frappe.whitelist()
def unread():
	return frappe.db.count(
		"Notification Log",
		{"for_user": frappe.session.user, "read": 0, "document_type": ("in", DOCTYPES)},
	)


@frappe.whitelist()
def mark_read(name=None):
	filters = {"for_user": frappe.session.user, "read": 0}
	if name:
		filters["name"] = name

	names = frappe.get_all("Notification Log", filters=filters, pluck="name", limit_page_length=0)

	for row in names:
		frappe.db.set_value("Notification Log", row, "read", 1, update_modified=False)

	return {"read": len(names)}
