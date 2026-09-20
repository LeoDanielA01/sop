# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from sop import demo


def ensure_admin():
	if frappe.session.user == "Administrator":
		return

	if "System Manager" not in frappe.get_roles():
		frappe.throw(
			_("Only a system administrator can manage demo data."), frappe.PermissionError
		)


@frappe.whitelist()
def overview():
	ensure_admin()

	return demo.summary()


@frappe.whitelist()
def seed():
	ensure_admin()

	if demo.seeded():
		frappe.throw(_("The demo spaces already exist. Remove them first, or choose Rebuild."))

	demo.install(force=1)

	return demo.summary()


@frappe.whitelist()
def remove():
	ensure_admin()

	demo.clear()

	return demo.summary()


@frappe.whitelist()
def rebuild():
	ensure_admin()

	demo.clear()
	demo.install(force=1)

	return demo.summary()
