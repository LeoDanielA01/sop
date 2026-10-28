# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re
from html import escape, unescape

import frappe
from frappe import _
from frappe.utils import add_days, cint, nowdate

LIMIT = 8
MARK = re.compile(r"</?mark>")
SPACE = re.compile(r"\s+")
TOKEN = re.compile(r'(-?)(?:([a-zA-Z]+):)?(?:"([^"]*)"|(\S+))')

STATUSES = ("Draft", "In Review", "Approved", "Effective", "Under Revision", "Retired")
TYPES = ("Process SOP", "Equipment SOP", "Appendix")
RISKS = ("Low", "Medium", "High")
KEYS = {
	"status": "status",
	"is": "status",
	"in": "space",
	"space": "space",
	"type": "type",
	"risk": "risk",
	"owner": "owner",
	"review": "review",
	"changed": "changed",
}
FIELDS = set(KEYS.values())
SORTS = {
	"modified": "modified desc",
	"number": "sop_no asc",
	"title": "title asc",
	"review": "review_due asc",
}
SEARCH_CLASS = "sop.sop.doctype.sop.sop_sqlite_search.SOPSQLiteSearch"


@frappe.whitelist()
def query(text, space=None, limit=LIMIT):
	text = (text or "").strip()
	if not text:
		return {"groups": []}

	limit = cint(limit) or LIMIT
	found = find(text)
	groups = []

	procedures = matching_rows(found, limit) if found.active else []
	if procedures:
		groups.append({"title": _("Procedures"), "items": [procedure_item(row, found.terms) for row in procedures]})

	if found.terms:
		shown = {row.name for row in procedures}
		mentions = [row for row in find_by_mention(" ".join(found.terms), limit) if row.name not in shown]
		if mentions:
			groups.append(
				{"title": _("Mentions this record"), "items": [procedure_item(row, found.terms) for row in mentions]}
			)

	spaces = find_spaces(text) if found.terms and not found.chosen else []
	if spaces:
		groups.append({"title": _("Spaces"), "items": spaces})

	return {"groups": groups, "corrected": found.corrected}


@frappe.whitelist()
def facets():
	owners = frappe.get_all("SOP", filters={"process_owner": ("is", "set")}, pluck="process_owner", distinct=True)
	names = dict(
		frappe.get_all(
			"User", filters={"name": ("in", owners or [""])}, fields=["name", "full_name"], as_list=True
		)
	)
	return {
		"statuses": STATUSES,
		"types": TYPES,
		"risks": RISKS,
		"owners": sorted(
			({"value": user, "label": names.get(user) or user} for user in owners),
			key=lambda row: row["label"].lower(),
		),
	}


@frappe.whitelist()
def rebuild_index():
	if "SOP Manager" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only an SOP Manager can rebuild the search index."), frappe.PermissionError)

	frappe.enqueue(
		"frappe.search.sqlite_search.build_index",
		queue="long",
		job_id=f"{SEARCH_CLASS}_rebuild",
		deduplicate=True,
		search_class_path=SEARCH_CLASS,
		force=True,
	)


def rebuild_nightly():
	from frappe.search.sqlite_search import build_index

	build_index(search_class_path=SEARCH_CLASS, force=True)


def parse(text):
	found = frappe._dict(words=[], phrases=[], excluded=[], filters={})

	for minus, key, quoted, bare in TOKEN.findall(text or ""):
		value = quoted or bare
		field = KEYS.get(key.lower()) if key else None

		if field:
			if value:
				found.filters.setdefault(field, []).append(value)
			continue

		if key:
			value = f"{key}:{value}"

		if not value or value == "-":
			continue

		if minus:
			found.excluded.append(value)
		elif quoted:
			found.phrases.append(value)
		else:
			found.words.append(value)

	return found


def find(text, filters=None):
	parsed = parse(text)

	chosen = {}
	for source in (frappe.parse_json(filters) or {}, parsed.filters):
		for field, values in source.items():
			if field not in FIELDS:
				continue
			values = values if isinstance(values, list) else [values]
			chosen.setdefault(field, []).extend(value for value in values if value)
	chosen = {field: list(dict.fromkeys(values)) for field, values in chosen.items() if values}

	rules = conditions(chosen)
	rules += [["search_text", "not like", f"%{word}%"] for word in parsed.excluded]

	statuses = next((rule[2] for rule in rules if rule[0] == "status"), None)
	spaces = next((rule[2] for rule in rules if rule[0] == "space"), None)
	ranked, corrected = rank(parsed, statuses, spaces)

	terms = parsed.phrases + parsed.words
	if corrected:
		terms += [word for word in corrected.values() if word not in terms]

	return frappe._dict(
		active=bool(ranked is not None or chosen),
		ranked=ranked,
		rules=rules,
		terms=terms,
		corrected=corrected,
		chosen=chosen,
		parsed=parsed,
	)


def conditions(chosen):
	rules = []

	for field, values in chosen.items():
		if field == "status":
			rules.append(["status", "in", pick(values, STATUSES)])
		elif field == "type":
			rules.append(["document_type", "in", pick(values, TYPES)])
		elif field == "risk":
			rules.append(["risk_level", "in", pick(values, RISKS)])
		elif field == "space":
			rules.append(["space", "in", spaces_named(values)])
		elif field == "owner":
			rules.append(["process_owner", "in", owners_named(values)])
		elif field == "review":
			if values[-1].lower().startswith("over"):
				rules += [["status", "=", "Effective"], ["review_due", "<", nowdate()]]
			else:
				rules += [["status", "=", "Effective"], ["review_due", "between", [nowdate(), add_days(nowdate(), 30)]]]
		elif field == "changed":
			days = cint(re.sub(r"\D", "", values[-1])) or 30
			rules.append(["modified", ">=", add_days(nowdate(), -days)])

	return rules


def pick(values, options):
	chosen = []
	for value in values:
		key = value.lower().replace("-", " ").replace("_", " ").strip()
		chosen += [option for option in options if option.lower() == key] or [
			option for option in options if key in option.lower()
		]
	return list(dict.fromkeys(chosen)) or [""]


def spaces_named(values):
	wanted = {value.lower() for value in values}
	rows = frappe.get_all("SOP Space", fields=["name", "space_code", "title"], limit_page_length=0)
	return [
		row.name
		for row in rows
		if wanted & {(row.name or "").lower(), (row.space_code or "").lower(), (row.title or "").lower()}
	] or [""]


def owners_named(values):
	users = []
	for value in values:
		if value.lower() == "me":
			users.append(frappe.session.user)
		elif frappe.db.exists("User", value):
			users.append(value)
		else:
			users += frappe.get_all(
				"User",
				or_filters={"full_name": ("like", f"%{value}%"), "name": ("like", f"%{value}%")},
				pluck="name",
				limit_page_length=20,
			)
	return list(dict.fromkeys(users)) or [""]


def rank(parsed, statuses=None, spaces=None):
	if not (parsed.words or parsed.phrases or parsed.excluded):
		return None, None

	hits, corrected = None, None
	if (parsed.words or parsed.phrases) and "Retired" not in (statuses or []):
		hits, corrected = indexed(parsed, statuses, spaces)

	if not hits:
		hits, corrected = by_like(parsed), None

	text = " ".join(parsed.phrases + parsed.words)
	mentioned = [row.name for row in find_by_mention(text, 0)] if text else []

	return list(dict.fromkeys(hits + mentioned)), corrected


def indexed(parsed, statuses=None, spaces=None):
	from sop.sop.doctype.sop.sop_sqlite_search import SOPSQLiteSearch

	search = SOPSQLiteSearch()
	if not (search.is_search_enabled() and search.index_exists()):
		return None, None

	filters = {}
	if statuses:
		filters["status"] = list(statuses)
	if spaces:
		filters["space"] = list(spaces)

	try:
		return search.find(parsed.words, parsed.phrases, parsed.excluded, filters)
	except Exception:
		frappe.log_error(title="SOP search index unavailable")
		return None, None


def by_like(parsed):
	rules = [["search_text", "like", f"%{word}%"] for word in parsed.words + parsed.phrases]
	rules += [["search_text", "not like", f"%{word}%"] for word in parsed.excluded]
	rows = frappe.get_all(
		"SOP", filters=rules, fields=["name", "title", "sop_no"], order_by="modified desc", limit_page_length=0
	)

	wanted = [word.lower() for word in parsed.phrases + parsed.words]

	def weight(row):
		title = (row.title or "").lower()
		return 0 if wanted and any(word in title for word in wanted) else 1

	return [row.name for row in sorted(rows, key=weight)]


def matching_rows(found, limit=None, base=None, sort="relevance", start=0, fields=None):
	rules = list(base or []) + found.rules
	if found.ranked is not None:
		rules.append(["name", "in", found.ranked or [""]])

	order = SORTS.get(sort) or "modified desc"
	names = frappe.get_list("SOP", filters=rules, pluck="name", order_by=order, limit_page_length=0)
	if found.ranked is not None and sort not in SORTS:
		place = {name: index for index, name in enumerate(found.ranked)}
		names.sort(key=lambda name: place.get(name, len(place)))

	page = names[start : start + limit] if limit else names[start:]
	rows = frappe.get_list(
		"SOP",
		filters={"name": ("in", page or [""])},
		fields=fields or ["name", "sop_no", "title", "summary", "status", "version", "space", "search_text"],
		limit_page_length=0,
	)
	place = {name: index for index, name in enumerate(page)}
	rows.sort(key=lambda row: place.get(row.name, 0))
	return MatchedRows(rows, len(names))


class MatchedRows(list):
	def __init__(self, rows, total):
		super().__init__(rows)
		self.total = total


def body_of(row):
	text = row.get("search_text") or ""
	number = row.get("sop_no") or ""
	return text[len(number) :] if number and text.startswith(number) else text


def excerpt(content, terms, width=60, fallback=None):
	if isinstance(terms, str):
		terms = [terms]
	terms = [term for term in (terms or []) if term]

	plain = SPACE.sub(" ", unescape(MARK.sub("", content or ""))).strip()
	lower = plain.lower()
	hits = sorted((lower.find(term.lower()), term) for term in terms if term.lower() in lower)

	if not hits:
		plain = SPACE.sub(" ", unescape(fallback or "")).strip() or plain
		return escape(plain[: width * 2]) + ("…" if len(plain) > width * 2 else "")

	at, first = hits[0]
	start, end = max(0, at - width), min(len(plain), at + len(first) + width)
	window = plain[start:end]
	pattern = re.compile("|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True)), re.I)

	out, last = [], 0
	for match in pattern.finditer(window):
		out += [escape(window[last : match.start()]), "<mark>", escape(match.group()), "</mark>"]
		last = match.end()
	out.append(escape(window[last:]))

	return ("…" if start else "") + "".join(out) + ("…" if end < len(plain) else "")


def find_by_mention(text, limit=LIMIT):
	names = frappe.get_all(
		"SOP Reference",
		filters={"reference_name": ("like", f"%{text}%"), "parenttype": "SOP"},
		pluck="parent",
		limit_page_length=limit * 2 if limit else 0,
	)
	if not names:
		return []

	return frappe.get_list(
		"SOP",
		filters={"name": ("in", list(dict.fromkeys(names)))},
		fields=["name", "sop_no", "title", "summary", "status", "version", "space", "search_text"],
		limit_page_length=limit or 0,
	)


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


def procedure_item(row, terms=None):
	return {
		"label": row.title,
		"description": " · ".join(
			part for part in [row.sop_no, f"Rev {row.version}" if row.version else None] if part
		),
		"excerpt": excerpt(body_of(row), terms, fallback=row.get("summary")),
		"route": f"/{row.name}",
		"badge": row.status,
		"icon": "lucide-file-text",
	}
