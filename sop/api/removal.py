# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _

NEVER_PUBLISHED = ("Draft", "In Review")
IN_FORCE = ("Approved", "Effective", "Under Revision")

LINKED = (
	("SOP Acknowledgement", "sop"),
	("SOP Revision", "sop"),
	("SOP Training Assignment", "sop"),
	("SOP Training Requirement", "sop"),
	("SOP Review Comment", "sop"),
)


def is_manager():
	return "SOP Manager" in frappe.get_roles()


def was_in_force(name, status=None):
	status = status or frappe.db.get_value("SOP", name, "status")

	return status not in NEVER_PUBLISHED or bool(frappe.db.exists("SOP Revision", {"sop": name}))


def removal_actions(doc):
	fresh = not was_in_force(doc.name, doc.status)

	return {
		"delete": fresh and (is_manager() or doc.owner == frappe.session.user),
		"purge": is_manager() and doc.status == "Retired",
	}


def wipe_procedure(name):
	assignments = frappe.get_all(
		"SOP Training Assignment", filters={"sop": name}, pluck="name", limit_page_length=0
	)

	for doctype, field in LINKED:
		for row in frappe.get_all(doctype, filters={field: name}, pluck="name", limit_page_length=0):
			frappe.delete_doc(doctype, row, force=True, ignore_permissions=True)

	frappe.db.delete("SOP Session Procedure", {"sop": name, "parenttype": "SOP Training Session"})
	frappe.db.delete("SOP Reference", {"reference_doctype": "SOP", "reference_name": name})
	frappe.db.delete(
		"Notification Log",
		{
			"document_type": ("in", ["SOP", "SOP Training Assignment"]),
			"document_name": ("in", [name, *assignments]),
		},
	)

	frappe.flags.sop_removal = True

	try:
		frappe.delete_doc("SOP", name, force=True, ignore_permissions=True)
	finally:
		frappe.flags.sop_removal = False


@frappe.whitelist()
def delete_draft(sop):
	doc = frappe.get_doc("SOP", sop)

	if not removal_actions(doc)["delete"]:
		frappe.throw(
			_("Only a draft that was never in force can be deleted, by its author or an SOP manager. Retire it instead."),
			frappe.PermissionError,
		)

	wipe_procedure(doc.name)

	return {"deleted": doc.name}


@frappe.whitelist()
def purge_procedure(sop, confirm=None):
	doc = frappe.get_doc("SOP", sop)

	if not removal_actions(doc)["purge"]:
		frappe.throw(
			_("Only an SOP manager can delete a procedure permanently, and only once it is retired."),
			frappe.PermissionError,
		)

	if (confirm or "").strip() != doc.sop_no:
		frappe.throw(_("Type {0} to confirm.").format(frappe.bold(doc.sop_no)))

	wipe_procedure(doc.name)

	return {"deleted": doc.name}


@frappe.whitelist()
def space_removal(space):
	record = frappe.get_doc("SOP Space", space)
	record.check_permission("read")

	rows = frappe.get_all(
		"SOP", filters={"space": space}, fields=["name", "status"], limit_page_length=0
	)

	in_force = [row.name for row in rows if row.status in IN_FORCE]
	history = [
		row.name for row in rows if row.name not in in_force and was_in_force(row.name, row.status)
	]
	drafts = len(rows) - len(in_force) - len(history)

	return {
		"name": record.name,
		"title": record.title,
		"code": record.space_code,
		"in_force": len(in_force),
		"history": len(history),
		"drafts": drafts,
		"processes": frappe.db.count("SOP Process", {"space": space}),
		"rules": frappe.db.count("SOP Training Requirement", {"space": space}),
		"can_delete": is_manager() and not in_force,
		"needs_confirm": bool(history),
	}


@frappe.whitelist()
def delete_space(space, confirm=None):
	from sop.demo import deepest_first

	if not is_manager():
		frappe.throw(_("Only an SOP manager can delete a space."), frappe.PermissionError)

	summary = space_removal(space)

	if summary["in_force"]:
		frappe.throw(
			_("{0} procedures in {1} are still in force. Retire them first.").format(
				summary["in_force"], frappe.bold(summary["title"])
			)
		)

	if summary["needs_confirm"] and (confirm or "").strip() != summary["code"]:
		frappe.throw(_("Type {0} to confirm.").format(frappe.bold(summary["code"])))

	for name in frappe.get_all("SOP", filters={"space": space}, pluck="name", limit_page_length=0):
		wipe_procedure(name)

	for name in frappe.get_all(
		"SOP Training Requirement", filters={"space": space}, pluck="name", limit_page_length=0
	):
		frappe.delete_doc("SOP Training Requirement", name, force=True, ignore_permissions=True)

	for name in deepest_first([space]):
		frappe.delete_doc("SOP Process", name, force=True, ignore_permissions=True)

	frappe.flags.sop_removal = True

	try:
		frappe.delete_doc("SOP Space", space, force=True, ignore_permissions=True)
	finally:
		frappe.flags.sop_removal = False

	return {"deleted": space}
