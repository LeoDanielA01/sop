# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

from urllib.parse import quote

import frappe
from frappe import _
from frappe.model import no_value_fields, table_fields
from frappe.utils import cint, date_diff, getdate, nowdate

CACHE_TTL = 60
CACHE_PREFIX = "sop:mention"

LONG_TEXT = {
	"Text",
	"Small Text",
	"Long Text",
	"Text Editor",
	"HTML Editor",
	"Markdown Editor",
	"Code",
	"JSON",
	"Password",
	"Signature",
	"Geolocation",
	"Attach",
	"Attach Image",
}

DEADLINE_WORDS = (
	"expir",
	"valid_upto",
	"valid_till",
	"valid_until",
	"due",
	"deadline",
	"end_date",
	"to_date",
	"warranty",
	"renew",
	"calibration",
	"next_",
	"maturity",
	"review",
)

RED_WORDS = ("overdue", "expired", "cancel", "reject", "disabled", "lost", "stopped", "block", "fail")
AMBER_WORDS = ("not ", "unpaid", "partly", "partial", "pending", "draft", "to ", "open", "hold", "review")
GREEN_WORDS = (
	"complete",
	"paid",
	"active",
	"enabled",
	"submitted",
	"deliver",
	"approved",
	"effective",
	"closed",
	"available",
)


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
def doctypes(search=None, limit=12):
	filters = {"istable": 0, "issingle": 0}
	or_filters = {"name": ("like", f"%{search}%")} if search else None

	rows = frappe.get_all(
		"DocType",
		filters=filters,
		or_filters=or_filters,
		pluck="name",
		order_by="name asc",
		limit_page_length=300,
	)

	used = most_mentioned()
	typed = (search or "").lower()

	allowed = [name for name in rows if frappe.has_permission(name, "read")]
	allowed.sort(
		key=lambda name: (not name.lower().startswith(typed), -used.get(name, 0), len(name), name)
	)

	return allowed[: cint(limit) or 12]


@frappe.whitelist()
def find(doctype, text=None, limit=10):
	doctype = type_named(doctype)
	if not doctype:
		return []

	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("You are not allowed to read {0}.").format(doctype), frappe.PermissionError)

	title_field = frappe.get_meta(doctype).get_title_field()

	fields = ["name"]
	if title_field != "name":
		fields.append(title_field)

	or_filters = {}
	if text:
		like = f"%{text}%"
		or_filters["name"] = ("like", like)
		if title_field != "name":
			or_filters[title_field] = ("like", like)

	rows = frappe.get_list(
		doctype,
		or_filters=or_filters or None,
		fields=fields,
		limit_page_length=cint(limit) or 10,
	)

	return [{"name": row.name, "label": row.get(title_field) or row.name} for row in rows]


@frappe.whitelist()
def card(doctype, name):
	doctype = type_named(doctype) or doctype

	if not frappe.db.exists("DocType", doctype) or not frappe.db.exists(doctype, name):
		return {"missing": True, "doctype": doctype, "name": name}

	if not frappe.has_permission(doctype, "read", doc=name):
		return {"blocked": True, "doctype": doctype, "name": name}

	key = cache_key("card", doctype, name)
	cached = frappe.cache().get_value(key)
	if cached:
		return cached

	meta = frappe.get_meta(doctype)
	row, picked, deadlines = read(meta, name)
	status = status_of(meta, row)

	times = [fact for fact in (deadline_fact(df, row.get(df.fieldname)) for df in deadlines) if fact]
	values = [fact for fact in (value_fact(df, row) for df in picked) if fact]

	result = {
		"doctype": doctype,
		"name": name,
		"title": title_of(meta, row),
		"image": row.get(meta.image_field) if meta.image_field else None,
		"status": status,
		"status_tone": tone_of(status),
		"facts": extras_for(doctype, name) + times + values + table_facts(meta, name),
		"counts": counts_for(doctype, name),
		"url": frappe.utils.get_url_to_form(doctype, name),
	}

	frappe.cache().set_value(key, result, expires_in_sec=CACHE_TTL)

	return result


def type_named(text):
	text = (text or "").strip()
	if not text:
		return None

	exact = frappe.db.get_value("DocType", {"name": text, "istable": 0}, "name")
	if exact:
		return exact

	candidates = frappe.get_all(
		"DocType",
		filters={"istable": 0, "issingle": 0, "name": ("like", f"%{text}%")},
		pluck="name",
		limit_page_length=50,
	)
	readable = [name for name in candidates if frappe.has_permission(name, "read")]
	starts = [name for name in readable if name.lower().startswith(text.lower())]

	if not starts:
		return readable[0] if len(readable) == 1 else None

	used = most_mentioned()

	return sorted(starts, key=lambda name: (-used.get(name, 0), len(name), name))[0]


def most_mentioned():
	counts = {}

	for doctype in frappe.get_all(
		"SOP Reference", filters={"parenttype": "SOP"}, pluck="reference_doctype", limit_page_length=0
	):
		counts[doctype] = counts.get(doctype, 0) + 1

	return counts


def resolve_doctype(doctype, names):
	out = []
	pending = []

	for name in names:
		cached = frappe.cache().get_value(cache_key("chip", doctype, name))
		if cached:
			out.append(cached)
		else:
			pending.append(name)

	if not pending:
		return out

	known = frappe.db.exists("DocType", doctype)
	readable = [
		name for name in pending if known and frappe.has_permission(doctype, "read", doc=name)
	]
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
				cache_key("chip", doctype, row["reference_name"]), row, expires_in_sec=CACHE_TTL
			)

	return out


def resolver_for(doctype):
	registered = (frappe.get_hooks("sop_mention_resolvers") or {}).get(doctype)
	if registered:
		return frappe.get_attr(registered[0] if isinstance(registered, list) else registered)

	return generic


def generic(doctype, names):
	meta = frappe.get_meta(doctype)
	out = []

	for name in names:
		if not frappe.db.exists(doctype, name):
			out.append(plain(doctype, name))
			continue

		found = read(meta, name)
		row, deadlines = found[0], found[2]
		status = status_of(meta, row)

		badges = []
		if status:
			badges.append({"label": status, "tone": tone_of(status)})

		urgent = headline(
			extras_for(doctype, name)
			+ [fact for fact in (deadline_fact(df, row.get(df.fieldname)) for df in deadlines) if fact]
		)
		if urgent:
			badges.append({"label": urgent.get("short") or f"{urgent['label']}: {urgent['value']}", "tone": urgent["tone"]})

		out.append(chip(doctype, name, title_of(meta, row), badges))

	return out


def headline(facts):
	for fact in facts:
		if fact.get("tone") in ("red", "amber"):
			return fact

	for fact in facts:
		if fact.get("headline"):
			return fact

	return None


def read(meta, name):
	picked = key_fields(meta)
	deadlines = [df for df in deadline_fields(meta) if df not in picked]

	fields = {"name", "docstatus"}
	for fieldname in (meta.get_title_field(), meta.image_field, "status", "disabled", "enabled"):
		if fieldname and (fieldname == "name" or meta.has_field(fieldname)):
			fields.add(fieldname)

	for df in picked + deadlines:
		fields.add(df.fieldname)
		if df.fieldtype == "Currency" and df.options and meta.has_field(df.options):
			fields.add(df.options)

	rows = frappe.get_all(meta.name, filters={"name": name}, fields=sorted(fields), limit_page_length=1)

	return (rows[0] if rows else frappe._dict(name=name)), picked, deadlines


def usable_fields(meta):
	skip = {meta.get_title_field(), meta.image_field, "status", "disabled", "enabled"}

	return [
		df
		for df in meta.fields
		if df.fieldtype not in no_value_fields
		and df.fieldtype not in table_fields
		and df.fieldtype not in LONG_TEXT
		and not df.hidden
		and df.fieldname not in skip
	]


def key_fields(meta, limit=6):
	usable = usable_fields(meta)
	picked = []

	for flag in ("in_preview", "bold", "in_list_view", "in_standard_filter", "reqd"):
		for df in usable:
			if df.get(flag) and df not in picked and df.fieldtype not in ("Date", "Datetime"):
				picked.append(df)

		if len(picked) >= limit:
			break

	return picked[:limit]


def deadline_fields(meta, limit=3):
	found = []

	for df in usable_fields(meta):
		if df.fieldtype not in ("Date", "Datetime"):
			continue

		text = f"{df.fieldname} {(df.label or '').lower()}"
		if any(word in text for word in DEADLINE_WORDS):
			found.append(df)

	return found[:limit]


def title_of(meta, row):
	title_field = meta.get_title_field()

	return (row.get(title_field) if title_field else None) or row.get("name")


def status_of(meta, row):
	if meta.has_field("status") and row.get("status"):
		return row.get("status")

	if meta.is_submittable:
		return {0: _("Draft"), 1: _("Submitted"), 2: _("Cancelled")}.get(cint(row.get("docstatus")))

	if meta.has_field("disabled") and cint(row.get("disabled")):
		return _("Disabled")

	if meta.has_field("enabled") and not cint(row.get("enabled")):
		return _("Disabled")

	return None


def tone_of(label):
	text = (label or "").lower()
	if not text:
		return "gray"

	if any(word in text for word in RED_WORDS):
		return "red"

	if any(word in text for word in AMBER_WORDS):
		return "amber"

	if any(word in text for word in GREEN_WORDS):
		return "green"

	return "gray"


def relative(days):
	if days == 0:
		return _("today")

	if days == 1:
		return _("tomorrow")

	if days == -1:
		return _("yesterday")

	if days > 0:
		return _("in {0} days").format(days)

	return _("{0} days ago").format(-days)


def urgency(days):
	if days <= 0:
		return "red"

	return "amber" if days <= 30 else "gray"


def deadline_fact(df, value):
	if not value:
		return None

	days = date_diff(getdate(value), getdate(nowdate()))
	label = _(df.label or frappe.unscrub(df.fieldname))
	when = relative(days)

	return {
		"label": label,
		"value": f"{frappe.format_value(getdate(value), {'fieldtype': 'Date'})} · {when}",
		"short": f"{label} {when}",
		"tone": urgency(days),
		"days": days,
	}


def value_fact(df, row):
	value = row.get(df.fieldname)
	if value in (None, "") or not value:
		return None

	if df.fieldtype == "Check":
		shown = _("Yes")
	elif df.fieldtype == "Link" and df.options:
		shown = link_title(df.options, value)
	else:
		shown = frappe.utils.strip_html(str(frappe.format_value(value, df=df, doc=row)))

	return {"label": _(df.label or frappe.unscrub(df.fieldname)), "value": shown, "tone": "gray"}


def link_title(doctype, value):
	try:
		title_field = frappe.get_meta(doctype).get_title_field()
	except Exception:
		return str(value)

	if title_field == "name":
		return str(value)

	title = frappe.db.get_value(doctype, value, title_field)

	return f"{title} ({value})" if title and title != value else str(value)


def table_facts(meta, name, limit=3):
	facts = []

	for df in [df for df in meta.get_table_fields() if not df.hidden][:limit]:
		rows = frappe.db.count(
			df.options, {"parent": name, "parenttype": meta.name, "parentfield": df.fieldname}
		)
		if not rows:
			continue

		facts.append(
			{
				"label": _(df.label or frappe.unscrub(df.fieldname)),
				"value": _("1 row") if rows == 1 else _("{0} rows").format(rows),
				"tone": "gray",
			}
		)

	return facts


def extras_for(doctype, name):
	facts = []

	for path in (frappe.get_hooks("sop_mention_facts") or {}).get(doctype, []):
		try:
			facts += frappe.get_attr(path)(name) or []
		except Exception:
			frappe.log_error(title=f"SOP mention facts failed for {doctype}")

	return facts


def counts_for(doctype, name):
	try:
		links = frappe.get_meta(doctype).get_dashboard_data()
		rows = dashboard_counts(doctype, name, links) if links and links.get("transactions") else []
		rows = rows or reverse_counts(doctype, name)
	except Exception:
		frappe.log_error(title=f"SOP mention counts failed for {doctype}")
		return []

	rows.sort(key=lambda row: -row["count"])

	return rows[:6]


def dashboard_counts(doctype, name, links):
	from frappe.desk.notifications import get_open_count

	found = (get_open_count(doctype, name) or {}).get("count") or {}
	fieldnames = links.get("non_standard_fieldnames") or {}
	out = []

	for row in (found.get("internal_links_found") or []) + (found.get("external_links_found") or []):
		total = cint(row.get("count"))
		if not total:
			continue

		opened = cint(row.get("open_count"))
		fieldname = None if row.get("names") is not None else fieldnames.get(row["doctype"], links.get("fieldname"))

		out.append(
			{
				"doctype": row["doctype"],
				"count": total,
				"label": f"{total} · {opened} {_('open')}" if opened else str(total),
				"route": list_route(row["doctype"], fieldname, name),
			}
		)

	return out


def reverse_counts(doctype, name):
	from frappe.desk.form.linked_with import get_linked_doctypes

	out = []

	for linked, info in list((get_linked_doctypes(doctype) or {}).items())[:12]:
		if info.get("child_doctype") or info.get("doctype_fieldname") or info.get("get_parent"):
			continue

		fields = info.get("fieldname") or []
		fields = [fields] if isinstance(fields, str) else list(fields)
		if not fields or not frappe.has_permission(linked, "read"):
			continue

		found = frappe.get_all(
			linked,
			or_filters=[[linked, field, "=", name] for field in fields],
			pluck="name",
			limit_page_length=101,
		)
		if not found:
			continue

		total = len(found)
		out.append(
			{
				"doctype": linked,
				"count": total,
				"label": "100+" if total > 100 else str(total),
				"route": list_route(linked, fields[0], name),
			}
		)

	return out


def list_route(doctype, fieldname, name):
	slug = frappe.scrub(doctype).replace("_", "-")

	if not fieldname:
		return f"/app/{slug}"

	return f"/app/{slug}?{fieldname}={quote(str(name))}"


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


def cache_key(kind, doctype, name):
	return f"{CACHE_PREFIX}:{kind}:{frappe.session.user}:{doctype}:{name}"
