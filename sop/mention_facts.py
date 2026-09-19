# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, flt, nowdate

from sop.api.mentions import relative, urgency


def quantity(value):
	return frappe.format_value(flt(value), {"fieldtype": "Float"})


def item(name):
	if not frappe.db.exists("DocType", "Bin"):
		return []

	uom = frappe.db.get_value("Item", name, "stock_uom") or ""
	bins = frappe.get_all(
		"Bin",
		filters={"item_code": name},
		fields=["warehouse", "actual_qty", "projected_qty"],
		limit_page_length=0,
	)

	facts = []

	if bins:
		stock = sum(flt(row.actual_qty) for row in bins)
		projected = sum(flt(row.projected_qty) for row in bins)
		places = len([row for row in bins if flt(row.actual_qty)])

		facts.append(
			{
				"key": "stock",
				"label": _("In stock"),
				"amount": stock,
				"value": _("{0} {1} in {2} warehouses").format(quantity(stock), uom, places),
				"short": _("{0} {1} in stock").format(quantity(stock), uom),
				"tone": "red" if stock <= 0 else "gray",
				"headline": True,
			}
		)

		if flt(projected) != flt(stock):
			facts.append(
				{
					"key": "projected",
					"label": _("Projected"),
					"value": f"{quantity(projected)} {uom}",
					"tone": "gray",
					"amount": projected,
				}
			)

	return facts + nearest_batch(name)


def nearest_batch(name):
	if not frappe.db.exists("DocType", "Batch"):
		return []

	rows = frappe.get_all(
		"Batch",
		filters={"item": name, "disabled": 0, "expiry_date": ("is", "set"), "batch_qty": (">", 0)},
		fields=["name", "expiry_date", "batch_qty"],
		order_by="expiry_date asc",
		limit_page_length=1,
	)
	if not rows:
		return []

	batch = rows[0]
	days = date_diff(batch.expiry_date, nowdate())

	return [
		{
			"key": "batch_expiry",
			"label": _("Next batch expiry"),
			"value": _("{0} · {1} · {2} left").format(
				frappe.format_value(batch.expiry_date, {"fieldtype": "Date"}),
				batch.name,
				quantity(batch.batch_qty),
			),
			"short": _("Batch expires {0}").format(relative(days)),
			"tone": urgency(days),
			"days": days,
		}
	]


def warehouse(name):
	if not frappe.db.exists("DocType", "Bin"):
		return []

	stocked = frappe.db.count("Bin", {"warehouse": name, "actual_qty": (">", 0)})

	return [
		{
			"key": "items_in_stock",
			"label": _("Items in stock"),
			"amount": stocked,
			"value": str(stocked),
			"short": _("{0} items in stock").format(stocked),
			"tone": "gray",
			"headline": True,
		}
	]
