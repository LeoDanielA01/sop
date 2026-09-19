# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_months, cint, getdate, now_datetime, nowdate

OPEN_STATES = ("Assigned", "In Progress", "Overdue")
IN_FORCE = ("Effective", "Under Revision")
WITNESSED = ("Attend Session", "Practical", "Verification", "Assessment")
REMIND_BEFORE = 3
ESCALATE_AFTER = 7

TASKS_BY_METHOD = {
	"Read & Understand": [("Read the procedure", "Read Procedure")],
	"Classroom": [
		("Read the procedure", "Read Procedure"),
		("Attend the training session", "Attend Session"),
	],
	"On the Job": [
		("Read the procedure", "Read Procedure"),
		("Carry out the procedure under supervision", "Practical"),
		("Supervisor confirms competence", "Verification"),
	],
	"Assessment": [
		("Read the procedure", "Read Procedure"),
		("Sit the assessment", "Assessment"),
	],
}


def assign_for_procedure(sop, cause=None, material=True):
	doc = frappe.get_doc("SOP", sop)

	if not cint(material):
		carry_forward(doc)
		return []

	replaced = retire_old(doc)
	created = []

	for requirement in requirements_for(doc):
		for user in expand(requirement):
			assignment = create_assignment(doc, requirement, user, cause, supersedes=replaced.get(user))
			if assignment:
				created.append(assignment)

	return created


def stale(doc):
	return frappe.get_all(
		"SOP Training Assignment",
		filters={"sop": doc.name, "status": ("in", OPEN_STATES), "version": ("!=", doc.version)},
		fields=["name", "trainee"],
		limit_page_length=0,
	)


def retire_old(doc):
	replaced = {}

	for row in stale(doc):
		frappe.db.set_value(
			"SOP Training Assignment",
			row.name,
			{"status": "Waived", "remarks": _("Replaced by revision {0}").format(doc.version)},
			update_modified=False,
		)
		replaced[row.trainee] = row.name

	return replaced


def carry_forward(doc):
	for row in stale(doc):
		frappe.db.set_value("SOP Training Assignment", row.name, "version", doc.version, update_modified=False)


def requirements_for(doc):
	rows = frappe.get_all(
		"SOP Training Requirement",
		filters={"enabled": 1, "scope": "Procedure", "sop": doc.name},
		fields=["name"],
		limit_page_length=0,
	)
	rows += frappe.get_all(
		"SOP Training Requirement",
		filters={"enabled": 1, "scope": "Space", "space": doc.space},
		fields=["name"],
		limit_page_length=0,
	)
	return [frappe.get_doc("SOP Training Requirement", row.name) for row in rows]


def procedures_of(requirement):
	if requirement.scope == "Procedure":
		if not requirement.sop:
			return []
		return frappe.get_all("SOP", filters={"name": requirement.sop, "status": ("in", IN_FORCE)}, pluck="name")

	return frappe.get_all(
		"SOP",
		filters={"space": requirement.space, "status": ("in", IN_FORCE)},
		pluck="name",
		limit_page_length=0,
	)


def eligible(users):
	from sop.api.session import can_use_app

	users = [user for user in dict.fromkeys(users) if user and user not in ("Administrator", "Guest")]
	if not users:
		return []

	active = set(
		frappe.get_all(
			"User",
			filters={"name": ("in", users), "enabled": 1, "user_type": "System User"},
			pluck="name",
			limit_page_length=0,
		)
	)
	return [user for user in users if user in active and can_use_app(user)]


def expand(requirement):
	if requirement.applies_to == "User":
		return eligible([requirement.user])

	if requirement.applies_to == "Role":
		return eligible(
			frappe.get_all(
				"Has Role",
				filters={"role": requirement.role, "parenttype": "User"},
				pluck="parent",
				limit_page_length=0,
			)
		)

	if requirement.applies_to == "Team":
		return eligible(
			frappe.get_all(
				"SOP Team Member",
				filters={"parent": requirement.team, "parenttype": "SOP Team"},
				pluck="user",
				limit_page_length=0,
			)
		)

	if not frappe.db.exists("DocType", "Employee"):
		return []

	field = "designation" if requirement.applies_to == "Designation" else "department"
	value = requirement.designation if field == "designation" else requirement.department

	return eligible(
		frappe.get_all(
			"Employee",
			filters={field: value, "status": "Active", "user_id": ("is", "set")},
			pluck="user_id",
			limit_page_length=0,
		)
	)


def baseline(sop):
	versions = frappe.get_all(
		"SOP Revision",
		filters={"sop": sop, "is_material": 1},
		pluck="version",
		order_by="version desc",
		limit_page_length=1,
	)
	return cint(versions[0]) if versions else 0


def covers(row, since):
	if row.status in OPEN_STATES:
		return True

	if cint(row.version) < since:
		return False

	if row.status == "Waived":
		return True

	return row.status == "Completed" and row.outcome != "Not Competent"


def holders(sop):
	since = baseline(sop)
	rows = frappe.get_all(
		"SOP Training Assignment",
		filters={"sop": sop},
		fields=["trainee", "status", "outcome", "version"],
		limit_page_length=0,
	)
	return {row.trainee for row in rows if covers(row, since)}


def create_assignment(doc, requirement, user, cause=None, is_refresher=0, supersedes=None):
	if not user or not frappe.db.exists("User", user):
		return None

	if frappe.db.exists(
		"SOP Training Assignment",
		{"sop": doc.name, "trainee": user, "status": ("in", OPEN_STATES)},
	):
		return None

	if not is_refresher and not supersedes and user in holders(doc.name):
		return None

	assignment = frappe.get_doc(
		{
			"doctype": "SOP Training Assignment",
			"sop": doc.name,
			"version": doc.version,
			"trainee": user,
			"requirement": requirement.name if requirement else None,
			"method": requirement.method if requirement else "Read & Understand",
			"assigned_on": nowdate(),
			"due_on": add_days(nowdate(), (requirement.due_days if requirement else 14) or 14),
			"requires_assessment": requirement.requires_assessment if requirement else 0,
			"pass_mark": requirement.pass_mark if requirement else 0,
			"max_attempts": (requirement.get("max_attempts") if requirement else 0) or 3,
			"question_count": (requirement.get("question_count") if requirement else 0) or 0,
			"is_refresher": is_refresher,
			"supersedes": supersedes,
			"remarks": cause,
		}
	)

	for task, task_type in TASKS_BY_METHOD.get(assignment.method, TASKS_BY_METHOD["Read & Understand"]):
		assignment.append("tasks", {"task": task, "task_type": task_type, "due_on": assignment.due_on})

	assignment.insert(ignore_permissions=True)
	notify(assignment)

	return assignment.name


def notify(assignment):
	sop_no = frappe.db.get_value("SOP", assignment.sop, "sop_no") or assignment.sop

	if assignment.supersedes and not assignment.is_refresher and "not-competent" in (assignment.remarks or ""):
		subject = _("Retraining assigned: {0}")
	else:
		subject = _("Training assigned: {0}")

	tell_about(assignment.trainee, subject.format(sop_no), assignment.sop)


def tell_about(user, subject, sop):
	from sop.notifications import tell

	tell(user, subject, frappe._dict(doctype="SOP", name=sop), kind="training")


def retrain(assignment):
	doc = frappe.get_doc("SOP", assignment.sop)

	if assignment.requirement and frappe.db.exists("SOP Training Requirement", assignment.requirement):
		requirement = frappe.get_doc("SOP Training Requirement", assignment.requirement)
	else:
		requirement = frappe._dict(
			name=None,
			method=assignment.method,
			due_days=14,
			requires_assessment=assignment.requires_assessment,
			pass_mark=assignment.pass_mark,
			max_attempts=assignment.max_attempts,
			question_count=assignment.question_count,
		)

	return create_assignment(
		doc,
		requirement,
		assignment.trainee,
		cause=_("Retraining after a not-competent outcome"),
		supersedes=assignment.name,
	)


def mark_read(sop, user):
	for name in frappe.get_all(
		"SOP Training Assignment",
		filters={"sop": sop, "trainee": user, "status": ("in", OPEN_STATES)},
		pluck="name",
	):
		doc = frappe.get_doc("SOP Training Assignment", name)
		changed = False

		for row in doc.tasks:
			if row.task_type == "Read Procedure" and not row.completed:
				row.completed = 1
				row.completed_on = now_datetime()
				row.completed_by = user
				changed = True

		if changed:
			doc.flags.from_acknowledgement = True
			doc.save(ignore_permissions=True)


def mark_overdue():
	names = frappe.get_all(
		"SOP Training Assignment",
		filters={"status": ("in", ("Assigned", "In Progress")), "due_on": ("<", nowdate())},
		pluck="name",
		limit_page_length=0,
	)

	for name in names:
		frappe.db.set_value("SOP Training Assignment", name, "status", "Overdue", update_modified=False)

	return len(names)


def latest_completions(rows):
	latest = {}
	for row in rows:
		key = (row.sop, row.trainee)
		if key not in latest or getdate(row.completed_on) > getdate(latest[key].completed_on):
			latest[key] = row
	return list(latest.values())


def schedule_refreshers():
	created = []

	rows = frappe.get_all(
		"SOP Training Assignment",
		filters={"status": "Completed", "outcome": "Competent", "completed_on": ("is", "set")},
		fields=["name", "sop", "trainee", "requirement", "completed_on"],
		limit_page_length=0,
	)
	if not rows:
		return created

	superseded = set(
		frappe.get_all(
			"SOP Training Assignment",
			filters={"supersedes": ("in", [row.name for row in rows])},
			pluck="supersedes",
			limit_page_length=0,
		)
	)

	for row in latest_completions(rows):
		if not row.requirement or row.name in superseded:
			continue

		if not frappe.db.exists("SOP Training Requirement", row.requirement):
			continue

		requirement = frappe.get_doc("SOP Training Requirement", row.requirement)
		if not requirement.enabled or not requirement.refresher_months:
			continue

		due = add_months(getdate(row.completed_on), requirement.refresher_months)
		if getdate(nowdate()) < getdate(due):
			continue

		doc = frappe.get_doc("SOP", row.sop)
		if doc.status not in IN_FORCE:
			continue

		name = create_assignment(
			doc, requirement, row.trainee, cause=_("Refresher"), is_refresher=1, supersedes=row.name
		)
		if name:
			created.append(name)

	return created


def sync_requirements():
	created = 0

	for name in frappe.get_all("SOP Training Requirement", filters={"enabled": 1}, pluck="name"):
		requirement = frappe.get_doc("SOP Training Requirement", name)
		users = expand(requirement)
		if not users:
			continue

		for sop in procedures_of(requirement):
			doc = frappe.get_doc("SOP", sop)
			covered = holders(sop)

			for user in users:
				if user in covered:
					continue
				if create_assignment(doc, requirement, user, cause=_("Newly in scope of this rule")):
					created += 1
					covered.add(user)

	return created


def manager_of(user):
	if not frappe.db.exists("DocType", "Employee"):
		return None

	boss = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"}, "reports_to")
	return frappe.db.get_value("Employee", boss, "user_id") if boss else None


def remind():
	today = getdate(nowdate())
	fields = ["name", "sop", "trainee", "due_on"]
	numbers = {}

	def number(sop):
		if sop not in numbers:
			numbers[sop] = frappe.db.get_value("SOP", sop, "sop_no") or sop
		return numbers[sop]

	for row in frappe.get_all(
		"SOP Training Assignment",
		filters={"status": ("in", ("Assigned", "In Progress")), "due_on": add_days(today, REMIND_BEFORE)},
		fields=fields,
		limit_page_length=0,
	):
		tell_about(
			row.trainee,
			_("Training due in {0} days: {1}").format(REMIND_BEFORE, number(row.sop)),
			row.sop,
		)

	for row in frappe.get_all(
		"SOP Training Assignment",
		filters={"status": "Overdue", "due_on": add_days(today, -1)},
		fields=fields,
		limit_page_length=0,
	):
		tell_about(row.trainee, _("Training overdue: {0}").format(number(row.sop)), row.sop)

	for row in frappe.get_all(
		"SOP Training Assignment",
		filters={"status": "Overdue", "due_on": add_days(today, -ESCALATE_AFTER)},
		fields=fields,
		limit_page_length=0,
	):
		boss = manager_of(row.trainee) or frappe.db.get_value("SOP", row.sop, "process_owner")
		if not boss or boss == row.trainee:
			continue

		who = frappe.db.get_value("User", row.trainee, "full_name") or row.trainee
		tell_about(
			boss,
			_("{0} is {1} days overdue on training for {2}").format(who, ESCALATE_AFTER, number(row.sop)),
			row.sop,
		)


def matrix(space=None):
	filters = {"status": "Effective"}
	if space:
		filters["space"] = space

	procedures = frappe.get_all(
		"SOP", filters=filters, fields=["name", "sop_no", "title"], order_by="sop_no asc",
		limit_page_length=0,
	)
	if not procedures:
		return {"procedures": [], "people": []}

	rows = frappe.get_all(
		"SOP Training Assignment",
		filters={"sop": ("in", [p.name for p in procedures])},
		fields=["sop", "trainee", "status", "outcome", "due_on", "completed_on"],
		limit_page_length=0,
	)

	people = {}
	for row in rows:
		person = people.setdefault(row.trainee, {"user": row.trainee, "cells": {}})
		current = person["cells"].get(row.sop)

		if not current or rank(row) > rank(current):
			person["cells"][row.sop] = row

	names = {
		row.name: row
		for row in frappe.get_all(
			"User",
			filters={"name": ("in", list(people))},
			fields=["name", "full_name", "user_image"],
			limit_page_length=0,
		)
	}

	for user, person in people.items():
		person["full_name"] = names.get(user, {}).get("full_name") or user
		person["user_image"] = names.get(user, {}).get("user_image")

	return {
		"procedures": procedures,
		"people": sorted(people.values(), key=lambda p: p["full_name"]),
	}


def rank(row):
	return {"Completed": 3, "In Progress": 2, "Assigned": 1, "Overdue": 1, "Waived": 2}.get(
		row.get("status"), 0
	)
