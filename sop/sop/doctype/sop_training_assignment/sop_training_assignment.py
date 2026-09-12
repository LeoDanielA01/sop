# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now_datetime, nowdate

OPEN_STATES = ("Assigned", "In Progress", "Overdue")


class SOPTrainingAssignment(Document):
	def validate(self):
		self.set_progress()
		self.set_status()
		self.validate_outcome()

	def set_progress(self):
		if not self.tasks:
			self.progress = 100 if self.outcome and self.outcome != "Pending" else 0
			return

		done = len([row for row in self.tasks if row.completed])
		self.progress = flt(done * 100 / len(self.tasks), 2)

	def set_status(self):
		if self.status == "Waived":
			return

		if self.outcome in ("Competent", "Not Competent"):
			self.status = "Completed"
			self.completed_on = self.completed_on or now_datetime()
		elif self.progress >= 100:
			# Every task done but nobody has judged it yet: the assessor still owes an outcome.
			self.status = "In Progress" if self.requires_outcome() else "Completed"
		elif self.progress > 0:
			self.status = "In Progress"
		elif self.due_on and getdate(self.due_on) < getdate(nowdate()):
			self.status = "Overdue"
		else:
			self.status = "Assigned"

		if self.status in ("Assigned", "In Progress") and self.due_on:
			if getdate(self.due_on) < getdate(nowdate()):
				self.status = "Overdue"

	def requires_outcome(self):
		return bool(self.requires_assessment or self.method in ("Classroom", "On the Job", "Assessment"))

	def validate_outcome(self):
		if self.outcome in (None, "", "Pending"):
			return

		if self.requires_assessment and self.outcome == "Competent":
			if flt(self.score) < flt(self.pass_mark):
				frappe.throw(
					_("{0} scored {1}%, below the pass mark of {2}%.").format(
						self.trainee, flt(self.score), flt(self.pass_mark)
					)
				)

	def complete_task(self, idx, user=None):
		user = user or frappe.session.user
		for row in self.tasks:
			if row.idx != idx:
				continue

			if row.verified_by and row.verified_by != user:
				frappe.throw(_("Task {0} has to be signed off by {1}.").format(row.idx, row.verified_by))

			row.completed = 1
			row.completed_on = now_datetime()
			row.completed_by = user

		self.save(ignore_permissions=True)
		return self.status
