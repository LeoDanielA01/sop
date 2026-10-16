# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet


class SOPResource(NestedSet):
	nsm_parent_field = "parent_sop_resource"

	def validate(self):
		self.check_parent()
		self.sync_values()
		self.check_requires()

	def on_update(self):
		super().on_update()
		frappe.cache().delete_keys("sop:mention")

	def check_parent(self):
		if not self.parent_sop_resource:
			return

		parent_type = frappe.db.get_value("SOP Resource", self.parent_sop_resource, "resource_type")
		if parent_type != self.resource_type:
			frappe.throw(
				_("{0} is a {1}, so it can't be the parent of a {2}.").format(
					frappe.bold(self.parent_sop_resource), parent_type, self.resource_type
				)
			)

	def sync_values(self):
		"""One row per detail on the type, in the type's order, keeping values already entered."""
		attributes = frappe.get_all(
			"SOP Resource Attribute",
			filters={"parent": self.resource_type, "parenttype": "SOP Resource Type"},
			fields=["label", "fieldtype", "options"],
			order_by="idx asc",
		)
		entered = {(row.attribute or "").strip().lower(): row.value for row in self.get("values") or []}

		self.set("values", [])
		for attribute in attributes:
			value = entered.get(attribute.label.strip().lower())
			if attribute.fieldtype == "Select" and value:
				choices = [choice.strip() for choice in (attribute.options or "").split("\n") if choice.strip()]
				if value not in choices:
					frappe.throw(
						_("{0} must be one of: {1}.").format(frappe.bold(attribute.label), ", ".join(choices))
					)

			self.append("values", {"attribute": attribute.label, "value": value})

	def check_requires(self):
		for row in self.get("requires") or []:
			if row.resource == self.name:
				frappe.throw(_("A resource can't require itself."))
