# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
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

FIELDS = ("profile", "writing_language", "allow_permanent_delete", "show_week_numbers")


def settings():
	values = {"profile": "General", "writing_language": "", **PROFILES["General"]}

	if frappe.db.exists("DocType", "SOP Settings"):
		stored = frappe.db.get_singles_dict("SOP Settings") or {}
		for field in FIELDS:
			if stored.get(field) not in (None, ""):
				values[field] = stored.get(field)

	values["allow_permanent_delete"] = cint(values["allow_permanent_delete"])
	values["show_week_numbers"] = cint(values["show_week_numbers"])

	return frappe._dict(values)


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
