# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, get_url_to_form, now_datetime

from sop.integrations.erpnext import ensure


@frappe.whitelist()
def choices():
	ensure()
	return {
		"ppe": frappe.get_list(
			"SOP PPE",
			filters={"is_group": 0},
			fields=["name", "is_consumable", "item", "standard"],
			order_by="lft asc",
			limit_page_length=0,
		),
		"warehouses": frappe.get_list(
			"Warehouse", filters={"is_group": 0, "disabled": 0}, pluck="name", limit_page_length=0
		),
	}


@frappe.whitelist()
def issue(ppe, employee, qty=1, warehouse=None, asset=None):
	ensure()
	row = frappe.get_doc("SOP PPE", ppe)
	person = frappe.get_doc("Employee", employee)
	person.check_permission("read")

	if row.is_consumable:
		return issue_from_stock(row, person, flt(qty), warehouse)

	return hand_over_asset(row, person, asset)


def issue_from_stock(row, person, qty, warehouse):
	if not row.get("item"):
		frappe.throw(_("Set the Stock Item on {0} before issuing it.").format(frappe.bold(row.name)))
	if not warehouse:
		frappe.throw(_("Pick the warehouse to issue {0} from.").format(frappe.bold(row.name)))
	if qty <= 0:
		frappe.throw(_("Issue at least one."))

	entry = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Issue",
			"purpose": "Material Issue",
			"company": person.company,
			"remarks": _("PPE {0} issued to {1} ({2})").format(row.name, person.employee_name, person.name),
			"items": [{"item_code": row.item, "qty": qty, "s_warehouse": warehouse}],
		}
	)
	entry.insert()
	entry.submit()

	return {"doctype": "Stock Entry", "name": entry.name, "url": get_url_to_form("Stock Entry", entry.name)}


def hand_over_asset(row, person, asset):
	if not asset:
		frappe.throw(
			_("{0} is kept by one person, so pick the asset to hand over.").format(frappe.bold(row.name))
		)

	movement = frappe.get_doc(
		{
			"doctype": "Asset Movement",
			"purpose": "Issue",
			"company": person.company,
			"transaction_date": now_datetime(),
			"assets": [
				{
					"asset": asset,
					"source_location": frappe.db.get_value("Asset", asset, "location"),
					"to_employee": person.name,
				}
			],
		}
	)
	movement.insert()
	movement.submit()

	return {
		"doctype": "Asset Movement",
		"name": movement.name,
		"url": get_url_to_form("Asset Movement", movement.name),
	}
