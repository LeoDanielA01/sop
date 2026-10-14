import frappe

from sop import demo
from sop.integrations import erpnext
from sop.patches.seed_safety_record_types import execute as seed_record_types

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
	erpnext.setup()
	seed_record_types()
	create_default_space()
	seed_demo()


def after_migrate():
	create_roles()
	erpnext.setup()
	seed_demo()


def seed_demo():
	frappe.db.savepoint("sop_demo")

	try:
		demo.after_migrate()
	except Exception as error:
		frappe.db.rollback(save_point="sop_demo")
		frappe.log_error(title="SOP demo data could not be created", message=frappe.get_traceback())
		print(f"SOP demo data: failed — {error}. Details in Error Log, or run sop.demo.status.")


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
