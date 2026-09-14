# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re
from html import unescape

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
		self.collect_mentions()
		self.set_review_dates()
		self.build_search_text()

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

	def collect_mentions(self):
		found = mentions_in(self.content)
		kept = {
			(row.reference_doctype, row.reference_name): row
			for row in self.references
			if row.mention_kind == "Tag"
		}

		self.references = []

		for doctype, name, kind in found:
			if (doctype, name) in kept:
				continue

			self.append(
				"references",
				{"reference_doctype": doctype, "reference_name": name, "mention_kind": kind},
			)

		for row in kept.values():
			self.append(
				"references",
				{
					"reference_doctype": row.reference_doctype,
					"reference_name": row.reference_name,
					"mention_kind": row.mention_kind,
					"context_snippet": row.context_snippet,
				},
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
		parts.append((self._user_tags or "").replace(",", " "))

		text = " ".join(part for part in parts if part)
		self.search_text = re.sub(r"\s+", " ", text).strip()[:100000]

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


LINK_MENTION = re.compile(r'href="#mention:([^:"]+):([^"]+)"')
NODE_MENTION = re.compile(r'data-type="mention"[^>]*data-id="([^"]+)"')
LEGACY_MENTION = re.compile(r'data-doctype="([^"]+)" data-name="([^"]+)"')


def mentions_in(content):
	if not content:
		return []

	found = []

	for doctype, name in LINK_MENTION.findall(content):
		found.append((unescape(doctype), unescape(name), kind_of(doctype)))

	for name in NODE_MENTION.findall(content):
		found.append(("User", unescape(name), "Person"))

	for doctype, name in LEGACY_MENTION.findall(content):
		found.append((unescape(doctype), unescape(name), kind_of(doctype)))

	seen = []
	for row in found:
		if row not in seen:
			seen.append(row)

	return seen


def kind_of(doctype):
	return "Person" if doctype == "User" else "Record"


def next_number(space):
	if not space:
		frappe.throw(_("Pick a space before saving — the procedure number comes from it."))

	code = frappe.db.get_value("SOP Space", space, "space_code") or "GEN"
	code = re.sub(r"[^A-Z0-9-]", "", code.upper()) or "GEN"

	return make_autoname(f"SOP-{code}-.####")
