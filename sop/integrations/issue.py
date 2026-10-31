# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

"""Issue any resource whose type can be issued: consumables come out of stock,
anything a person keeps is handed over as an asset."""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from sop.api.mentions import record_url
from sop.integrations.erpnext import ensure
from sop.resources import DOCTYPE, TYPE_DOCTYPE


@frappe.whitelist()
def choices():
	ensure()
	issuable = frappe.get_all(TYPE_DOCTYPE, filters={"can_be_issued": 1}, fields=["name", "icon"], order_by="name asc")
	fields = ["name", "resource_type", "is_consumable"]
	if frappe.get_meta(DOCTYPE).has_field("item"):
		fields.append("item")

	resources = (
		frappe.get_list(
			DOCTYPE,
			filters={"is_group": 0, "disabled": 0, "resource_type": ("in", [row.name for row in issuable])},
			fields=fields,
			order_by="resource_type asc, lft asc",
			limit_page_length=0,
		)
		if issuable
		else []
	)

	return {
		"types": issuable,
		"resources": resources,
		"warehouses": frappe.get_list(
			"Warehouse", filters={"is_group": 0, "disabled": 0}, pluck="name", limit_page_length=0
		),
	}


@frappe.whitelist()
def issue(resource, employee, qty=1, warehouse=None, asset=None):
	ensure()
	row = frappe.get_doc(DOCTYPE, resource)
	row.check_permission("read")
	if not frappe.db.get_value(TYPE_DOCTYPE, row.resource_type, "can_be_issued"):
		frappe.throw(_("{0} resources aren't set to be issued.").format(frappe.bold(row.resource_type)))

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
			"remarks": _("{0} {1} issued to {2} ({3})").format(
				row.resource_type, row.name, person.employee_name, person.name
			),
			"items": [{"item_code": row.item, "qty": qty, "s_warehouse": warehouse}],
		}
	)
	entry.insert()
	entry.submit()

	return {"doctype": "Stock Entry", "name": entry.name, "url": record_url("Stock Entry", entry.name)}


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
		"url": record_url("Asset Movement", movement.name),
	}
