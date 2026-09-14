# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

ALLOWED = re.compile(r"^[A-Z0-9-]{1,10}$")


class SOPSpace(Document):
	def validate(self):
		self.validate_code()

	def validate_code(self):
		code = (self.space_code or "").strip().upper()

		if not ALLOWED.match(code):
			frappe.throw(
				_(
					"{0} cannot be a space code. Use up to 10 letters, digits or dashes — the code becomes part of every procedure number, like SOP-{1}-0001."
				).format(frappe.bold(self.space_code or ""), "QA")
			)

		self.space_code = code
