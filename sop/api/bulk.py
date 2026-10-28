# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import json
import re
from html import escape, unescape
from urllib.parse import quote, unquote

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

TAG = re.compile(r"(<[^>]*>)")
BLOCK = re.compile(r"^</?(?:p|div|li|ul|ol|h[1-6]|br|tr|td|th|table|blockquote|section|pre|hr)\b", re.I)
RECORD_ANCHOR = re.compile(r'^<a\b[^>]*href="#(?:mention|live|check):', re.I)
ANCHOR = re.compile(r'<a\b([^>]*?)href="#(mention|live|check):([^"]*)"([^>]*)>(.*?)</a>', re.I | re.S)
WHEN = re.compile(r'data-sop-when="([^"]*)"')
DOLLAR = re.compile(r"\$(?:(\d+)|\{(\d+)\}|(&))")
EMPTY_INLINE = re.compile(r"<(strong|em|b|i|u|s|mark|code)\b[^>]*></\1>", re.I)
GAP = "\n"
FIELDS = ("title", "summary", "content")
HTML_FIELDS = {"content"}
EDITABLE = ("Draft", "Under Revision")
SAFE = "-_.!~*'()"
LIMIT_MATCHES = 25
LIMIT_RECORDS = 2000

LOCK = "sop:bulk-replace"
LOCK_TTL = 300


def flatten(value, html=True):
	parts, chars, where = [], [], []
	if not html:
		parts.append(["text", value or "", value or "", False])
		for offset, char in enumerate(value or ""):
			chars.append(char)
			where.append((0, offset))
		return parts, "".join(chars), where

	guarded = 0
	for chunk in TAG.split(value or ""):
		if not chunk:
			continue

		if chunk.startswith("<"):
			if RECORD_ANCHOR.match(chunk):
				guarded += 1
			elif guarded and chunk[:3].lower() == "</a":
				guarded -= 1
			parts.append(["tag", chunk, None, False])
			if BLOCK.match(chunk):
				chars.append(GAP)
				where.append(None)
			continue

		decoded = unescape(chunk)
		index = len(parts)
		parts.append(["text", chunk, decoded, False])
		for offset, char in enumerate(decoded):
			chars.append(char)
			where.append(None if guarded else (index, offset))

	return parts, "".join(chars), where


def rules_of(rules=None, find=None, replace=None, match_case=0, whole_word=0):
	rows = frappe.parse_json(rules) if rules else None
	if not rows:
		rows = [{"find": find, "replace": replace, "match_case": match_case, "whole_word": whole_word}]

	out = []
	for number, row in enumerate(rows, 1):
		text = row.get("find") or ""
		if not text.strip():
			continue
		if len(text) > 500:
			frappe.throw(_("Rule {0} is too long. Keep a pattern under 500 characters.").format(number))

		rule = {
			"find": text if cint(row.get("regex")) else text.strip(),
			"replace": row.get("replace") or "",
			"regex": cint(row.get("regex")),
			"match_case": cint(row.get("match_case")),
			"whole_word": cint(row.get("whole_word")),
			"keep_case": cint(row.get("keep_case")),
		}

		source = rule["find"] if rule["regex"] else re.escape(rule["find"])
		if rule["whole_word"]:
			source = rf"(?<!\w)(?:{source})(?!\w)"
		try:
			rule["pattern"] = re.compile(source, 0 if rule["match_case"] else re.IGNORECASE)
		except re.error as error:
			frappe.throw(_("Rule {0} is not a valid pattern: {1}.").format(number, error))

		out.append(rule)

	return out


def keep_case(found, value):
	letters = [char for char in found if char.isalpha()]
	if not letters or not value:
		return value
	if all(char.isupper() for char in letters) and len(letters) > 1:
		return value.upper()
	if letters[0].isupper():
		return value[:1].upper() + value[1:]
	return value[:1].lower() + value[1:]


def substitute(rule, match):
	value = rule["replace"]
	if rule["regex"]:

		def group(found):
			number = found.group(1) or found.group(2)
			try:
				return (match.group(int(number)) if number else match.group(0)) or ""
			except IndexError:
				return found.group(0)

		value = DOLLAR.sub(group, value)

	return keep_case(match.group(0), value) if rule["keep_case"] else value


def matches_in(text, where, rules):
	found = []
	for order, rule in enumerate(rules):
		for match in rule["pattern"].finditer(text):
			start, end = match.span()
			if end <= start or any(where[spot] is None for spot in range(start, end)):
				continue
			found.append((start, order, end, rule, match))

	found.sort(key=lambda row: (row[0], row[1]))

	chosen, edge = [], -1
	for start, order, end, rule, match in found:
		if start < edge:
			continue
		chosen.append({"start": start, "end": end, "rule": order, "with": substitute(rule, match), "hit": match.group(0)})
		edge = end

	return chosen


def context(text, start, end, width=45):
	left, right = max(0, start - width), min(len(text), end + width)
	clean = lambda value: re.sub(r"\s+", " ", value)
	return (
		("…" if left else "") + clean(text[left:start]),
		clean(text[end:right]) + ("…" if right < len(text) else ""),
	)


def replace_text(value, rules, html=True, only=None, start=0):
	parts, text, where = flatten(value, html)
	found = matches_in(text, where, rules)
	seen = start + len(found)
	picked = [hit for number, hit in enumerate(found, start) if only is None or number in only]

	for hit in reversed(picked):
		spots = where[hit["start"] : hit["end"]]
		first = spots[0][0]
		pieces = {}
		for index, offset in spots:
			low, high = pieces.get(index, (offset, offset))
			pieces[index] = (min(low, offset), max(high, offset))

		for index in sorted(pieces, reverse=True):
			low, high = pieces[index]
			decoded = parts[index][2]
			middle = hit["with"] if index == first else ""
			parts[index][2] = decoded[:low] + middle + decoded[high + 1 :]
			parts[index][3] = True

	out = []
	for kind, raw, decoded, changed in parts:
		if kind == "text" and changed:
			out.append(escape(decoded, quote=False) if html else decoded)
		else:
			out.append(raw)

	value = "".join(out)
	if html and picked:
		value = EMPTY_INLINE.sub("", value)

	return value, len(picked), seen


def text_hits(value, rules, html=True, start=0, field=None):
	parts, text, where = flatten(value, html)
	listed = []
	found = matches_in(text, where, rules)
	for number, hit in enumerate(found, start):
		if len(listed) >= LIMIT_MATCHES:
			break
		before, after = context(text, hit["start"], hit["end"])
		listed.append(
			{"index": number, "field": field, "before": before, "hit": hit["hit"], "after": after, "with": hit["with"]}
		)
	return listed, start + len(found)


def doctype_matches(written, wanted, cache):
	if written == wanted:
		return True
	if written not in cache:
		from sop.api.mentions import type_named

		cache[written] = type_named(written)
	return cache[written] == wanted


def title_for(doctype, name, cache):
	key = (doctype, name)
	if key not in cache:
		meta = frappe.get_meta(doctype)
		field = meta.title_field if meta.title_field and meta.has_field(meta.title_field) else None
		cache[key] = (frappe.db.get_value(doctype, name, field) if field else None) or name
	return cache[key]


def plain(html):
	return re.sub(r"\s+", " ", unescape(TAG.sub(" ", html or ""))).strip()


def record_spec(record):
	spec = frappe.parse_json(record) if isinstance(record, str) else record
	if not spec or not spec.get("doctype"):
		frappe.throw(_("Pick the kind of record to replace."))

	doctype = spec["doctype"]
	if not frappe.db.exists("DocType", doctype):
		frappe.throw(_("{0} is not a record type.").format(doctype))

	names = [name for name in (spec.get("names") or []) if name]
	rules = [row for row in (spec.get("filters") or []) if row and row[0] and len(row) >= 3]

	if not names and not rules:
		frappe.throw(_("Pick the records to replace, or describe them with a filter."))

	if rules:
		matched = frappe.get_list(
			doctype,
			filters=[[doctype, field, operator, value] for field, operator, value in (row[:3] for row in rules)],
			pluck="name",
			limit_page_length=LIMIT_RECORDS,
		)
		names = [name for name in names if name in matched] if names else matched

	mapping = {old: new for old, new in (spec.get("map") or {}).items() if new}
	return {"doctype": doctype, "names": set(names), "to": spec.get("to") or None, "map": mapping}


def new_name(spec, old):
	return spec["map"].get(old) or spec["to"]


def record_links(html, spec, cache):
	links = []
	for match in ANCHOR.finditer(html or ""):
		kind, raw = match.group(2), unescape(match.group(3))
		if kind == "mention":
			doctype, _sep, name = raw.partition(":")
		else:
			pieces = [unquote(piece) for piece in raw.split(":")]
			if len(pieces) < 2:
				continue
			doctype, name = pieces[0], pieces[1]

		if name in spec["names"] and doctype_matches(doctype, spec["doctype"], cache):
			links.append({"span": match.span(), "kind": kind, "name": name, "match": match})

	for match in WHEN.finditer(html or ""):
		for condition in unescape(match.group(1)).split("|"):
			pieces = [unquote(piece) for piece in condition.split(":")]
			if len(pieces) >= 3 and pieces[0] == "check":
				if pieces[2] in spec["names"] and doctype_matches(pieces[1], spec["doctype"], cache):
					links.append({"span": match.span(), "kind": "when", "name": pieces[2], "match": match})

	return links


def record_hits(html, spec, cache, start=0):
	listed = []
	links = record_links(html, spec, cache)
	for number, link in enumerate(links, start):
		if len(listed) >= LIMIT_MATCHES:
			break
		low, high = link["span"]
		before = plain(html[max(0, low - 400) : low])[-45:]
		after = plain(html[high : high + 400])[:45]
		label = plain(link["match"].group(5)) if link["kind"] != "when" else _("condition")
		target = new_name(spec, link["name"])
		by_id = label == link["name"] or link["kind"] == "when"
		listed.append(
			{
				"index": number,
				"field": "content",
				"kind": link["kind"],
				"record": link["name"],
				"before": ("…" if low else "") + before + " ",
				"hit": label or link["name"],
				"after": " " + after + "…",
				"with": (target if by_id else title_for(spec["doctype"], target, cache)) if target else "",
				"to": target,
				"by_id": by_id,
			}
		)
	return listed, start + len(links)


def encode_parts(pieces):
	return ":".join(quote(str(piece), safe=SAFE) for piece in pieces)


def swap_condition(value, spec, cache, number, only, counter):
	out = []
	for condition in unescape(value).split("|"):
		pieces = [unquote(piece) for piece in condition.split(":")]
		if len(pieces) >= 3 and pieces[0] == "check" and pieces[2] in spec["names"] and doctype_matches(
			pieces[1], spec["doctype"], cache
		):
			index = number + counter["seen"]
			counter["seen"] += 1
			target = new_name(spec, pieces[2])
			if target and (only is None or index in only):
				pieces[2] = target
				counter["hits"] += 1
				condition = "check:" + encode_parts(pieces[1:])
		out.append(condition)
	return escape("|".join(out), quote=True)


def replace_records(html, spec, cache, only=None, start=0):
	if not html:
		return html, 0, start

	links = record_links(html, spec, cache)
	order = {link["span"]: index for index, link in enumerate(links, start) if link["kind"] != "when"}
	counter = {"hits": 0, "seen": 0}

	def anchor(match):
		index = order.get(match.span())
		if index is None:
			return match.group(0)

		kind, raw = match.group(2), unescape(match.group(3))
		if kind == "mention":
			doctype, _sep, old = raw.partition(":")
		else:
			pieces = [unquote(piece) for piece in raw.split(":")]
			doctype, old = pieces[0], pieces[1]

		target = new_name(spec, old)
		if not target or (only is not None and index not in only):
			return match.group(0)

		counter["hits"] += 1
		if kind == "mention":
			href = f"#mention:{doctype}:{target}"
		else:
			pieces[1] = target
			href = f"#{kind}:{encode_parts(pieces)}"

		label = match.group(5)
		shown = plain(label)
		if shown == old:
			label = escape(target, quote=False)
		elif shown == title_for(spec["doctype"], old, cache):
			label = escape(title_for(spec["doctype"], target, cache), quote=False)

		return f'<a{match.group(1)}href="{escape(href, quote=True)}"{match.group(4)}>{label}</a>'

	html = ANCHOR.sub(anchor, html)

	when_start = start + sum(1 for link in links if link["kind"] != "when")
	html = WHEN.sub(
		lambda match: f'data-sop-when="{swap_condition(match.group(1), spec, cache, when_start, only, counter)}"',
		html,
	)

	return html, counter["hits"], start + len(links)


def describe(kind, rules=None, spec=None):
	if kind == "Record":
		target = spec["to"] or _("{0} mapped records").format(len(spec["map"]))
		return _("{0}: {1} records → {2}").format(spec["doctype"], len(spec["names"]), target)[:140]

	parts = [f"“{rule['find']}” → “{rule['replace']}”" for rule in rules]
	return "; ".join(parts)[:140]


def fields_of(fields):
	chosen = frappe.parse_json(fields) if isinstance(fields, str) else fields
	return [field for field in (chosen or FIELDS) if field in FIELDS] or list(FIELDS)


def candidates(space=None, record=None):
	filters = {"space": space} if space else {}
	if record:
		parents = frappe.get_all(
			"SOP Reference",
			filters={"parenttype": "SOP", "reference_doctype": record["doctype"], "reference_name": ("in", list(record["names"]) or [""])},
			pluck="parent",
			limit_page_length=0,
		)
		linked = frappe.get_all("SOP", filters={"content": ("like", "%#live:%")}, pluck="name", limit_page_length=0)
		linked += frappe.get_all("SOP", filters={"content": ("like", "%check:%")}, pluck="name", limit_page_length=0)
		filters["name"] = ("in", list(dict.fromkeys(parents + linked)) or [""])

	return frappe.get_list(
		"SOP",
		filters=filters,
		fields=["name", "sop_no", "title", "summary", "status", "content"],
		order_by="sop_no asc",
		limit_page_length=0,
	)


@frappe.whitelist()
def preview(
	find=None, replace=None, space=None, match_case=0, whole_word=0, rules=None, fields=None, record=None, limit=None
):
	cache = {}
	record = record_spec(record) if record else None
	rules = None if record else rules_of(rules, find, replace, match_case, whole_word)
	if not record and not rules:
		return []

	look_in = fields_of(fields)
	out = []
	for row in candidates(space, record):
		matches, seen = [], 0

		if record:
			matches, seen = record_hits(row.content, record, cache)
		else:
			for field in FIELDS:
				if field not in look_in:
					continue
				found, seen = text_hits(row.get(field), rules, field in HTML_FIELDS, seen, field)
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


FILTERABLE = {"Link", "Select", "Data", "Check", "Int", "Float", "Currency", "Date", "Dynamic Link"}


@frappe.whitelist()
def record_types():
	rows = frappe.db.sql(
		"""
		SELECT reference_doctype AS doctype, COUNT(DISTINCT reference_name) AS records, COUNT(DISTINCT parent) AS procedures
		FROM `tabSOP Reference`
		WHERE parenttype = 'SOP' AND reference_doctype != 'User'
		GROUP BY reference_doctype
		ORDER BY procedures DESC
		""",
		as_dict=True,
	)
	return [row for row in rows if frappe.db.exists("DocType", row.doctype) and frappe.has_permission(row.doctype, "read")]


@frappe.whitelist()
def filter_fields(doctype):
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("You cannot read {0}.").format(doctype), frappe.PermissionError)

	meta = frappe.get_meta(doctype)
	fields = [
		{"fieldname": df.fieldname, "label": _(df.label), "fieldtype": df.fieldtype, "options": df.options or ""}
		for df in meta.fields
		if df.fieldtype in FILTERABLE and df.label and not df.hidden
	]
	return [{"fieldname": "name", "label": _("ID"), "fieldtype": "Data", "options": ""}, *fields]


@frappe.whitelist()
def linked_records(doctype, space=None):
	filters = {"parenttype": "SOP", "reference_doctype": doctype}
	names = frappe.get_all("SOP Reference", filters=filters, pluck="reference_name", distinct=True, limit_page_length=0)
	cache = {}
	return [
		{"value": name, "label": title_for(doctype, name, cache)}
		for name in sorted(names)
		if frappe.db.exists(doctype, name)
	]


@frappe.whitelist()
def titles(doctype, names):
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("You cannot read {0}.").format(doctype), frappe.PermissionError)

	cache = {}
	return {name: title_for(doctype, name, cache) for name in frappe.parse_json(names) or [] if frappe.db.exists(doctype, name)}


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


def open_batch(batch, kind, rules=None, spec=None, raw=None):
	if batch:
		doc = frappe.get_doc("SOP Bulk Change", batch)
		if doc.owner != frappe.session.user:
			frappe.throw(_("That change belongs to someone else."), frappe.PermissionError)
		return doc

	doc = frappe.get_doc(
		{
			"doctype": "SOP Bulk Change",
			"kind": kind,
			"status": "Applied",
			"description": describe(kind, rules, spec),
			"spec": json.dumps(raw, indent=1, default=str),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


@frappe.whitelist()
def apply(
	names,
	find=None,
	replace=None,
	match_case=0,
	whole_word=0,
	start_revision=0,
	picks=None,
	rules=None,
	fields=None,
	record=None,
	batch=None,
):
	names = frappe.parse_json(names) if isinstance(names, str) else names
	picks = (frappe.parse_json(picks) if isinstance(picks, str) else picks) or {}
	start_revision = cint(start_revision)
	cache = {}

	raw_record = frappe.parse_json(record) if isinstance(record, str) else record
	spec = record_spec(raw_record) if raw_record else None
	rule_rows = None if spec else rules_of(rules, find, replace, match_case, whole_word)
	if not spec and not rule_rows:
		frappe.throw(_("Nothing to find."))

	current = holder()
	if current and current != frappe.session.user:
		frappe.throw(_("{0} is running a replace right now.").format(current), frappe.ValidationError)
	frappe.cache().set_value(LOCK, frappe.session.user, expires_in_sec=LOCK_TTL)

	look_in = fields_of(fields)
	raw = {"record": raw_record} if spec else {
		"rules": [{key: value for key, value in rule.items() if key != "pattern"} for rule in rule_rows],
		"fields": look_in,
	}
	log = open_batch(batch, "Record" if spec else "Text", rule_rows, spec, raw)

	changed, skipped = [], []
	for name in names or []:
		doc = frappe.get_doc("SOP", name)
		if not doc.has_permission("write"):
			skipped.append({"name": name, "status": doc.status, "sop_no": doc.sop_no, "reason": _("no permission")})
			continue

		revised = 0
		if doc.status not in EDITABLE:
			if not start_revision or doc.status != "Effective":
				skipped.append({"name": name, "status": doc.status, "sop_no": doc.sop_no, "reason": doc.status})
				continue

			from sop.api.lifecycle import start_revision as begin

			begin(name)
			doc = frappe.get_doc("SOP", name)
			revised = 1

		wanted = picks.get(name)
		only = set(wanted) if wanted is not None else None
		before = {field: doc.get(field) for field in FIELDS}

		hits = 0
		if spec:
			doc.content, hits, _seen = replace_records(doc.content, spec, cache, only)
		else:
			seen = 0
			for field in FIELDS:
				if field not in look_in:
					continue
				value, found, seen = replace_text(doc.get(field), rule_rows, field in HTML_FIELDS, only, seen)
				doc.set(field, value)
				hits += found

		if not hits:
			continue

		doc.save()
		log.append(
			"changes",
			{
				"sop": doc.name,
				"sop_no": doc.sop_no,
				"hits": hits,
				"revised": revised,
				"modified_after": doc.modified,
				"title_before": before["title"],
				"summary_before": before["summary"],
				"content_before": before["content"],
			},
		)
		changed.append({"name": name, "sop_no": doc.sop_no, "hits": hits})

	log.save(ignore_permissions=True)
	frappe.db.commit()

	return {"changed": changed, "skipped": skipped, "batch": log.name}


@frappe.whitelist()
def history(limit=20):
	rows = frappe.get_all(
		"SOP Bulk Change",
		fields=["name", "kind", "status", "description", "owner", "creation", "undone_by", "undone_on"],
		order_by="creation desc",
		limit_page_length=cint(limit) or 20,
	)
	if not rows:
		return []

	counts = {}
	for row in frappe.get_all(
		"SOP Bulk Change Item",
		filters={"parenttype": "SOP Bulk Change", "parent": ("in", [row.name for row in rows])},
		fields=["parent", "hits"],
		limit_page_length=0,
	):
		total = counts.setdefault(row.parent, [0, 0])
		total[0] += 1
		total[1] += cint(row.hits)

	names = dict(
		frappe.get_all(
			"User",
			filters={"name": ("in", list({row.owner for row in rows}))},
			fields=["name", "full_name"],
			as_list=True,
		)
	)
	for row in rows:
		row.procedures, row.hits = counts.get(row.name, [0, 0])
		row.owner_name = names.get(row.owner) or row.owner
		row.can_undo = row.status == "Applied" and (
			row.owner == frappe.session.user or "SOP Manager" in frappe.get_roles()
		)

	return [row for row in rows if row.procedures or row.status == "Undone"]


@frappe.whitelist()
def undo(batch):
	log = frappe.get_doc("SOP Bulk Change", batch)
	if log.owner != frappe.session.user and "SOP Manager" not in frappe.get_roles():
		frappe.throw(_("Only the person who made this change or an SOP Manager can undo it."), frappe.PermissionError)
	if log.status == "Undone":
		frappe.throw(_("This change was already undone."))

	restored, left = [], []
	for row in log.changes:
		if not frappe.db.exists("SOP", row.sop):
			left.append({"sop_no": row.sop_no, "reason": _("deleted")})
			continue

		doc = frappe.get_doc("SOP", row.sop)
		if not doc.has_permission("write"):
			left.append({"sop_no": row.sop_no, "reason": _("no permission")})
		elif get_datetime(doc.modified) != get_datetime(row.modified_after):
			left.append({"sop_no": row.sop_no, "reason": _("edited since")})
		elif doc.status not in EDITABLE:
			left.append({"sop_no": row.sop_no, "reason": doc.status})
		else:
			doc.title = row.title_before
			doc.summary = row.summary_before
			doc.content = row.content_before
			doc.save()
			restored.append({"sop_no": row.sop_no, "revised": row.revised})

	log.status = "Undone"
	log.undone_by = frappe.session.user
	log.undone_on = now_datetime()
	log.save(ignore_permissions=True)

	return {"restored": restored, "left": left}
