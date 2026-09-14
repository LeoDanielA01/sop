# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

from sop import training


@frappe.whitelist()
def my_training(status=None, limit=50):
	filters = {"trainee": frappe.session.user}
	if status:
		filters["status"] = status
	else:
		filters["status"] = ("in", training.OPEN_STATES)

	rows = frappe.get_all(
		"SOP Training Assignment",
		filters=filters,
		fields=[
			"name",
			"sop",
			"version",
			"status",
			"progress",
			"method",
			"due_on",
			"outcome",
			"is_refresher",
		],
		order_by="field(status, 'Overdue', 'In Progress', 'Assigned'), due_on asc",
		limit_page_length=limit,
	)

	titles = procedure_titles([row.sop for row in rows])
	for row in rows:
		row.title = titles.get(row.sop, {}).get("title")
		row.sop_no = titles.get(row.sop, {}).get("sop_no")

	return rows


@frappe.whitelist()
def assignment(name):
	doc = frappe.get_doc("SOP Training Assignment", name)
	doc.check_permission("read")

	procedure = frappe.db.get_value("SOP", doc.sop, ["sop_no", "title"], as_dict=True) or {}

	return {
		"name": doc.name,
		"sop": doc.sop,
		"sop_no": procedure.get("sop_no"),
		"title": procedure.get("title"),
		"version": doc.version,
		"trainee": doc.trainee,
		"status": doc.status,
		"progress": doc.progress,
		"method": doc.method,
		"due_on": doc.due_on,
		"outcome": doc.outcome,
		"score": doc.score,
		"pass_mark": doc.pass_mark,
		"requires_assessment": doc.requires_assessment,
		"assessed_by": doc.assessed_by,
		"is_refresher": doc.is_refresher,
		"tasks": [row.as_dict() for row in doc.tasks],
		"can_assess": can_assess(doc),
	}


@frappe.whitelist()
def complete_task(name, idx):
	doc = frappe.get_doc("SOP Training Assignment", name)

	if doc.trainee != frappe.session.user and not can_assess(doc):
		frappe.throw(_("Only {0} or a trainer can tick these off.").format(doc.trainee))

	return doc.complete_task(frappe.utils.cint(idx))


@frappe.whitelist()
def record_outcome(name, outcome, score=None, remarks=None):
	doc = frappe.get_doc("SOP Training Assignment", name)

	if not can_assess(doc):
		frappe.throw(_("Only a trainer or SOP manager can record an outcome."))

	if doc.trainee == frappe.session.user:
		frappe.throw(_("You cannot assess your own training."))

	doc.outcome = outcome
	doc.score = flt(score) if score is not None else doc.score
	doc.remarks = remarks or doc.remarks
	doc.assessed_by = frappe.session.user
	doc.save(ignore_permissions=True)

	return doc.status


@frappe.whitelist()
def assign(sop, trainees, method="Read & Understand", due_days=14):
	if isinstance(trainees, str):
		trainees = frappe.parse_json(trainees)

	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	if not frappe.has_permission("SOP Training Assignment", "create"):
		frappe.throw(_("You cannot assign training."))

	requirement = frappe._dict(
		name=None, method=method, due_days=frappe.utils.cint(due_days), requires_assessment=0, pass_mark=0
	)

	return [name for name in (training.create_assignment(doc, requirement, user) for user in trainees) if name]


@frappe.whitelist()
def matrix(space=None):
	return training.matrix(space)


@frappe.whitelist()
def training_counts():
	user = frappe.session.user
	open_states = ("Assigned", "In Progress", "Overdue")

	return {
		"open": frappe.db.count(
			"SOP Training Assignment", {"trainee": user, "status": ("in", open_states)}
		),
		"overdue": frappe.db.count("SOP Training Assignment", {"trainee": user, "status": "Overdue"}),
		"to_assess": frappe.db.count(
			"SOP Training Assignment", {"assessed_by": user, "outcome": "Pending"}
		)
		if frappe.has_permission("SOP Training Assignment", "write")
		else 0,
	}


def can_assess(doc):
	roles = set(frappe.get_roles())
	return bool({"SOP Trainer", "SOP Manager"} & roles)


def procedure_titles(names):
	names = [name for name in names if name]
	if not names:
		return {}

	rows = frappe.get_all(
		"SOP", filters={"name": ("in", names)}, fields=["name", "sop_no", "title"],
		limit_page_length=0,
	)
	return {row.name: row for row in rows}
