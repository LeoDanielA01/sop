# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re
from html import unescape
from urllib.parse import unquote

import frappe
from frappe import _
from frappe.utils import flt

from sop.api.mentions import (
	deadline_fact,
	extras_for,
	read,
	status_of,
	title_of,
	tone_of,
	type_named,
	value_fact,
)

LINK = re.compile(r'href="(#(?:live|check):[^"]+)"')
NUMBERS = {"Int", "Float", "Currency", "Percent"}
CHECKS = {
	"number": ["at_least", "at_most", "above_zero", "no_warning"],
	"date": ["not_passed", "days_left", "no_warning"],
	"text": ["is", "is_not", "no_warning"],
}


def choices(doctype, name):
	meta = frappe.get_meta(doctype)
	row, picked, deadlines = read(meta, name)
	out = []

	status = status_of(meta, row)
	if status:
		out.append(
			{
				"key": "status",
				"label": _("Status"),
				"value": status,
				"tone": tone_of(status),
				"kind": "text",
				"raw": status,
			}
		)

	for fact in extras_for(doctype, name):
		if "amount" in fact:
			kind, raw = "number", flt(fact["amount"])
		elif "days" in fact:
			kind, raw = "date", fact["days"]
		else:
			kind, raw = "text", fact.get("value")

		out.append(
			{
				"key": fact.get("key") or frappe.scrub(fact["label"]),
				"label": fact["label"],
				"value": fact["value"],
				"tone": fact.get("tone") or "gray",
				"kind": kind,
				"raw": raw,
			}
		)

	for df in deadlines:
		fact = deadline_fact(df, row.get(df.fieldname))
		if fact:
			out.append({**fact, "key": df.fieldname, "kind": "date", "raw": fact["days"]})

	for df in picked:
		fact = value_fact(df, row)
		if not fact:
			continue

		number = df.fieldtype in NUMBERS
		raw = flt(row.get(df.fieldname)) if number else fact["value"]
		out.append({**fact, "key": df.fieldname, "kind": "number" if number else "text", "raw": raw})

	seen = set()
	unique = []
	for option in out:
		if option["key"] not in seen:
			seen.add(option["key"])
			unique.append(option)

	return {"title": title_of(meta, row), "options": unique}


def passes(option, check, target):
	if check == "no_warning":
		return option["tone"] != "red"

	raw = option["raw"]

	if check == "is":
		return str(raw or "").strip().lower() == str(target or "").strip().lower()
	if check == "is_not":
		return str(raw or "").strip().lower() != str(target or "").strip().lower()
	if check == "above_zero":
		return flt(raw) > 0
	if check == "at_least":
		return flt(raw) >= flt(target)
	if check == "at_most":
		return flt(raw) <= flt(target)
	if check == "not_passed":
		return flt(raw) >= 0
	if check == "days_left":
		return flt(raw) >= flt(target)

	return False


def parse(href):
	kind, *parts = [unquote(part) for part in href[1:].split(":")]

	if kind == "live" and len(parts) >= 3:
		return {"kind": "live", "doctype": parts[0], "name": parts[1], "key": parts[2]}

	if kind == "check" and len(parts) >= 4:
		return {
			"kind": "check",
			"doctype": parts[0],
			"name": parts[1],
			"key": parts[2],
			"check": parts[3],
			"target": parts[4] if len(parts) > 4 else "",
		}

	return None


def outcome(spec, cache):
	doctype = type_named(spec["doctype"]) or spec["doctype"]
	name = spec["name"]
	record = (doctype, name)

	if record not in cache:
		if not frappe.db.exists("DocType", doctype) or not frappe.db.exists(doctype, name):
			cache[record] = None
		else:
			cache[record] = choices(doctype, name)

	found = cache[record]
	if not found:
		return {"missing": True, "message": _("{0} {1} can no longer be found.").format(doctype, name)}

	option = next((row for row in found["options"] if row["key"] == spec["key"]), None)
	if not option:
		return {
			"missing": True,
			"title": found["title"],
			"message": _("{0} no longer shows this detail.").format(found["title"]),
		}

	result = {
		"title": found["title"],
		"label": option["label"],
		"value": option["value"],
		"tone": option["tone"],
	}

	if spec["kind"] == "check":
		result["ok"] = passes(option, spec["check"], spec.get("target"))

	return result


@frappe.whitelist()
def options(doctype, name):
	doctype = type_named(doctype) or doctype

	if not frappe.has_permission(doctype, "read", doc=name):
		frappe.throw(_("You are not allowed to read {0}.").format(doctype), frappe.PermissionError)

	found = choices(doctype, name)
	for option in found["options"]:
		option["checks"] = CHECKS[option["kind"]]

	return found


@frappe.whitelist()
def preview(doctype, name, key, check=None, target=None):
	doctype = type_named(doctype) or doctype

	if not frappe.has_permission(doctype, "read", doc=name):
		frappe.throw(_("You are not allowed to read {0}.").format(doctype), frappe.PermissionError)

	spec = {"kind": "check" if check else "live", "doctype": doctype, "name": name, "key": key}
	if check:
		spec.update(check=check, target=target)

	return outcome(spec, {})


@frappe.whitelist()
def evaluate(sop, revision=None):
	from sop.api.procedures import served_content

	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	content, _version = served_content(doc, revision)

	cache = {}
	out = {}

	for href in dict.fromkeys(unescape(match) for match in LINK.findall(content or "")):
		spec = parse(href)
		if not spec:
			continue

		try:
			out[href] = outcome(spec, cache)
		except Exception:
			frappe.log_error(title=f"SOP live value failed in {sop}")
			out[href] = {"missing": True, "message": _("This live value could not be read.")}

	return out
