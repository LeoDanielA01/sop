# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime

from sop import training

OUTCOMES = ("Pending", "Competent", "Needs More Practice", "Not Competent")


@frappe.whitelist()
def sessions(status=None, limit=50):
	filters = {"status": status} if status else {}

	rows = frappe.get_list(
		"SOP Training Session",
		filters=filters,
		fields=["name", "title", "trainer", "status", "scheduled_on", "location", "method"],
		order_by="scheduled_on desc",
		limit_page_length=limit,
	)
	if not rows:
		return []

	names = [row.name for row in rows]
	attendees = counted("SOP Session Attendee", names)
	attended = counted("SOP Session Attendee", names, {"attended": 1})
	procedures = counted("SOP Session Procedure", names)
	trainers = frappe.get_all(
		"User",
		filters={"name": ("in", list({row.trainer for row in rows if row.trainer}) or [""])},
		fields=["name", "full_name", "user_image"],
		limit_page_length=0,
	)
	by_email = {row.name: row for row in trainers}

	for row in rows:
		row.trainer_name = by_email.get(row.trainer, {}).get("full_name") or row.trainer
		row.trainer_image = by_email.get(row.trainer, {}).get("user_image")
		row.attendees = attendees.get(row.name, 0)
		row.attended = attended.get(row.name, 0)
		row.procedures = procedures.get(row.name, 0)

	return rows


def counted(doctype, parents, extra=None):
	filters = dict(extra or {}, parenttype="SOP Training Session", parent=("in", parents))
	rows = frappe.get_all(doctype, filters=filters, pluck="parent", limit_page_length=0)

	totals = {}
	for parent in rows:
		totals[parent] = totals.get(parent, 0) + 1

	return totals


@frappe.whitelist()
def session(name):
	doc = frappe.get_doc("SOP Training Session", name)
	doc.check_permission("read")

	people = frappe.get_all(
		"User",
		filters={"name": ("in", [row.user for row in doc.attendees] or [""])},
		fields=["name", "full_name", "user_image"],
		limit_page_length=0,
	)
	by_email = {row.name: row for row in people}

	return {
		"name": doc.name,
		"title": doc.title,
		"trainer": doc.trainer,
		"status": doc.status,
		"scheduled_on": doc.scheduled_on,
		"location": doc.location,
		"method": doc.method,
		"notes": doc.notes,
		"can_run": can_run(),
		"procedures": [{"sop": row.sop, "title": row.title} for row in doc.procedures],
		"attendees": [
			{
				"idx": row.idx,
				"user": row.user,
				"full_name": by_email.get(row.user, {}).get("full_name") or row.user,
				"image": by_email.get(row.user, {}).get("user_image"),
				"attended": row.attended,
				"outcome": row.outcome or "Pending",
				"score": row.score,
				"remarks": row.remarks,
			}
			for row in doc.attendees
		],
	}


@frappe.whitelist()
def save_session(
	name=None,
	title=None,
	trainer=None,
	scheduled_on=None,
	location=None,
	method="Classroom",
	procedures=None,
	attendees=None,
	notes=None,
):
	ensure_trainer()

	doc = frappe.get_doc("SOP Training Session", name) if name else frappe.new_doc("SOP Training Session")

	doc.title = title
	doc.trainer = trainer or frappe.session.user
	doc.scheduled_on = scheduled_on
	doc.location = location
	doc.method = method
	doc.notes = notes

	doc.procedures = []
	for sop in as_list(procedures):
		doc.append(
			"procedures", {"sop": sop, "title": frappe.db.get_value("SOP", sop, "title")}
		)

	keep = {row.user: row for row in doc.attendees}
	doc.attendees = []
	for user in as_list(attendees):
		existing = keep.get(user)
		doc.append(
			"attendees",
			{
				"user": user,
				"attended": existing.attended if existing else 0,
				"outcome": existing.outcome if existing else "Pending",
				"score": existing.score if existing else None,
				"remarks": existing.remarks if existing else None,
			},
		)

	doc.save()

	return {"name": doc.name}


@frappe.whitelist()
def record_attendance(name, rows):
	ensure_trainer()

	doc = frappe.get_doc("SOP Training Session", name)
	decisions = {row.get("user"): row for row in as_list(rows)}

	for attendee in doc.attendees:
		decision = decisions.get(attendee.user)
		if not decision:
			continue

		attendee.attended = 1 if decision.get("attended") else 0
		attendee.outcome = decision.get("outcome") if decision.get("outcome") in OUTCOMES else "Pending"
		attendee.score = decision.get("score")
		attendee.remarks = decision.get("remarks")

	doc.status = "Held"
	doc.save()

	return {"name": doc.name, "closed": close_assignments(doc)}


def close_assignments(doc):
	closed = 0

	for attendee in doc.attendees:
		if not attendee.attended or attendee.outcome == "Pending":
			continue

		for row in doc.procedures:
			closed += settle(row.sop, attendee, doc.name)

	return closed


def settle(sop, attendee, session_name):
	name = frappe.db.get_value(
		"SOP Training Assignment",
		{"sop": sop, "trainee": attendee.user, "status": ("in", training.OPEN_STATES)},
		"name",
	)
	if not name:
		return 0

	assignment = frappe.get_doc("SOP Training Assignment", name)
	assignment.session = session_name
	assignment.outcome = attendee.outcome
	assignment.score = attendee.score
	assignment.assessed_by = frappe.session.user
	assignment.completed_on = now_datetime()

	for task in assignment.tasks:
		if not task.completed:
			task.completed = 1
			task.completed_on = now_datetime()
			task.completed_by = frappe.session.user
			task.verified_by = frappe.session.user

	assignment.save(ignore_permissions=True)

	return 1


@frappe.whitelist()
def cancel_session(name):
	ensure_trainer()

	doc = frappe.get_doc("SOP Training Session", name)
	doc.status = "Cancelled"
	doc.save()

	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def procedure_options(search=None):
	filters = {"status": "Effective"}
	if search:
		filters["title"] = ("like", f"%{search}%")

	rows = frappe.get_list(
		"SOP",
		filters=filters,
		fields=["name", "sop_no", "title"],
		order_by="sop_no asc",
		limit_page_length=50,
	)
	return [{"value": row.name, "label": f"{row.sop_no} · {row.title}"} for row in rows]


def as_list(value):
	if isinstance(value, str):
		value = frappe.parse_json(value)

	return value or []


def can_run():
	return bool({"SOP Trainer", "SOP Manager"} & set(frappe.get_roles()))


def ensure_trainer():
	if not can_run():
		frappe.throw(_("Only a trainer can run a session."), frappe.PermissionError)

