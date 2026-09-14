# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.translate import get_all_translations


@frappe.whitelist()
def languages():
	rows = frappe.get_all(
		"Language",
		filters={"enabled": 1},
		fields=["name", "language_name"],
		order_by="language_name asc",
		limit_page_length=0,
	)

	return [{"value": row.name, "label": row.language_name or row.name} for row in rows]


@frappe.whitelist()
def current():
	return frappe.db.get_value("User", frappe.session.user, "language") or frappe.local.lang or "en"


@frappe.whitelist()
def set_language(language):
	if language and not frappe.db.exists("Language", language):
		frappe.throw(_("{0} is not a language on this site.").format(language))

	frappe.db.set_value("User", frappe.session.user, "language", language or None)
	frappe.local.lang = language or "en"

	return {"language": language}


@frappe.whitelist()
def translations(language=None):
	return get_all_translations(language or current())
