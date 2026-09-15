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
		fields=[
			"name",
			"parent_comment",
			"quote",
			"quote_before",
			"quote_after",
			"comment",
			"status",
			"version",
			"owner",
			"creation",
		],
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

	def shape(row):
		return {
			"name": row.name,
			"parent": row.parent_comment,
			"quote": row.quote,
			"quote_before": row.quote_before,
			"quote_after": row.quote_after,
			"comment": row.comment,
			"status": row.status,
			"version": row.version,
			"author": people.get(row.owner, {}).get("full_name") or row.owner,
			"image": people.get(row.owner, {}).get("user_image"),
			"when": pretty_date(row.creation),
			"is_mine": row.owner == mine,
		}

	threads = []
	by_name = {}

	for row in rows:
		item = shape(row)
		item["replies"] = []

		if row.parent_comment and row.parent_comment in by_name:
			by_name[row.parent_comment]["replies"].append(item)
		else:
			threads.append(item)

		by_name[row.name] = item

	return threads


def review_rights(doc):
	user = frappe.session.user
	manager = "SOP Manager" in frappe.get_roles()
	reviewer = any(row.approver == user for row in doc.approvals)
	author = user in (doc.owner, doc.process_owner)
	in_review = doc.status == "In Review"
	changing = doc.status in ("Draft", "Under Revision") and bool(doc.approvals)

	return {
		"visible": in_review or changing,
		"comment": in_review and (reviewer or manager),
		"respond": (in_review or changing) and (reviewer or manager or author),
	}


@frappe.whitelist()
def add_comment(sop, comment, quote=None, version=None, parent=None, before=None, after=None):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	comment = (comment or "").strip()
	if not comment:
		frappe.throw(_("Write what has to change."))

	rights = review_rights(doc)

	if parent and not rights["respond"]:
		frappe.throw(
			_("Replies on {0} are open only during its review.").format(doc.sop_no), frappe.PermissionError
		)

	if not parent and not rights["comment"]:
		frappe.throw(
			_("Only the reviewers of {0} can comment, and only while it is in review.").format(doc.sop_no),
			frappe.PermissionError,
		)

	row = frappe.get_doc(
		{
			"doctype": "SOP Review Comment",
			"sop": sop,
			"parent_comment": parent,
			"version": frappe.utils.cint(version) or doc.version,
			"quote": (quote or "").strip()[:500],
			"quote_before": (before or "")[-140:],
			"quote_after": (after or "")[:140],
			"comment": comment,
			"status": "Open",
		}
	).insert(ignore_permissions=True)

	return {"name": row.name}


@frappe.whitelist()
def resolve_comment(name, status="Resolved"):
	row = frappe.get_doc("SOP Review Comment", name)
	doc = frappe.get_doc("SOP", row.sop)
	doc.check_permission("read")

	if not review_rights(doc)["respond"]:
		frappe.throw(
			_("Comments on {0} can only be resolved during its review.").format(doc.sop_no),
			frappe.PermissionError,
		)

	row.status = "Resolved" if status == "Resolved" else "Open"
	row.save(ignore_permissions=True)

	for reply in frappe.get_all(
		"SOP Review Comment", filters={"parent_comment": name}, pluck="name", limit_page_length=0
	):
		frappe.db.set_value("SOP Review Comment", reply, "status", row.status)

	return {"name": row.name, "status": row.status}


@frappe.whitelist()
def delete_comment(name):
	row = frappe.get_doc("SOP Review Comment", name)

	if row.owner != frappe.session.user and not frappe.has_permission("SOP", "write", doc=row.sop):
		frappe.throw(_("You can only delete your own comments."), frappe.PermissionError)

	if not review_rights(frappe.get_doc("SOP", row.sop))["respond"]:
		frappe.throw(_("Comments can only be deleted during the review."), frappe.PermissionError)

	frappe.delete_doc("SOP Review Comment", name, ignore_permissions=True)

	return {"deleted": name}


def open_count(sop, version=None):
	filters = {"sop": sop, "status": "Open"}
	if version:
		filters["version"] = frappe.utils.cint(version)

	return frappe.db.count("SOP Review Comment", filters)
