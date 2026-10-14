# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model import no_value_fields, table_fields
from frappe.utils import cint

PROFILES = {
	"General": {
		"allow_permanent_delete": 1,
		"show_week_numbers": 0,
	},
	"Public sector": {
		"allow_permanent_delete": 0,
		"show_week_numbers": 0,
	},
}

FIELDS = (
	"profile",
	"writing_language",
	"allow_permanent_delete",
	"show_week_numbers",
	"use_procedure_template",
	"intermediate_from",
	"expert_from",
	"job_card_check",
)
INT_FIELDS = (
	"allow_permanent_delete",
	"show_week_numbers",
	"use_procedure_template",
	"intermediate_from",
	"expert_from",
)
DEFAULTS = {
	"profile": "General",
	"writing_language": "",
	"use_procedure_template": 1,
	"intermediate_from": 4,
	"expert_from": 7,
	"job_card_check": "Off",
}

STANDARD_LAYOUT = """<h2>Purpose</h2><p>Why this procedure exists and what goes wrong without it.</p>
<h2>Scope</h2><p>Where, to which products and to whom it applies.</p>
<h2>Responsibilities</h2><ul><li><p><strong>Role</strong> — what they do</p></li></ul>
<h2>Safety and PPE</h2><p>Mention each chemical and piece of PPE with # so the Safety box fills itself.</p>
<h2>Materials and tools</h2><ul><li><p></p></li></ul>
<h2>Steps</h2><ol><li><p><strong>What is done</strong> — responsible: role · location: room</p></li></ol>
<h2>Records</h2><p>What is filled in, signed or kept, and where.</p>
<h2>References</h2><p>Related procedures, forms and documents.</p>"""


def settings():
	values = {**DEFAULTS, **PROFILES["General"]}

	if frappe.db.exists("DocType", "SOP Settings"):
		stored = frappe.db.get_singles_dict("SOP Settings") or {}
		for field in FIELDS:
			if stored.get(field) not in (None, ""):
				values[field] = stored.get(field)

	for field in INT_FIELDS:
		values[field] = cint(values[field])

	return frappe._dict(values)


def has_erpnext():
	return "erpnext" in frappe.get_installed_apps()


@frappe.whitelist()
def authoring():
	layout = None
	if settings().use_procedure_template:
		layout = frappe.db.get_single_value("SOP Settings", "procedure_template") or STANDARD_LAYOUT

	return {
		"layout": layout,
		"erpnext": has_erpnext(),
		"record_types": [
			{"doctype": row.reference_doctype, "label": row.label or row.reference_doctype, "icon": row.icon}
			for row in record_types()
			if frappe.db.exists("DocType", row.reference_doctype)
			and frappe.has_permission(row.reference_doctype, "read")
		],
	}


def writing_language():
	language = (
		settings().writing_language
		or frappe.db.get_value("User", frappe.session.user, "language")
		or frappe.local.lang
		or "en"
	)

	return language.split("-")[0].lower()


def resolved():
	current = settings()

	return {
		"writing_language": writing_language(),
		"week_numbers": bool(current.show_week_numbers),
		"allow_permanent_delete": bool(current.allow_permanent_delete),
	}


RECORD_TYPE_FIELDS = ("reference_doctype", "label", "icon", "fields_to_show", "in_safety")


def record_types():
	if "sop_record_types" not in frappe.local.cache:
		frappe.local.cache["sop_record_types"] = (
			frappe.get_all(
				"SOP Record Type",
				filters={"parent": "SOP Settings", "parenttype": "SOP Settings"},
				fields=list(RECORD_TYPE_FIELDS),
				order_by="idx asc",
			)
			if frappe.db.exists("DocType", "SOP Record Type")
			else []
		)

	return frappe.local.cache["sop_record_types"]


def record_type(doctype):
	return next((row for row in record_types() if row.reference_doctype == doctype), None)


def field_names(row):
	return [name.strip() for name in re.split(r"[\n,]", (row and row.fields_to_show) or "") if name.strip()]


@frappe.whitelist()
def fields_of(doctype):
	ensure_manager()
	if not frappe.db.exists("DocType", doctype):
		return []

	return [
		{
			"value": df.fieldname,
			"label": _(df.label or frappe.unscrub(df.fieldname)),
			"fieldtype": df.fieldtype,
		}
		for df in frappe.get_meta(doctype).fields
		if df.fieldtype not in no_value_fields and df.fieldtype not in table_fields and not df.hidden
	]


def save_record_types(doc, rows):
	doc.set("record_types", [])
	seen = set()
	for row in rows or []:
		doctype = (row.get("reference_doctype") or "").strip()
		if not doctype or doctype in seen:
			continue
		if not frappe.db.exists("DocType", doctype):
			frappe.throw(_("{0} is not a record type on this site.").format(doctype))

		seen.add(doctype)
		fields = row.get("fields_to_show")
		doc.append(
			"record_types",
			{
				"reference_doctype": doctype,
				"label": row.get("label"),
				"icon": row.get("icon"),
				"fields_to_show": "\n".join(fields) if isinstance(fields, list) else fields,
				"in_safety": cint(row.get("in_safety")),
			},
		)
	frappe.local.cache.pop("sop_record_types", None)


def ensure_manager():
	if not {"SOP Manager", "System Manager"} & set(frappe.get_roles()):
		frappe.throw(_("Only an SOP manager can change organisation settings."), frappe.PermissionError)


@frappe.whitelist()
def get():
	from sop.api.i18n import languages

	return {
		**settings(),
		"profiles": list(PROFILES),
		"languages": languages(),
		"resolved": resolved(),
		"erpnext": has_erpnext(),
		"record_types": [{**row, "fields_to_show": field_names(row)} for row in record_types()],
	}


@frappe.whitelist()
def save(values):
	ensure_manager()

	if isinstance(values, str):
		values = frappe.parse_json(values)

	doc = frappe.get_doc("SOP Settings")
	for field in FIELDS:
		if field in (values or {}):
			doc.set(field, values[field] or None if field == "writing_language" else values[field])

	if "record_types" in (values or {}):
		save_record_types(doc, values["record_types"])

	intermediate = cint(doc.intermediate_from or DEFAULTS["intermediate_from"])
	expert = cint(doc.expert_from or DEFAULTS["expert_from"])
	if intermediate < 1 or expert <= intermediate:
		frappe.throw(
			_("Expert has to need more completed trainings than Intermediate, and both at least one.")
		)

	doc.save(ignore_permissions=True)

	return get()


@frappe.whitelist()
def apply_profile(profile):
	ensure_manager()

	if profile not in PROFILES:
		frappe.throw(_("{0} is not a profile.").format(profile))

	doc = frappe.get_doc("SOP Settings")
	doc.update({"profile": profile, **PROFILES[profile]})
	doc.save(ignore_permissions=True)

	return get()
