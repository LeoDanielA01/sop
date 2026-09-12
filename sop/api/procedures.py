# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, nowdate

from sop.api.mentions import resolve


@frappe.whitelist()
def spaces():
	"""Binders the signed-in user may open, with the number that gets people chased."""
	rows = frappe.get_list(
		"SOP Space",
		fields=["name", "title", "space_code", "visibility", "icon"],
		order_by="title asc",
	)

	for row in rows:
		row.total = frappe.db.count("SOP", {"space": row.name})
		row.overdue = frappe.db.count(
			"SOP", {"space": row.name, "status": "Effective", "review_due": ("<", nowdate())}
		)

	return rows


@frappe.whitelist()
def counts(space=None):
	user = frappe.session.user
	scope = {"space": space} if space else {}

	return {
		"approval": pending_approvals(user, space),
		"drafts": frappe.db.count("SOP", dict(scope, status="Draft", owner=user)),
		"unacknowledged": unacknowledged_count(user, space),
		"review": frappe.db.count(
			"SOP", dict(scope, status="Effective", review_due=("<=", add_days(nowdate(), 30)))
		),
	}


def pending_approvals(user, space=None):
	filters = {"parenttype": "SOP", "approver": user, "decision": "Pending"}
	names = frappe.get_all("SOP Approval", filters=filters, pluck="parent")
	if not names:
		return 0

	scope = {"name": ("in", names), "status": "In Review"}
	if space:
		scope["space"] = space
	return frappe.db.count("SOP", scope)


def unacknowledged_count(user, space=None):
	scope = {"status": "Effective"}
	if space:
		scope["space"] = space

	effective = frappe.get_all("SOP", filters=scope, fields=["name", "version"])
	if not effective:
		return 0

	signed = {
		(row.sop, row.version)
		for row in frappe.get_all(
			"SOP Acknowledgement",
			filters={"user": user, "sop": ("in", [row.name for row in effective])},
			fields=["sop", "version"],
		)
	}
	return len([row for row in effective if (row.name, row.version) not in signed])


LIST_FIELDS = [
	"name",
	"sop_no",
	"title",
	"summary",
	"status",
	"version",
	"space",
	"process_owner",
	"effective_from",
	"review_due",
	"modified",
]


@frappe.whitelist()
def list_procedures(space=None, view="all", search=None, start=0, page_length=20):
	"""One page of rows plus the real total, so the pager can say 'page 2 of 9'."""
	filters = view_filters(space, view)

	if search:
		filters["search_text"] = ("like", f"%{search}%")

	total = frappe.db.count("SOP", filters)
	rows = frappe.get_list(
		"SOP",
		filters=filters,
		fields=LIST_FIELDS,
		order_by="modified desc",
		limit_start=frappe.utils.cint(start),
		limit_page_length=frappe.utils.cint(page_length),
	)

	names = user_names({row.process_owner for row in rows if row.process_owner})
	for row in rows:
		row.process_owner_name = names.get(row.process_owner, {}).get("full_name")
		row.owner_image = names.get(row.process_owner, {}).get("user_image")
		row.is_mine = row.process_owner == frappe.session.user

	return {"rows": rows, "total": total, "start": frappe.utils.cint(start)}


def view_filters(space, view):
	"""Every view narrows in SQL, so paging and counting agree with each other."""
	filters = {}
	if space:
		filters["space"] = space

	user = frappe.session.user

	if view == "drafts":
		filters.update({"status": "Draft", "owner": user})
	elif view == "review":
		filters.update({"status": "Effective", "review_due": ("<=", add_days(nowdate(), 30))})
	elif view == "approval":
		names = frappe.get_all(
			"SOP Approval",
			filters={"parenttype": "SOP", "approver": user, "decision": "Pending"},
			pluck="parent",
		)
		filters.update({"name": ("in", names or [""]), "status": "In Review"})
	elif view == "unacknowledged":
		filters["name"] = ("in", unacknowledged_names(user, space) or [""])

	return filters


def unacknowledged_names(user, space=None):
	scope = {"status": "Effective"}
	if space:
		scope["space"] = space

	effective = frappe.get_all("SOP", filters=scope, fields=["name", "version"])
	if not effective:
		return []

	signed = {
		(row.sop, row.version)
		for row in frappe.get_all(
			"SOP Acknowledgement",
			filters={"user": user, "sop": ("in", [row.name for row in effective])},
			fields=["sop", "version"],
		)
	}
	return [row.name for row in effective if (row.name, row.version) not in signed]


@frappe.whitelist()
def get_procedure(name, revision=None):
	doc = frappe.get_doc("SOP", name)
	doc.check_permission("read")

	content, version = served_content(doc, revision)
	owner = user_names([doc.process_owner]).get(doc.process_owner, {})
	signed = last_acknowledgement(doc.name)

	return {
		"name": doc.name,
		"sop_no": doc.sop_no,
		"title": doc.title,
		"summary": doc.summary,
		"status": doc.status,
		"version": version,
		"effective_revision": doc.version,
		"space": doc.space,
		"content": content,
		"steps": [step.as_dict() for step in doc.steps],
		"tags": [row.tag for row in doc.tags],
		"references": resolve(references_of(doc)),
		"process_owner": doc.process_owner,
		"process_owner_name": owner.get("full_name"),
		"owner_image": owner.get("user_image"),
		"effective_from": doc.effective_from,
		"review_due": doc.review_due,
		"revisions": frappe.get_all(
			"SOP Revision",
			filters={"sop": doc.name},
			fields=["version", "effective_from"],
			order_by="version desc",
		),
		"acknowledged": bool(signed and signed.version == doc.version),
		"acknowledged_on": signed.acknowledged_at if signed else None,
		"acknowledged_version": signed.version if signed else None,
		"can_edit": doc.is_editable() and doc.has_permission("write"),
	}


def served_content(doc, revision=None):
	"""Readers get the approved revision. Only editors see the working draft."""
	if revision:
		row = frappe.db.get_value(
			"SOP Revision", {"sop": doc.name, "version": revision}, ["content", "version"], as_dict=True
		)
		if row:
			return row.content, row.version

	if doc.status in ("Effective", "Under Revision") and doc.version:
		row = doc.effective_revision()
		if row:
			return row.content, row.version

	return doc.content, doc.version


def references_of(doc):
	return [
		{"doctype": row.reference_doctype, "name": row.reference_name}
		for row in doc.references
	]


def user_names(users):
	users = [user for user in users if user]
	if not users:
		return {}

	rows = frappe.get_all(
		"User", filters={"name": ("in", users)}, fields=["name", "full_name", "user_image"]
	)
	return {row.name: row for row in rows}


def has_acknowledged(sop, version):
	return bool(
		frappe.db.exists(
			"SOP Acknowledgement", {"sop": sop, "version": version, "user": frappe.session.user}
		)
	)


def last_acknowledgement(sop):
	rows = frappe.get_all(
		"SOP Acknowledgement",
		filters={"sop": sop, "user": frappe.session.user},
		fields=["version", "acknowledged_at"],
		order_by="version desc",
		limit=1,
	)
	return rows[0] if rows else None


@frappe.whitelist()
def save_draft(space, title, name=None, summary=None, content=None):
	"""Create or update a draft. Only states that are meant to be edited accept it."""
	if name:
		doc = frappe.get_doc("SOP", name)
		doc.check_permission("write")

		if not doc.is_editable():
			frappe.throw(
				_("{0} is {1} and cannot be edited. Start a revision instead.").format(
					doc.sop_no, frappe.bold(doc.status)
				)
			)
	else:
		doc = frappe.new_doc("SOP")
		doc.space = space
		doc.process_owner = frappe.session.user

	doc.title = title
	doc.summary = summary
	doc.content = content
	doc.save()

	return {"name": doc.name, "sop_no": doc.sop_no, "status": doc.status, "version": doc.version}


@frappe.whitelist()
def acknowledge(sop, version):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	if doc.status != "Effective":
		frappe.throw(_("Only an effective procedure can be acknowledged."))

	if has_acknowledged(sop, version):
		return

	frappe.get_doc(
		{
			"doctype": "SOP Acknowledgement",
			"sop": sop,
			"version": version,
			"user": frappe.session.user,
			"acknowledged_at": frappe.utils.now_datetime(),
			"method": "Web",
		}
	).insert(ignore_permissions=True)

	return True
