# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SOPLogEntry(Document):
	def after_insert(self):
		if self.location and self.room_status:
			frappe.db.set_value(
				"SOP Resource",
				self.location,
				{
					"room_status": self.room_status,
					"room_status_on": self.logged_at,
					"room_status_by": self.done_by,
				},
			)
