# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from sop.sop.doctype.sop_process.sop_process import ancestors_of, descendants_of
from sop.templates import TEMPLATES, apply_template


@frappe.whitelist()
def tree(space=None):
	filters = {"space": space} if space else {}
	rows = frappe.get_list(
		"SOP Process",
		filters=filters,
		fields=["name", "title", "space", "parent_process", "sequence", "description"],
		order_by="sequence asc, title asc",
		limit_page_length=0,
	)

	counts = procedure_counts(space)
	nodes = {
		row.name: {
			"name": row.name,
			"title": row.title,
			"space": row.space,
			"parent": row.parent_process,
			"description": row.description,
			"count": counts.get(row.name, 0),
			"children": [],
		}
		for row in rows
	}

	roots = []
	for row in rows:
		node = nodes[row.name]
		parent = nodes.get(row.parent_process)
		if parent:
			parent["children"].append(node)
		else:
			roots.append(node)

	for node in nodes.values():
		roll_up(node)

	return roots


def roll_up(node):
	node["total"] = node["count"] + sum(roll_up(child) for child in node["children"])
	return node["total"]


def procedure_counts(space=None):
	filters = {"space": space} if space else {}
	rows = frappe.get_all(
		"SOP",
		filters=dict(filters, sop_process=("is", "set")),
		fields=["sop_process", "count(name) as total"],
		group_by="sop_process",
	)
	return {row.sop_process: row.total for row in rows}


@frappe.whitelist()
def create_process(title, space, parent=None, sequence=None, description=None):
	if not frappe.has_permission("SOP Process", "create"):
		frappe.throw(_("You are not allowed to add a process."), frappe.PermissionError)

	if parent and not space:
		space = frappe.db.get_value("SOP Process", parent, "space")

	doc = frappe.get_doc(
		{
			"doctype": "SOP Process",
			"title": title,
			"space": space,
			"parent_process": parent,
			"sequence": frappe.utils.cint(sequence),
			"description": description,
		}
	).insert()

	return {"name": doc.name, "title": doc.title, "space": doc.space, "parent": doc.parent_process}


@frappe.whitelist()
def rename_process(name, title):
	doc = frappe.get_doc("SOP Process", name)
	doc.check_permission("write")

	doc.title = title
	doc.save()

	return {"name": doc.name, "title": doc.title}


@frappe.whitelist()
def move_process(name, parent=None):
	doc = frappe.get_doc("SOP Process", name)
	doc.check_permission("write")

	doc.parent_process = parent or None
	doc.save()

	return {"name": doc.name, "parent": doc.parent_process}


@frappe.whitelist()
def delete_process(name):
	doc = frappe.get_doc("SOP Process", name)
	doc.check_permission("delete")
	doc.delete()

	return {"deleted": name}


@frappe.whitelist()
def trail(process):
	names = list(reversed(ancestors_of(process)))
	if not names:
		return []

	titles = {
		row.name: row.title
		for row in frappe.get_all(
			"SOP Process", filters={"name": ("in", names)}, fields=["name", "title"]
		)
	}
	return [{"name": name, "title": titles.get(name, name)} for name in names]


@frappe.whitelist()
def templates():
	return [
		{"key": key, "title": value["title"], "description": value["description"]}
		for key, value in TEMPLATES.items()
	]


@frappe.whitelist()
def apply_to_space(space, template, with_drafts=0):
	if not frappe.has_permission("SOP Process", "create"):
		frappe.throw(_("You are not allowed to add processes."), frappe.PermissionError)

	return apply_template(space, template, with_drafts=frappe.utils.cint(with_drafts))


def scope_of(process):
	return [process] + descendants_of(process)
