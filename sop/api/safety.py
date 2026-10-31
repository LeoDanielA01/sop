# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

"""The box at the top of a procedure: the records it mentions that are set to show there,
plus whatever those records require (a chemical's PPE, a machine's guarding, a room's hazards)."""

import frappe
from frappe.model import table_fields
from frappe.utils import cint

from sop.api.mentions import card, record_url, type_label
from sop.api.settings import record_types
from sop.resources import DOCTYPE as RESOURCE, settings_of

# Tree bookkeeping links, never a "requirement".
SKIP_LINKS = {"old_parent", "parent_sop_resource", "amended_from"}


@frappe.whitelist()
def for_sop(sop):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	types = {row.reference_doctype: row for row in record_types() if row.in_safety}
	if not types:
		return {"records": [], "related": []}

	mentioned = []
	for row in doc.references:
		pair = (row.reference_doctype, row.reference_name)
		if row.reference_doctype in types and pair not in mentioned and shown(*pair):
			mentioned.append(pair)

	records = []
	for doctype, name in mentioned:
		found = card(doctype, name)
		if found.get("missing") or found.get("blocked"):
			continue
		records.append(
			{**found, "type_label": label_of(doctype, name), "icon": icon_of(doctype, name, types[doctype].icon)}
		)

	return {"records": records, "related": related(mentioned, types)}


def shown(doctype, name):
	if doctype != RESOURCE:
		return True

	resource_type = frappe.db.get_value(RESOURCE, name, "resource_type")
	settings = settings_of(resource_type) if resource_type else None
	return bool(settings and cint(settings.show_in_procedure))


def label_of(doctype, name):
	if doctype == RESOURCE:
		return frappe.db.get_value(RESOURCE, name, "resource_type") or type_label(doctype)
	return type_label(doctype)


def icon_of(doctype, name, fallback=None):
	if doctype == RESOURCE:
		resource_type = frappe.db.get_value(RESOURCE, name, "resource_type")
		settings = settings_of(resource_type) if resource_type else None
		return (settings and settings.icon) or fallback
	return fallback


def related(mentioned, types):
	"""Records the mentioned ones point at, through their own link and table fields."""
	needed = {}

	for doctype, name in mentioned:
		for target_doctype, target in links_from(doctype, name, set(types)):
			if (target_doctype, target) in mentioned:
				continue
			needed.setdefault((target_doctype, target), [])
			title = frappe.db.get_value(doctype, name, frappe.get_meta(doctype).get_title_field()) or name
			if title not in needed[(target_doctype, target)]:
				needed[(target_doctype, target)].append(title)

	out = []
	for (doctype, name), sources in needed.items():
		if not frappe.db.exists(doctype, name) or not frappe.has_permission(doctype, "read", doc=name):
			continue

		meta = frappe.get_meta(doctype)
		out.append(
			{
				"doctype": doctype,
				"name": name,
				"path": trail(meta, name),
				"type_label": label_of(doctype, name),
				"icon": icon_of(doctype, name, types[doctype].icon if doctype in types else None),
				"for": sources,
				"url": record_url(doctype, name),
			}
		)

	return out


def links_from(doctype, name, targets):
	meta = frappe.get_meta(doctype)
	found = []

	for df in meta.fields:
		if df.fieldname in SKIP_LINKS:
			continue

		if df.fieldtype == "Link" and df.options in targets:
			value = frappe.db.get_value(doctype, name, df.fieldname)
			if value:
				found.append((df.options, value))

		elif df.fieldtype in table_fields and df.options:
			child = frappe.get_meta(df.options)
			for child_df in child.fields:
				if child_df.fieldtype != "Link" or child_df.options not in targets:
					continue
				for value in frappe.get_all(
					df.options,
					filters={"parent": name, "parenttype": doctype, "parentfield": df.fieldname},
					pluck=child_df.fieldname,
					order_by="idx asc",
				):
					if value:
						found.append((child_df.options, value))

	return found


def trail(meta, name):
	"""PPE › Mask › Filter for tree records, the title otherwise."""
	title_field = meta.get_title_field()

	if not meta.is_tree:
		return frappe.db.get_value(meta.name, name, title_field) or name

	row = frappe.db.get_value(meta.name, name, ["lft", "rgt"], as_dict=True)
	if not row or not row.lft:
		return name

	path = frappe.get_all(
		meta.name,
		filters={"lft": ("<=", row.lft), "rgt": (">=", row.rgt)},
		pluck=title_field if title_field != "name" else "name",
		order_by="lft asc",
	)
	return " › ".join(path or [name])
