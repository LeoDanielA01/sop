# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

"""Generic resources: any business defines its own types (Chemical, PPE, Tool, Hazard...)
with their own details, and procedures mention the resources like any other record."""

import frappe
from frappe import _
from frappe.utils import cint

DOCTYPE = "SOP Resource"
TYPE_DOCTYPE = "SOP Resource Type"


def installed():
	return bool(frappe.db.exists("DocType", DOCTYPE))


def settings_of(resource_type):
	"""Type settings, cached for the request."""
	cache = frappe.local.cache.setdefault("sop_resource_types", {})
	if resource_type not in cache:
		row = frappe.db.get_value(
			TYPE_DOCTYPE,
			resource_type,
			["name", "icon", "is_tree", "show_in_procedure", "can_be_issued", "document_label", "review_label"],
			as_dict=True,
		)
		if row:
			row.attributes = frappe.get_all(
				"SOP Resource Attribute",
				filters={"parent": resource_type, "parenttype": TYPE_DOCTYPE},
				fields=["label", "fieldtype", "options", "show_in_procedure"],
				order_by="idx asc",
			)
		cache[resource_type] = row

	return cache[resource_type]


@frappe.whitelist()
def type_settings(resource_type):
	frappe.has_permission(TYPE_DOCTYPE, "read", throw=True)
	return settings_of(resource_type) or {}


@frappe.whitelist()
def nav_types():
	"""Resource types for the sidebar, with how many resources each has."""
	if not installed() or not frappe.has_permission(DOCTYPE, "read"):
		return []

	counts = dict(
		frappe.db.sql(
			f"""select resource_type, count(*) from `tab{DOCTYPE}`
			where is_group = 0 and disabled = 0 group by resource_type"""
		)
	)
	return [
		{"name": row.name, "icon": row.icon, "is_tree": cint(row.is_tree), "count": counts.get(row.name, 0)}
		for row in frappe.get_all(TYPE_DOCTYPE, fields=["name", "icon", "is_tree"], order_by="name asc")
	]


def facts(name):
	"""Card lines for a resource: its type's details, document, review date and requirements."""
	from sop.api.mentions import deadline_fact

	row = frappe.db.get_value(
		DOCTYPE, name, ["name", "resource_type", "document", "check_date"], as_dict=True
	)
	if not row:
		return []

	settings = settings_of(row.resource_type) or frappe._dict(attributes=[])
	shown = {attribute.label: attribute for attribute in settings.attributes if cint(attribute.show_in_procedure)}
	out = []

	values = frappe.get_all(
		"SOP Resource Value",
		filters={"parent": name, "parenttype": DOCTYPE},
		fields=["attribute", "value"],
		order_by="idx asc",
	)
	for value in values:
		attribute = shown.get(value.attribute)
		if not attribute or value.value in (None, ""):
			continue

		if attribute.fieldtype == "Date":
			fact = deadline_fact(frappe._dict(label=attribute.label, fieldname=""), value.value)
			if fact:
				out.append(fact)
			continue

		if attribute.fieldtype == "Check":
			if not cint(value.value):
				continue
			shown_value = _("Yes")
		else:
			shown_value = value.value

		out.append({"label": attribute.label, "value": shown_value, "tone": "gray"})

	if settings.get("review_label") and row.check_date:
		fact = deadline_fact(frappe._dict(label=settings.review_label, fieldname=""), row.check_date)
		if fact:
			out.append(fact)

	if settings.get("document_label") and row.document:
		out.append({"label": settings.document_label, "value": row.document, "tone": "gray"})

	required = frappe.get_all(
		"SOP Resource Requirement",
		filters={"parent": name, "parenttype": DOCTYPE},
		pluck="resource",
		order_by="idx asc",
	)
	if required:
		out.append({"label": _("Requires"), "value": ", ".join(required), "tone": "gray"})

	return out


def resolve(doctype, names):
	"""Mention chips that carry the resource type's own icon and name."""
	from sop.api.mentions import generic

	chips = generic(doctype, names)
	types = dict(
		frappe.get_all(
			DOCTYPE,
			filters={"name": ("in", names)},
			fields=["name", "resource_type"],
			as_list=True,
		)
	)
	for chip in chips:
		resource_type = types.get(chip.get("reference_name"))
		settings = settings_of(resource_type) if resource_type else None
		if settings:
			chip["icon"] = settings.icon or chip.get("icon")
			chip["short_type"] = resource_type[:12]

	return chips


def type_label_of(name):
	return frappe.db.get_value(DOCTYPE, name, "resource_type")
