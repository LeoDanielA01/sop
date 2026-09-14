# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_months, getdate, nowdate

OPEN_STATES = ("Assigned", "In Progress", "Overdue")

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


def assign_for_procedure(sop, cause=None):
	doc = frappe.get_doc("SOP", sop)
	created = []

	for requirement in requirements_for(doc):
		for user in expand(requirement):
			assignment = create_assignment(doc, requirement, user, cause)
			if assignment:
				created.append(assignment)

	return created


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


def expand(requirement):
	if requirement.applies_to == "User":
		return [requirement.user] if requirement.user else []

	if requirement.applies_to == "Role":
		return frappe.get_all(
			"Has Role",
			filters={"role": requirement.role, "parenttype": "User"},
			pluck="parent",
			limit_page_length=0,
		)

	if requirement.applies_to == "Team":
		return frappe.get_all(
			"SOP Team Member", filters={"parent": requirement.team}, pluck="user",
			limit_page_length=0,
		)

	field = "designation" if requirement.applies_to == "Designation" else "department"
	value = requirement.designation if field == "designation" else requirement.department

	return frappe.get_all(
		"Employee",
		filters={field: value, "status": "Active", "user_id": ("is", "set")},
		pluck="user_id",
		limit_page_length=0,
	)


def create_assignment(doc, requirement, user, cause=None, is_refresher=0, supersedes=None):
	if not user or not frappe.db.exists("User", user):
		return None

	if frappe.db.exists(
		"SOP Training Assignment",
		{"sop": doc.name, "version": doc.version, "trainee": user, "status": ("in", OPEN_STATES)},
	):
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
			"is_refresher": is_refresher,
			"supersedes": supersedes,
			"remarks": cause,
		}
	)

	for task, task_type in TASKS_BY_METHOD.get(assignment.method, TASKS_BY_METHOD["Read & Understand"]):
		assignment.append(
			"tasks", {"task": task, "task_type": task_type, "due_on": assignment.due_on}
		)

	assignment.insert(ignore_permissions=True)
	notify(assignment)

	return assignment.name


def notify(assignment):
	frappe.get_doc(
		{
			"doctype": "Notification Log",
			"subject": _("Training assigned: {0}").format(assignment.sop),
			"for_user": assignment.trainee,
			"type": "Assignment",
			"document_type": "SOP Training Assignment",
			"document_name": assignment.name,
		}
	).insert(ignore_permissions=True)


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


def schedule_refreshers():
	created = []

	rows = frappe.get_all(
		"SOP Training Assignment",
		filters={"status": "Completed", "outcome": "Competent"},
		fields=["name", "sop", "trainee", "requirement", "completed_on"],
		limit_page_length=0,
	)

	for row in rows:
		if not row.requirement or not row.completed_on:
			continue

		requirement = frappe.get_doc("SOP Training Requirement", row.requirement)
		if not requirement.enabled or not requirement.refresher_months:
			continue

		due = add_months(getdate(row.completed_on), requirement.refresher_months)
		if getdate(nowdate()) < getdate(due):
			continue

		doc = frappe.get_doc("SOP", row.sop)
		name = create_assignment(
			doc, requirement, row.trainee, cause=_("Refresher"), is_refresher=1, supersedes=row.name
		)
		if name:
			created.append(name)

	return created


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
