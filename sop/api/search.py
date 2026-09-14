# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _

LIMIT = 8


@frappe.whitelist()
def query(text, space=None, limit=LIMIT):
	text = (text or "").strip()
	if not text:
		return {"groups": []}

	limit = frappe.utils.cint(limit) or LIMIT
	groups = []

	procedures = find_procedures(text, space, limit)
	if procedures:
		groups.append({"title": _("Procedures"), "items": procedures})

	mentions = find_by_mention(text, space, limit)
	if mentions:
		groups.append({"title": _("Mentions this record"), "items": mentions})

	spaces = find_spaces(text)
	if spaces:
		groups.append({"title": _("Spaces"), "items": spaces})

	return {"groups": groups}


def find_procedures(text, space=None, limit=LIMIT):
	rows = full_text(text, space, limit)
	if rows is not None:
		return rows

	return by_like(text, space, limit)


def full_text(text, space=None, limit=LIMIT):
	from sop.sop.doctype.sop.sop_sqlite_search import SOPSQLiteSearch, readable

	search = SOPSQLiteSearch()
	if not (search.is_search_enabled() and search.index_exists()):
		return None

	try:
		hits = search.search(text, filters={"space": space} if space else None)
	except Exception:
		frappe.log_error(title="SOP search index unavailable")
		return None

	rows = readable(hits.get("results", []))[:limit]

	return [
		procedure_item(
			frappe._dict(
				name=row.get("name"),
				sop_no=row.get("sop_no"),
				title=row.get("title"),
				summary=snippet(row.get("content")),
				status=row.get("status"),
				version=row.get("version"),
				space=row.get("space"),
			)
		)
		for row in rows
	]


def snippet(content, length=120):
	text = (content or "").strip()

	return text[:length] + ("…" if len(text) > length else "")


def by_like(text, space=None, limit=LIMIT):
	like = f"%{text}%"
	filters = {"space": space} if space else {}

	seen = {}
	for clause in ("sop_no", "title", "search_text"):
		rows = frappe.get_list(
			"SOP",
			filters=dict(filters, **{clause: ("like", like)}),
			fields=["name", "sop_no", "title", "summary", "status", "version", "space"],
			order_by="modified desc",
			limit_page_length=limit,
		)
		for row in rows:
			seen.setdefault(row.name, row)

		if len(seen) >= limit:
			break

	return [procedure_item(row) for row in list(seen.values())[:limit]]


def find_by_mention(text, space=None, limit=LIMIT):
	names = frappe.get_all(
		"SOP Reference",
		filters={"reference_name": ("like", f"%{text}%"), "parenttype": "SOP"},
		pluck="parent",
		limit_page_length=limit * 2,
	)
	if not names:
		return []

	filters = {"name": ("in", list(dict.fromkeys(names)))}
	if space:
		filters["space"] = space

	rows = frappe.get_list(
		"SOP",
		filters=filters,
		fields=["name", "sop_no", "title", "summary", "status", "version", "space"],
		limit_page_length=limit,
	)
	return [procedure_item(row) for row in rows]


def find_spaces(text):
	rows = frappe.get_list(
		"SOP Space",
		or_filters={"title": ("like", f"%{text}%"), "space_code": ("like", f"%{text}%")},
		fields=["name", "title", "space_code"],
		limit_page_length=5,
	)
	return [
		{
			"label": row.title,
			"description": _("Space · {0}").format(row.space_code),
			"route": f"/?space={row.name}",
			"icon": "lucide-library",
		}
		for row in rows
	]


def procedure_item(row):
	return {
		"label": row.title,
		"description": " · ".join(
			part for part in [row.sop_no, f"Rev {row.version}" if row.version else None, row.summary] if part
		),
		"route": f"/{row.name}",
		"badge": row.status,
		"icon": "lucide-file-text",
	}
