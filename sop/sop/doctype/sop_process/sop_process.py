# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SOPProcess(Document):
	def autoname(self):
		self.name = next_name(self.space, self.title)

	def validate(self):
		self.validate_parent()

	def validate_parent(self):
		if not self.parent_process:
			return

		if self.parent_process == self.name:
			frappe.throw(_("A process cannot sit inside itself."))

		parent = frappe.db.get_value(
			"SOP Process", self.parent_process, ["space", "parent_process"], as_dict=True
		)
		if not parent:
			return

		if parent.space != self.space:
			frappe.throw(_("{0} belongs to another space.").format(self.parent_process))

		if self.name in ancestors_of(self.parent_process):
			frappe.throw(_("That would put {0} inside one of its own steps.").format(self.title))

	def on_trash(self):
		if frappe.db.exists("SOP Process", {"parent_process": self.name}):
			frappe.throw(_("Move or delete the steps inside {0} first.").format(self.title))

		if frappe.db.exists("SOP", {"process": self.name}):
			frappe.throw(_("Procedures still sit in {0}.").format(self.title))


def next_name(space, title):
	code = frappe.db.get_value("SOP Space", space, "space_code") or "GEN"
	base = f"{code}-{frappe.scrub(title).replace('_', '-')}"[:120]

	name = base
	suffix = 1
	while frappe.db.exists("SOP Process", name):
		suffix += 1
		name = f"{base}-{suffix}"

	return name


def ancestors_of(process):
	seen = []
	current = process

	while current and current not in seen:
		seen.append(current)
		current = frappe.db.get_value("SOP Process", current, "parent_process")

	return seen


def descendants_of(process):
	found = []
	frontier = [process]

	while frontier:
		children = frappe.get_all(
			"SOP Process",
			filters={"parent_process": ("in", frontier)},
			pluck="name",
			limit_page_length=0,
		)
		children = [row for row in children if row not in found and row != process]
		if not children:
			break

		found += children
		frontier = children

	return found
