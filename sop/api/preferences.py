# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe

DEFAULTS = {
	"autosave": 1,
	"shortcuts": 1,
	"rows_per_page": 20,
	"email_on_approval": 1,
	"email_on_publish": 1,
	"email_on_training": 1,
	"digest": "Weekly",
}

DIGESTS = ("Off", "Weekly", "Monthly")


@frappe.whitelist()
def get(user=None):
	return shape(record(user or frappe.session.user))


@frappe.whitelist()
def save(**values):
	doc = record(frappe.session.user)

	for key in DEFAULTS:
		if key in values:
			doc.set(key, clean(key, values[key]))

	doc.save(ignore_permissions=True)

	return shape(doc)


def record(user):
	name = frappe.db.get_value("SOP User Preference", {"user": user}, "name")
	if name:
		return frappe.get_doc("SOP User Preference", name)

	return frappe.get_doc(dict(DEFAULTS, doctype="SOP User Preference", user=user))


def shape(doc):
	return dict({key: doc.get(key) for key in DEFAULTS}, user=doc.user)


def clean(key, value):
	if key == "digest":
		return value if value in DIGESTS else DEFAULTS[key]

	if key == "rows_per_page":
		return min(max(frappe.utils.cint(value) or DEFAULTS[key], 5), 200)

	return 1 if frappe.utils.cint(value) else 0

