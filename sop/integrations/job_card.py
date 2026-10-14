# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from sop.api.settings import settings
from sop.proficiency import level, rank


def check_qualification(doc, method=None):
	mode = settings().job_card_check
	if mode == "Off" or not doc.get("operation"):
		return

	sop, minimum = frappe.db.get_value("Operation", doc.operation, ["sop", "sop_min_tier"]) or (None, None)
	if not sop or not minimum:
		return

	employees = sorted(
		{
			row.employee
			for row in (doc.get("employee") or []) + (doc.get("time_logs") or [])
			if row.get("employee")
		}
	)

	short = []
	for employee in employees:
		name, user = frappe.db.get_value("Employee", employee, ["employee_name", "user_id"]) or (
			employee,
			None,
		)
		if not user:
			short.append(
				_("{0} has no user account, so their training can't be checked").format(name or employee)
			)
			continue

		found = level(user, sop)
		if rank(found["tier"]) < rank(minimum):
			short.append(
				_("{0} is {1} ({2} completed trainings)").format(
					name or employee, found["tier"], found["completions"]
				)
			)

	if not short:
		return

	message = _("Procedure {0} needs {1} or above:").format(frappe.bold(sop), frappe.bold(minimum))
	message += "<br>" + "<br>".join(short)

	if mode == "Block":
		frappe.throw(message, title=_("Not qualified"))

	frappe.msgprint(message, title=_("Check qualification"), indicator="orange")
