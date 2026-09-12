import frappe

ROLES = [
	("SOP Reader", "Reads effective procedures and acknowledges them."),
	("SOP Author", "Writes and edits drafts."),
	("SOP Reviewer", "Comments on drafts under review."),
	("SOP Approver", "Signs off revisions."),
	("SOP Trainer", "Runs training sessions and records outcomes."),
	("SOP Manager", "Owns spaces, teams, mention configuration and retirement."),
]


def after_install():
	create_roles()
	create_default_space()


def after_migrate():
	create_roles()


def create_roles():
	for name, _description in ROLES:
		if frappe.db.exists("Role", name):
			continue

		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": name,
				"desk_access": 1,
				"is_custom": 1,
				"search_bar": 1,
				"notifications": 1,
			}
		).insert(ignore_permissions=True)


def create_default_space():
	if frappe.db.exists("SOP Space", {"space_code": "GEN"}):
		return

	frappe.get_doc(
		{
			"doctype": "SOP Space",
			"title": "General",
			"space_code": "GEN",
			"visibility": "Public",
			"review_interval_months": 12,
			"description": "Procedures that do not belong to a department binder yet.",
		}
	).insert(ignore_permissions=True)
