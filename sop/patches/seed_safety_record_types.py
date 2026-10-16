import frappe

from sop.patches.migrate_to_resources import RECORD_TYPE


def execute():
	"""New sites start with the generic Resource record type; each business adds its own resource types."""
	doc = frappe.get_doc("SOP Settings")
	if any(row.reference_doctype == RECORD_TYPE["reference_doctype"] for row in doc.record_types):
		return

	doc.append("record_types", RECORD_TYPE)
	doc.save(ignore_permissions=True)
