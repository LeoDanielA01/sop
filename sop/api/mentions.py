# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _

CACHE_TTL = 60
CACHE_PREFIX = "sop:mention"


@frappe.whitelist()
def resolve(references):

	if isinstance(references, str):
		references = frappe.parse_json(references)

	grouped = {}
	for row in references or []:
		doctype = row.get("doctype") or row.get("reference_doctype")
		name = row.get("name") or row.get("reference_name")
		if doctype and name:
			grouped.setdefault(doctype, set()).add(name)

	resolved = []
	for doctype, names in grouped.items():
		resolved += resolve_doctype(doctype, sorted(names))

	return resolved


@frappe.whitelist()
def targets():
	rows = frappe.get_all(
		"SOP Mention Config",
		filters={"enabled": 1},
		fields=["document_type", "title_field"],
		order_by="document_type asc",
		limit_page_length=0,
	)

	return [
		{"doctype": row.document_type, "title_field": row.title_field}
		for row in rows
		if frappe.has_permission(row.document_type, "read")
	]


@frappe.whitelist()
def find(doctype, text=None, limit=10):
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("You are not allowed to read {0}.").format(doctype), frappe.PermissionError)

	title_field = frappe.db.get_value("SOP Mention Config", doctype, "title_field")
	title_field = title_field or frappe.get_meta(doctype).title_field

	fields = ["name"]
	if title_field and title_field != "name":
		fields.append(title_field)

	filters = {}
	or_filters = {}
	if text:
		like = f"%{text}%"
		or_filters["name"] = ("like", like)
		if title_field and title_field != "name":
			or_filters[title_field] = ("like", like)

	rows = frappe.get_list(
		doctype,
		filters=filters,
		or_filters=or_filters or None,
		fields=fields,
		limit_page_length=frappe.utils.cint(limit) or 10,
	)

	return [
		{"name": row.name, "label": (row.get(title_field) if title_field else None) or row.name}
		for row in rows
	]


def resolve_doctype(doctype, names):
	out = []
	pending = []

	for name in names:
		cached = frappe.cache().get_value(cache_key(doctype, name))
		if cached:
			out.append(cached)
		else:
			pending.append(name)

	if not pending:
		return out

	readable = [name for name in pending if frappe.has_permission(doctype, "read", doc=name)]
	blocked = [name for name in pending if name not in readable]

	out += [plain(doctype, name) for name in blocked]

	if readable:
		try:
			out += resolver_for(doctype)(doctype, readable)
		except Exception:
			frappe.log_error(title=f"SOP mention resolver failed for {doctype}")
			out += [plain(doctype, name) for name in readable]

	for row in out:
		if row.get("reference_name") in readable:
			frappe.cache().set_value(
				cache_key(doctype, row["reference_name"]), row, expires_in_sec=CACHE_TTL
			)

	return out


def resolver_for(doctype):
	registered = (frappe.get_hooks("sop_mention_resolvers") or {}).get(doctype)
	if registered:
		return frappe.get_attr(registered[0] if isinstance(registered, list) else registered)

	if frappe.db.exists("SOP Mention Config", {"document_type": doctype, "enabled": 1}):
		return configured

	return generic


def configured(doctype, names):
	config = frappe.get_doc("SOP Mention Config", {"document_type": doctype})
	fields = ["name", config.title_field or "name"]

	badge_fields = [row.fieldname for row in config.badge_fields]
	fields += [f for f in badge_fields if f not in fields]
	if config.status_field and config.status_field not in fields:
		fields.append(config.status_field)

	rows = frappe.get_all(doctype, filters={"name": ("in", names)}, fields=fields, limit_page_length=0)
	labels = {row.fieldname: row.label for row in config.badge_fields}

	out = []
	for row in rows:
		badges = []
		if config.status_field and row.get(config.status_field):
			badges.append({"label": row.get(config.status_field), "tone": "neutral"})

		for fieldname in badge_fields:
			value = row.get(fieldname)
			if value in (None, "", 0):
				continue
			badges.append({"label": f"{labels.get(fieldname, fieldname)}: {value}", "tone": "neutral"})

		out.append(chip(doctype, row.name, row.get(config.title_field) or row.name, badges))

	return out


def generic(doctype, names):
	meta = frappe.get_meta(doctype)
	fields = ["name"]

	if meta.title_field and meta.title_field not in fields:
		fields.append(meta.title_field)
	if meta.has_field("status"):
		fields.append("status")

	rows = frappe.get_all(doctype, filters={"name": ("in", names)}, fields=fields, limit_page_length=0)

	out = []
	for row in rows:
		badges = []
		if row.get("status"):
			badges.append({"label": row.status, "tone": "neutral"})

		label = row.get(meta.title_field) if meta.title_field else None
		out.append(chip(doctype, row.name, label or row.name, badges))

	return out


def plain(doctype, name):
	return chip(doctype, name, name, [], url=None)


def chip(doctype, name, label, badges, url=...):
	return {
		"key": f"{doctype}::{name}",
		"reference_doctype": doctype,
		"reference_name": name,
		"short_type": frappe.unscrub(doctype).split(" ")[0][:12],
		"label": label,
		"badges": badges,
		"url": frappe.utils.get_url_to_form(doctype, name) if url is ... else url,
	}


def cache_key(doctype, name):
	return f"{CACHE_PREFIX}:{frappe.session.user}:{doctype}:{name}"
