# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _

TAG = re.compile(r"(<[^>]*>)")
EDITABLE = ("Draft", "Under Revision")


def pattern(find, match_case=0, whole_word=0):
	text = re.escape(find)
	if whole_word:
		text = rf"\b{text}\b"

	return re.compile(text, 0 if match_case else re.IGNORECASE)


def replace_in(html, find, replace, match_case=0, whole_word=0):
	if not html or not find:
		return html, 0

	rule = pattern(find, match_case, whole_word)
	hits = 0
	out = []

	for index, chunk in enumerate(TAG.split(html)):
		if index % 2:
			out.append(chunk)
			continue

		chunk, found = rule.subn(replace or "", chunk)
		hits += found
		out.append(chunk)

	return "".join(out), hits


def count_in(html, find, match_case=0, whole_word=0):
	return replace_in(html, find, find, match_case, whole_word)[1]


def snippet_of(html, find, match_case=0, whole_word=0):
	text = re.sub(r"\s+", " ", TAG.sub(" ", html or "")).strip()
	match = pattern(find, match_case, whole_word).search(text)
	if not match:
		return ""

	start = max(0, match.start() - 40)
	end = min(len(text), match.end() + 40)

	return ("…" if start else "") + text[start:end].strip() + ("…" if end < len(text) else "")


@frappe.whitelist()
def preview(find, space=None, match_case=0, whole_word=0, limit=100):
	find = (find or "").strip()
	if not find:
		return []

	match_case = frappe.utils.cint(match_case)
	whole_word = frappe.utils.cint(whole_word)

	filters = {"space": space} if space else {}
	rows = frappe.get_list(
		"SOP",
		filters=filters,
		fields=["name", "sop_no", "title", "summary", "status", "content"],
		order_by="sop_no asc",
		limit_page_length=frappe.utils.cint(limit) or 100,
	)

	out = []
	for row in rows:
		hits = sum(
			count_in(text, find, match_case, whole_word)
			for text in (row.content, row.title, row.summary)
		)
		if not hits:
			continue

		out.append(
			{
				"name": row.name,
				"sop_no": row.sop_no,
				"title": row.title,
				"status": row.status,
				"hits": hits,
				"editable": row.status in EDITABLE,
				"snippet": snippet_of(row.content, find, match_case, whole_word),
			}
		)

	return out


@frappe.whitelist()
def apply(find, replace, names, match_case=0, whole_word=0, start_revision=0):
	find = (find or "").strip()
	if not find:
		frappe.throw(_("Nothing to find."))

	if isinstance(names, str):
		names = frappe.parse_json(names)

	match_case = frappe.utils.cint(match_case)
	whole_word = frappe.utils.cint(whole_word)
	start_revision = frappe.utils.cint(start_revision)

	changed = []
	skipped = []

	for name in names or []:
		doc = frappe.get_doc("SOP", name)
		doc.check_permission("write")

		if doc.status not in EDITABLE:
			if not start_revision or doc.status != "Effective":
				skipped.append({"name": name, "status": doc.status, "sop_no": doc.sop_no})
				continue

			from sop.api.lifecycle import start_revision as begin

			begin(name)
			doc = frappe.get_doc("SOP", name)

		hits = 0

		doc.content, found = replace_in(doc.content, find, replace, match_case, whole_word)
		hits += found

		doc.title, found = replace_in(doc.title, find, replace, match_case, whole_word)
		hits += found

		doc.summary, found = replace_in(doc.summary, find, replace, match_case, whole_word)
		hits += found

		for step in doc.steps:
			step.instruction, found = replace_in(
				step.instruction, find, replace, match_case, whole_word
			)
			hits += found

		if not hits:
			continue

		doc.save()
		changed.append({"name": name, "sop_no": doc.sop_no, "hits": hits})

	frappe.db.commit()

	return {"changed": changed, "skipped": skipped}
