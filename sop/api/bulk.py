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


def replace_in(html, find, replace, match_case=0, whole_word=0, only=None, start=0):
	if not html or not find:
		return html, 0, start

	rule = pattern(find, match_case, whole_word)
	seen = start
	hits = 0
	out = []

	def swap_one(match):
		nonlocal seen, hits

		index = seen
		seen += 1

		if only is not None and index not in only:
			return match.group(0)

		hits += 1
		return replace or ""

	for index, chunk in enumerate(TAG.split(html)):
		if index % 2:
			out.append(chunk)
			continue

		out.append(rule.sub(swap_one, chunk))

	return "".join(out), hits, seen


def count_in(html, find, match_case=0, whole_word=0):
	return replace_in(html, find, find, match_case, whole_word)[1]


def occurrences(html, find, match_case=0, whole_word=0, start=0, limit=25):
	text = re.sub(r"\s+", " ", TAG.sub(" ", html or "")).strip()
	if not text:
		return [], start

	rule = pattern(find, match_case, whole_word)
	found = []
	index = start

	for match in rule.finditer(text):
		if len(found) < limit:
			left = max(0, match.start() - 45)
			right = min(len(text), match.end() + 45)

			found.append(
				{
					"index": index,
					"before": ("…" if left else "") + text[left : match.start()],
					"hit": match.group(0),
					"after": text[match.end() : right] + ("…" if right < len(text) else ""),
				}
			)

		index += 1

	return found, index


@frappe.whitelist()
def preview(find, replace=None, space=None, match_case=0, whole_word=0, limit=100):
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
		matches = []
		seen = 0

		for text in (row.title, row.summary, row.content):
			found, seen = occurrences(text, find, match_case, whole_word, seen)
			matches += found

		if not seen:
			continue

		out.append(
			{
				"name": row.name,
				"sop_no": row.sop_no,
				"title": row.title,
				"status": row.status,
				"hits": seen,
				"editable": row.status in EDITABLE,
				"matches": matches,
			}
		)

	return out


LOCK = "sop:bulk-replace"
LOCK_TTL = 300


def holder():
	return frappe.cache().get_value(LOCK)


@frappe.whitelist()
def claim():
	current = holder()

	if current and current != frappe.session.user:
		frappe.throw(
			_("{0} is running a replace right now. Wait until it finishes.").format(current),
			frappe.ValidationError,
		)

	frappe.cache().set_value(LOCK, frappe.session.user, expires_in_sec=LOCK_TTL)

	return {"holder": frappe.session.user}


@frappe.whitelist()
def release():
	if holder() == frappe.session.user:
		frappe.cache().delete_value(LOCK)

	return {"holder": holder()}


@frappe.whitelist()
def busy():
	current = holder()

	return {"busy": bool(current and current != frappe.session.user), "holder": current}


@frappe.whitelist()
def apply(find, replace, names, match_case=0, whole_word=0, start_revision=0, picks=None):
	find = (find or "").strip()
	if not find:
		frappe.throw(_("Nothing to find."))

	if isinstance(names, str):
		names = frappe.parse_json(names)

	if isinstance(picks, str):
		picks = frappe.parse_json(picks)

	match_case = frappe.utils.cint(match_case)
	whole_word = frappe.utils.cint(whole_word)
	start_revision = frappe.utils.cint(start_revision)
	picks = picks or {}

	current = holder()
	if current and current != frappe.session.user:
		frappe.throw(
			_("{0} is running a replace right now.").format(current), frappe.ValidationError
		)

	frappe.cache().set_value(LOCK, frappe.session.user, expires_in_sec=LOCK_TTL)

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

		wanted = picks.get(name)
		only = set(wanted) if wanted is not None else None

		hits = 0
		seen = 0

		doc.title, found, seen = replace_in(
			doc.title, find, replace, match_case, whole_word, only, seen
		)
		hits += found

		doc.summary, found, seen = replace_in(
			doc.summary, find, replace, match_case, whole_word, only, seen
		)
		hits += found

		doc.content, found, seen = replace_in(
			doc.content, find, replace, match_case, whole_word, only, seen
		)
		hits += found

		for step in doc.steps:
			step.instruction, found, seen = replace_in(
				step.instruction, find, replace, match_case, whole_word, only, seen
			)
			hits += found

		if not hits:
			continue

		doc.save()
		changed.append({"name": name, "sop_no": doc.sop_no, "hits": hits})

	frappe.db.commit()

	return {"changed": changed, "skipped": skipped}
