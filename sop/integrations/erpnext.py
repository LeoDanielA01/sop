# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from sop.api.settings import has_erpnext

CUSTOM_FIELDS = {
	"Operation": [
		{
			"fieldname": "sop_section",
			"fieldtype": "Section Break",
			"label": "Procedure",
			"insert_after": "quality_inspection_template",
		},
		{
			"fieldname": "sop",
			"fieldtype": "Link",
			"label": "Procedure",
			"options": "SOP",
			"insert_after": "sop_section",
		},
		{
			"fieldname": "sop_min_tier",
			"fieldtype": "Select",
			"label": "Minimum Proficiency",
			"options": "\nBeginner\nIntermediate\nExpert",
			"depends_on": "sop",
			"description": "Job Cards for this operation check their employees against it.",
			"insert_after": "sop",
		},
	],
	"Job Card": [
		{
			"fieldname": "sop",
			"fieldtype": "Link",
			"label": "Procedure",
			"options": "SOP",
			"fetch_from": "operation.sop",
			"read_only": 1,
			"insert_after": "operation",
		},
	],
	"SOP PPE": [
		{
			"fieldname": "item",
			"fieldtype": "Link",
			"label": "Stock Item",
			"options": "Item",
			"description": "The stock item issued for consumable PPE.",
			"insert_after": "is_consumable",
		},
	],
}


def setup():
	if has_erpnext():
		create_custom_fields(CUSTOM_FIELDS, update=True)


def ensure():
	if not has_erpnext():
		frappe.throw(_("This needs ERPNext installed on the site."))
