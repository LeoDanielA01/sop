# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, nowdate

from sop.api.mentions import relative, urgency


def maintenance(name):
	if not frappe.db.exists("DocType", "Asset Maintenance Task"):
		return []

	schedules = frappe.get_all("Asset Maintenance", filters={"asset_name": name}, pluck="name")
	if not schedules:
		return []

	tasks = frappe.get_all(
		"Asset Maintenance Task",
		filters={"parenttype": "Asset Maintenance", "parent": ("in", schedules)},
		fields=["maintenance_task", "maintenance_status", "next_due_date"],
		order_by="next_due_date asc",
	)

	facts = []
	upcoming = [task for task in tasks if task.next_due_date]
	if upcoming:
		task = upcoming[0]
		days = date_diff(task.next_due_date, nowdate())
		facts.append(
			{
				"key": "next_maintenance",
				"label": _("Next maintenance"),
				"value": "{0} · {1} · {2}".format(
					task.maintenance_task,
					frappe.format_value(task.next_due_date, {"fieldtype": "Date"}),
					relative(days),
				),
				"short": _("Maintenance {0}").format(relative(days)),
				"tone": urgency(days),
				"days": days,
				"headline": True,
			}
		)

	overdue = [task.maintenance_task for task in tasks if task.maintenance_status == "Overdue"]
	if overdue:
		facts.append(
			{
				"key": "maintenance_overdue",
				"label": _("Maintenance overdue"),
				"value": ", ".join(overdue),
				"short": _("Maintenance overdue"),
				"tone": "red",
			}
		)

	return facts
