import frappe


def execute():
	frappe.db.delete("Custom Field", {"dt": "SOP", "fieldname": "steps"})

	if frappe.db.exists("DocType", "SOP Step"):
		frappe.delete_doc("DocType", "SOP Step", ignore_missing=True, force=True)

	frappe.db.sql_ddl("drop table if exists `tabSOP Step`")
