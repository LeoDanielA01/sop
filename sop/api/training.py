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
		order_by="due_on asc",
		limit_page_length=limit,
	)

	urgency = {state: index for index, state in enumerate(("Overdue", "In Progress", "Assigned"))}
	rows.sort(key=lambda row: urgency.get(row.status, len(urgency)))

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
		"tasks": [
			{**row.as_dict(), "witnessed": row.task_type in training.WITNESSED} for row in doc.tasks
		],
		"can_assess": can_assess(doc) and doc.trainee != frappe.session.user,
		"is_mine": doc.trainee == frappe.session.user,
		"quiz": quiz_summary(doc),
		"remarks": doc.remarks,
	}


def quiz_summary(doc):
	from sop.api.quiz import summary

	return summary(doc)


@frappe.whitelist()
def certificate(name):
	doc = frappe.get_doc("SOP Training Assignment", name)

	if doc.trainee != frappe.session.user and not can_assess(doc):
		frappe.throw(_("You can only see your own certificates."), frappe.PermissionError)

	if doc.status != "Completed" or doc.outcome != "Competent":
		frappe.throw(_("A certificate is only issued once training is completed as competent."))

	procedure = frappe.db.get_value("SOP", doc.sop, ["sop_no", "title"], as_dict=True) or {}

	return {
		"name": doc.name,
		"trainee": frappe.db.get_value("User", doc.trainee, "full_name") or doc.trainee,
		"sop_no": procedure.get("sop_no") or doc.sop,
		"title": procedure.get("title") or doc.sop,
		"version": doc.version,
		"method": doc.method,
		"score": doc.score,
		"completed_on": doc.completed_on,
		"assessed_by": (
			_("Online quiz")
			if doc.assessed_by_quiz and not doc.assessed_by
			else frappe.db.get_value("User", doc.assessed_by, "full_name") or doc.assessed_by
		),
		"is_refresher": doc.is_refresher,
		"organisation": frappe.db.get_single_value("Website Settings", "app_name")
		or frappe.db.get_default("company")
		or "",
	}


@frappe.whitelist()
def export_records(space=None, status=None):
	import csv
	import io

	if not ({"SOP Manager", "SOP Trainer", "System Manager"} & set(frappe.get_roles())):
		frappe.throw(_("Only trainers and managers can export training records."), frappe.PermissionError)

	filters = {}
	if status:
		filters["status"] = status
	if space:
		filters["sop"] = ("in", frappe.get_all("SOP", filters={"space": space}, pluck="name") or [""])

	rows = frappe.get_all(
		"SOP Training Assignment",
		filters=filters,
		fields=[
			"name",
			"trainee",
			"sop",
			"version",
			"method",
			"status",
			"outcome",
			"score",
			"assigned_on",
			"due_on",
			"completed_on",
			"assessed_by",
			"assessed_by_quiz",
			"is_refresher",
		],
		order_by="trainee asc, assigned_on desc",
		limit_page_length=0,
	)

	titles = procedure_titles([row.sop for row in rows])
	involved = {row.trainee for row in rows} | {row.assessed_by for row in rows if row.assessed_by}
	people = {
		row.name: row.full_name
		for row in frappe.get_all(
			"User", filters={"name": ("in", list(involved) or [""])}, fields=["name", "full_name"], limit_page_length=0
		)
	}

	out = io.StringIO()
	writer = csv.writer(out)
	writer.writerow(
		[
			_("Record"),
			_("Person"),
			_("Email"),
			_("Procedure"),
			_("Title"),
			_("Revision"),
			_("Method"),
			_("Status"),
			_("Outcome"),
			_("Score %"),
			_("Assigned"),
			_("Due"),
			_("Completed"),
			_("Assessed by"),
			_("Refresher"),
		]
	)

	for row in rows:
		about = titles.get(row.sop, {})
		writer.writerow(
			[
				row.name,
				people.get(row.trainee) or row.trainee,
				row.trainee,
				about.get("sop_no") or row.sop,
				about.get("title") or "",
				row.version,
				row.method,
				row.status,
				row.outcome,
				flt(row.score) if row.score is not None else "",
				row.assigned_on or "",
				row.due_on or "",
				row.completed_on or "",
				assessor(row, people),
				_("Yes") if row.is_refresher else "",
			]
		)

	frappe.response["type"] = "csv"
	frappe.response["doctype"] = f"training-records-{frappe.utils.nowdate()}"
	frappe.response["result"] = out.getvalue()


def assessor(row, people):
	if row.assessed_by_quiz and not row.assessed_by:
		return _("Online quiz")
	return people.get(row.assessed_by) or row.assessed_by or ""


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
	return {
		"open": frappe.db.count(
			"SOP Training Assignment", {"trainee": user, "status": ("in", training.OPEN_STATES)}
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
