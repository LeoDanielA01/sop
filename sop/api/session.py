# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def me():
	user = frappe.get_cached_doc("User", frappe.session.user)
	roles = frappe.get_roles()

	return {
		"name": user.name,
		"full_name": user.full_name,
		"image": user.user_image,
		"is_manager": "SOP Manager" in roles,
		"is_author": bool({"SOP Author", "SOP Manager"} & set(roles)),
		"csrf_token": frappe.sessions.get_csrf_token(),
	}

@frappe.whitelist()
def stats():
	user = frappe.session.user

	from sop.api.procedures import attention

	return {
		"waiting": attention(user),
		"owned": frappe.db.count("SOP", {"process_owner": user}),
		"drafts": frappe.db.count("SOP", {"owner": user, "status": "Draft"}),
		"signed": frappe.db.count("SOP Acknowledgement", {"user": user}),
		"training_open": frappe.db.count(
			"SOP Training Assignment",
			{"trainee": user, "status": ("in", ("Assigned", "In Progress", "Overdue"))},
		),
		"training_overdue": frappe.db.count(
			"SOP Training Assignment", {"trainee": user, "status": "Overdue"}
		),
	}
