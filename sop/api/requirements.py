# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from sop import training

TARGETS = {
	"Role": "role",
	"Designation": "designation",
	"Department": "department",
	"Team": "team",
	"User": "user",
}


@frappe.whitelist()
def requirements(space=None):
	filters = {"space": space} if space else {}

	rows = frappe.get_list(
		"SOP Training Requirement",
		filters=filters,
		fields=[
			"name",
			"enabled",
			"applies_to",
			"role",
			"designation",
			"department",
			"team",
			"user",
			"scope",
			"sop",
			"space",
			"method",
			"due_days",
			"requires_assessment",
			"pass_mark",
			"refresher_months",
			"max_attempts",
			"question_count",
		],
		order_by="modified desc",
		limit_page_length=0,
	)

	procedures = titles_of([row.sop for row in rows])
	spaces = space_titles([row.space for row in rows])

	for row in rows:
		row.who = row.get(TARGETS.get(row.applies_to, "role")) or row.applies_to
		row.covers = (
			procedures.get(row.sop) or row.sop if row.scope == "Procedure" else spaces.get(row.space) or row.space
		)
		row.assignments = frappe.db.count("SOP Training Assignment", {"requirement": row.name})

	return rows


def titles_of(names):
	names = [name for name in names if name]
	if not names:
		return {}

	rows = frappe.get_all("SOP", filters={"name": ("in", names)}, fields=["name", "sop_no", "title"], limit_page_length=0)
	return {row.name: f"{row.sop_no} · {row.title}" for row in rows}


def space_titles(names):
	names = [name for name in names if name]
	if not names:
		return {}

	rows = frappe.get_all("SOP Space", filters={"name": ("in", names)}, fields=["name", "title"], limit_page_length=0)
	return {row.name: row.title for row in rows}


@frappe.whitelist()
def save_requirement(name=None, **values):
	ensure_manager()

	doc = frappe.get_doc("SOP Training Requirement", name) if name else frappe.new_doc(
		"SOP Training Requirement"
	)

	fields = (
		"applies_to",
		"role",
		"designation",
		"department",
		"team",
		"user",
		"scope",
		"sop",
		"space",
		"method",
		"due_days",
		"requires_assessment",
		"pass_mark",
		"refresher_months",
		"max_attempts",
		"question_count",
		"enabled",
	)

	for field in fields:
		if field in values:
			doc.set(field, values[field])

	for target, field in TARGETS.items():
		if doc.applies_to != target:
			doc.set(field, None)

	if doc.scope == "Procedure":
		doc.space = None
	else:
		doc.sop = None

	doc.save()

	return {"name": doc.name}


@frappe.whitelist()
def toggle_requirement(name, enabled):
	ensure_manager()

	doc = frappe.get_doc("SOP Training Requirement", name)
	doc.enabled = 1 if frappe.utils.cint(enabled) else 0
	doc.save()

	return {"name": doc.name, "enabled": doc.enabled}


@frappe.whitelist()
def delete_requirement(name):
	ensure_manager()

	frappe.delete_doc("SOP Training Requirement", name)

	return {"deleted": name}


@frappe.whitelist()
def run_requirement(name):
	ensure_manager()

	requirement = frappe.get_doc("SOP Training Requirement", name)
	created = 0

	for sop in training.procedures_of(requirement):
		doc = frappe.get_doc("SOP", sop)
		for user in training.expand(requirement):
			if training.create_assignment(doc, requirement, user):
				created += 1

	return {"created": created}


def ensure_manager():
	if not frappe.has_permission("SOP Training Requirement", "write"):
		frappe.throw(_("Only a training manager can change the rules."), frappe.PermissionError)
