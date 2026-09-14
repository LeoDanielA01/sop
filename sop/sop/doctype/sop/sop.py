# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import add_months, cint, getdate, strip_html

EDITABLE_STATES = ("Draft", "In Review", "Under Revision")


class SOP(Document):
	def autoname(self):
		self.sop_no = self.sop_no or next_number(self.space)
		self.name = self.sop_no

	def validate(self):
		self.validate_process()
		self.set_review_dates()
		self.build_search_text()
		self.validate_steps()

	def validate_process(self):
		if not self.sop_process:
			return

		space = frappe.db.get_value("SOP Process", self.sop_process, "space")
		if space and space != self.space:
			frappe.throw(
				_("{0} is a process of another space. Pick one from {1}.").format(
					frappe.bold(self.sop_process), frappe.bold(self.space)
				)
			)

	def set_review_dates(self):
		if not self.review_interval_months:
			self.review_interval_months = cint(
				frappe.db.get_value("SOP Space", self.space, "review_interval_months")
			) or 12

		if self.effective_from:
			self.review_due = add_months(getdate(self.effective_from), cint(self.review_interval_months))
		else:
			self.review_due = None

	def build_search_text(self):
		parts = [self.sop_no, self.title, self.summary, strip_html(self.content or "")]
		parts += [strip_html(row.instruction or "") for row in self.steps]
		parts += [row.tag for row in self.tags]

		text = " ".join(part for part in parts if part)
		self.search_text = re.sub(r"\s+", " ", text).strip()[:100000]

	def validate_steps(self):
		for idx, row in enumerate(self.steps, start=1):
			row.step_no = idx

	def is_editable(self):
		return self.status in EDITABLE_STATES

	def effective_revision(self):
		if not self.version:
			return None

		return frappe.db.get_value(
			"SOP Revision",
			{"sop": self.name, "version": self.version},
			["name", "version", "content", "effective_from", "approved_by", "approved_on"],
			as_dict=True,
		)


def next_number(space):
	if not space:
		frappe.throw(_("Pick a space before saving — the procedure number comes from it."))

	code = frappe.db.get_value("SOP Space", space, "space_code") or "GEN"
	code = re.sub(r"[^A-Z0-9-]", "", code.upper()) or "GEN"

	return make_autoname(f"SOP-{code}-.####")
