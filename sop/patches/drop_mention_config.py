import frappe


def execute():
	for doctype in ("SOP Mention Config", "SOP Mention Badge"):
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, ignore_missing=True, force=True)

	for table in ("tabSOP Mention Config", "tabSOP Mention Badge"):
		frappe.db.sql_ddl(f"drop table if exists `{table}`")
