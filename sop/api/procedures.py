# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.utils import add_days, nowdate

from sop.api.lifecycle import actions_for, approvals_of
from sop.api.mentions import resolve
from sop.api.review import review_rights


@frappe.whitelist()
def spaces():
	rows = frappe.get_list(
		"SOP Space",
		fields=["name", "title", "space_code", "visibility", "icon"],
		order_by="title asc",
		limit_page_length=0,
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

	waiting = pending_approvals(user, space)
	unsigned = unacknowledged_count(user, space)

	return {
		"approval": waiting,
		"drafts": frappe.db.count("SOP", dict(scope, status="Draft", owner=user)),
		"unacknowledged": unsigned,
		"review": frappe.db.count(
			"SOP", dict(scope, status="Effective", review_due=("<=", add_days(nowdate(), 30)))
		),
		"attention": attention(user) if space else waiting + unsigned,
	}


def attention(user):
	return pending_approvals(user) + unacknowledged_count(user)


def pending_approvals(user, space=None):
	filters = {"parenttype": "SOP", "approver": user, "decision": "Pending"}
	names = frappe.get_all("SOP Approval", filters=filters, pluck="parent", limit_page_length=0)
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

	effective = frappe.get_all("SOP", filters=scope, fields=["name", "version"], limit_page_length=0)
	if not effective:
		return 0

	signed = {
		(row.sop, row.version)
		for row in frappe.get_all(
			"SOP Acknowledgement",
			filters={"user": user, "sop": ("in", [row.name for row in effective])},
			fields=["sop", "version"],
			limit_page_length=0,
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
	"sop_process",
	"process_owner",
	"effective_from",
	"review_due",
	"modified",
]


@frappe.whitelist()
def list_procedures(space=None, view="all", process=None, search=None, start=0, page_length=20):
	filters = view_filters(space, view)

	if process:
		filters["sop_process"] = ("in", process_scope(process))

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


def process_scope(process):
	from sop.api.processes import scope_of

	return scope_of(process)


def view_filters(space, view):
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
			limit_page_length=0,
		)
		filters.update({"name": ("in", names or [""]), "status": "In Review"})
	elif view == "unacknowledged":
		filters["name"] = ("in", unacknowledged_names(user, space) or [""])

	return filters


def unacknowledged_names(user, space=None):
	scope = {"status": "Effective"}
	if space:
		scope["space"] = space

	effective = frappe.get_all("SOP", filters=scope, fields=["name", "version"], limit_page_length=0)
	if not effective:
		return []

	signed = {
		(row.sop, row.version)
		for row in frappe.get_all(
			"SOP Acknowledgement",
			filters={"user": user, "sop": ("in", [row.name for row in effective])},
			fields=["sop", "version"],
			limit_page_length=0,
		)
	}
	return [row.name for row in effective if (row.name, row.version) not in signed]


@frappe.whitelist()
def neighbours(name):
	from sop.api.processes import tree

	doc = frappe.get_doc("SOP", name)
	doc.check_permission("read")

	rows = frappe.get_list(
		"SOP",
		filters={"space": doc.space, "status": ("!=", "Retired")},
		fields=["name", "sop_no", "title", "sop_process"],
		order_by="sop_no asc",
		limit_page_length=0,
	)

	rank = reading_rank(tree(doc.space))
	rows.sort(key=lambda row: (rank.get(row.sop_process, -1), row.sop_no or ""))

	names = [row.name for row in rows]
	if name not in names:
		return {"previous": None, "next": None}

	index = names.index(name)

	return {
		"previous": rows[index - 1] if index else None,
		"next": rows[index + 1] if index + 1 < len(rows) else None,
	}


def reading_rank(roots):
	rank = {}

	def walk(nodes):
		for node in nodes:
			rank[node["name"]] = len(rank)
			walk(node["children"])

	walk(roots)

	return rank


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
		"space_title": frappe.db.get_value("SOP Space", doc.space, "title"),
		"process": doc.sop_process,
		"process_trail": process_trail(doc.sop_process),
		"risk_level": doc.risk_level,
		"is_controlled": doc.is_controlled,
		"content": content,
		"tags": [tag for tag in (doc._user_tags or "").split(",") if tag],
		"references": resolve(references_of(doc)),
		"process_owner": doc.process_owner,
		"process_owner_name": owner.get("full_name"),
		"owner_image": owner.get("user_image"),
		"effective_from": doc.effective_from,
		"review_due": doc.review_due,
		"edited": frappe.utils.pretty_date(doc.modified),
		"edited_by": editor_name(doc.modified_by),
		"created": frappe.utils.pretty_date(doc.creation),
		"created_by": editor_name(doc.owner),
		"revisions": frappe.get_all(
			"SOP Revision",
			filters={"sop": doc.name},
			fields=["version", "effective_from"],
			order_by="version desc",
			limit_page_length=0,
		),
		"acknowledged": bool(signed and signed.version == doc.version),
		"acknowledged_on": signed.acknowledged_at if signed else None,
		"acknowledged_version": signed.version if signed else None,
		"can_edit": doc.is_editable() and doc.has_permission("write"),
		"approvals": approvals_of(doc),
		"actions": actions_for(doc),
		"review": review_rights(doc),
	}


def editor_name(user):
	if not user:
		return None

	if user == frappe.session.user:
		return _("you")

	return frappe.db.get_value("User", user, "full_name") or user


def process_trail(process):
	if not process:
		return []

	from sop.api.processes import trail

	return trail(process)


def served_content(doc, revision=None):
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
		"User", filters={"name": ("in", users)}, fields=["name", "full_name", "user_image"],
		limit_page_length=0,
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
def save_draft(
	space,
	title,
	name=None,
	summary=None,
	content=None,
	process=None,
	risk_level=None,
	is_controlled=None,
):
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
	doc.sop_process = process or None

	if risk_level:
		doc.risk_level = risk_level

	if is_controlled is not None:
		doc.is_controlled = frappe.utils.cint(is_controlled)

	doc.save()

	return {"name": doc.name, "sop_no": doc.sop_no, "status": doc.status, "version": doc.version}


@frappe.whitelist()
def create_space(
	title,
	space_code=None,
	visibility="Public",
	review_interval_months=12,
	template=None,
	with_drafts=0,
	description=None,
	team=None,
):
	if not frappe.has_permission("SOP Space", "create"):
		frappe.throw(_("You are not allowed to create a space."), frappe.PermissionError)

	code = (space_code or initials(title)).strip().upper()
	if not code:
		frappe.throw(_("A space needs a short code — it becomes the procedure number."))

	if frappe.db.exists("SOP Space", code):
		frappe.throw(_("A space with the code {0} already exists.").format(code))

	doc = frappe.get_doc(
		{
			"doctype": "SOP Space",
			"title": title,
			"space_code": code,
			"visibility": visibility or "Public",
			"review_interval_months": frappe.utils.cint(review_interval_months) or 12,
			"description": description,
			"team": team,
		}
	).insert()

	seeded = {}
	if template:
		from sop.templates import apply_template

		seeded = apply_template(doc.name, template, with_drafts=frappe.utils.cint(with_drafts))

	return {
		"name": doc.name,
		"title": doc.title,
		"space_code": doc.space_code,
		"total": seeded.get("drafts", 0),
		"overdue": 0,
		"seeded": seeded,
	}


def initials(title):
	words = [word for word in re.split(r"[^A-Za-z0-9]+", title or "") if word]
	if not words:
		return ""

	if len(words) == 1:
		return words[0][:3]

	return "".join(word[0] for word in words)[:4]


@frappe.whitelist()
def people(search=None, limit=10):
	filters = {"enabled": 1, "user_type": "System User"}
	if search:
		filters["full_name"] = ("like", f"%{search}%")

	return frappe.get_all(
		"User",
		filters=filters,
		fields=["name", "full_name", "user_image"],
		order_by="full_name asc",
		limit_page_length=frappe.utils.cint(limit),
	)

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
