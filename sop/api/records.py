from urllib.parse import quote

import frappe
from frappe import _
from frappe.model import no_value_fields, table_fields
from frappe.utils import cint, flt, strip_html

from sop.api.mentions import card, key_fields, link_title, record_url, status_of, tone_of, type_label, value_fact
from sop.api.settings import record_type

PAGE = 50
TABLE_ROWS = 50
TABLE_COLUMNS = 5
LONG_TEXT = {"Text Editor", "Text", "Long Text", "Small Text", "Markdown Editor", "HTML Editor", "Code", "JSON"}
FILES = {"Attach", "Attach Image"}
NUMBERS = {"Int", "Float", "Currency", "Percent"}


def readable(doctype):
	if not doctype or not frappe.db.exists("DocType", doctype):
		frappe.throw(_("{0} is not a record type on this site.").format(doctype or "?"))
	meta = frappe.get_meta(doctype)
	if meta.istable or meta.issingle:
		frappe.throw(_("{0} cannot be shown as a list of records.").format(doctype))
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("You are not allowed to see {0}.").format(_(doctype)), frappe.PermissionError)
	return meta


def list_path(doctype):
	return f"/sop/records/{quote(doctype)}"


def header(doctype):
	configured = record_type(doctype)
	return {
		"doctype": doctype,
		"type_label": type_label(doctype),
		"icon": (configured.icon if configured else None) or None,
	}


def clean_filters(meta, filters):
	if not isinstance(filters, dict):
		return {}
	return {key: value for key, value in filters.items() if meta.has_field(key) and isinstance(value, (str, int, float))}


@frappe.whitelist()
def get_list(doctype, search=None, filters=None, start=0):
	meta = readable(doctype)
	filters = clean_filters(meta, frappe.parse_json(filters) if isinstance(filters, str) else filters)
	title_field = meta.get_title_field()
	columns = [df for df in key_fields(meta, limit=4) if df.fieldname != title_field][:4]
	fields = ["name", title_field]
	if meta.image_field:
		fields.append(meta.image_field)
	if meta.has_field("status"):
		fields.append("status")
	fields += [df.fieldname for df in columns]
	fields = list(dict.fromkeys(fields))

	or_filters = None
	if search:
		like = f"%{search.strip()}%"
		or_filters = {"name": ["like", like]}
		if title_field != "name":
			or_filters[title_field] = ["like", like]

	rows = frappe.get_list(
		doctype,
		fields=fields,
		filters=filters,
		or_filters=or_filters,
		order_by="modified desc",
		start=cint(start),
		page_length=PAGE + 1,
	)

	out = []
	for row in rows[:PAGE]:
		status = status_of(meta, row)
		values = {}
		for df in columns:
			fact = value_fact(df, row)
			values[df.fieldname] = fact["value"] if fact else ""
		out.append(
			{
				"name": row.name,
				"title": row.get(title_field) or row.name,
				"image": row.get(meta.image_field) if meta.image_field else None,
				"status": status,
				"status_tone": tone_of(status) if status else None,
				"values": values,
				"url": record_url(doctype, row.name),
			}
		)

	return {
		**header(doctype),
		"filters": filters,
		"columns": [{"key": df.fieldname, "label": _(df.label or frappe.unscrub(df.fieldname))} for df in columns],
		"rows": out,
		"more": len(rows) > PAGE,
	}


@frappe.whitelist()
def get_record(doctype, name):
	meta = readable(doctype)
	base = card(doctype, name)
	if base.get("missing") or base.get("blocked"):
		return {**header(doctype), **base}

	doc = frappe.get_doc(doctype, name)
	doc.apply_fieldlevel_read_permissions()

	return {
		**header(doctype),
		**base,
		"groups": field_groups(meta, doc),
		"list_url": list_path(doctype),
	}


def field_groups(meta, doc):
	groups = []
	current = {"label": None, "fields": [], "tables": []}
	skip = {meta.get_title_field(), meta.image_field}

	for df in meta.fields:
		if df.fieldtype in ("Section Break", "Tab Break"):
			if current["fields"] or current["tables"]:
				groups.append(current)
			current = {"label": _(df.label) if df.label else None, "fields": [], "tables": []}
			continue
		if df.hidden or df.fieldname in skip:
			continue
		if df.fieldtype in table_fields:
			table = child_table(df, doc)
			if table:
				current["tables"].append(table)
			continue
		if df.fieldtype in no_value_fields:
			continue
		entry = field_value(df, doc)
		if entry:
			current["fields"].append(entry)

	if current["fields"] or current["tables"]:
		groups.append(current)
	return groups


def field_value(df, doc):
	value = doc.get(df.fieldname)
	if value in (None, "") or (df.fieldtype == "Check" and not cint(value)):
		return None
	if df.fieldtype in NUMBERS and not flt(value):
		return None

	entry = {"key": df.fieldname, "label": _(df.label or frappe.unscrub(df.fieldname))}

	if df.fieldtype == "Link" and df.options:
		return {**entry, **linked(df.options, value)}
	if df.fieldtype == "Dynamic Link" and doc.get(df.options):
		return {**entry, **linked(doc.get(df.options), value)}
	if df.fieldtype in FILES:
		return {**entry, "value": str(value).rsplit("/", 1)[-1], "file": value}
	if df.fieldtype in LONG_TEXT:
		return {**entry, "value": strip_html(str(value)).strip(), "long": True}
	if df.fieldtype == "Check":
		return {**entry, "value": _("Yes")}

	return {**entry, "value": strip_html(str(frappe.format_value(value, df=df, doc=doc)))}


def linked(doctype, name):
	return {
		"value": link_title(doctype, name),
		"link": record_url(doctype, name),
		"link_doctype": doctype,
		"link_name": name,
	}


def child_table(df, doc):
	rows = doc.get(df.fieldname) or []
	if not rows or not df.options:
		return None

	child = frappe.get_meta(df.options)
	usable = [
		field
		for field in child.fields
		if not field.hidden and field.fieldtype not in no_value_fields and field.fieldtype not in LONG_TEXT
	]
	columns = [field for field in usable if field.in_list_view] or usable
	columns = [field for field in columns if any(row.get(field.fieldname) not in (None, "") for row in rows)][:TABLE_COLUMNS]
	if not columns:
		return None

	return {
		"key": df.fieldname,
		"label": _(df.label or frappe.unscrub(df.fieldname)),
		"columns": [{"key": field.fieldname, "label": _(field.label or frappe.unscrub(field.fieldname))} for field in columns],
		"rows": [
			{field.fieldname: (field_value(field, row) or {"value": ""}) for field in columns} for row in rows[:TABLE_ROWS]
		],
		"count": len(rows),
	}


def section_enabled(doctype, flag):
	configured = record_type(doctype)
	if not configured:
		return True
	value = configured.get(flag)
	return True if value is None else bool(cint(value))


def extra_sections(doctype, name):
	sections = []
	if doctype == "Item" and section_enabled("Item", "show_stock_by_warehouse"):
		stock = stock_by_warehouse(name)
		if stock:
			sections.append(stock)
	return sections


def stock_by_warehouse(item_code):
	if not frappe.db.exists("DocType", "Bin"):
		return None

	uom = frappe.db.get_value("Item", item_code, "stock_uom") or ""
	bins = frappe.get_all(
		"Bin",
		filters={"item_code": item_code},
		fields=[
			"warehouse",
			"actual_qty",
			"reserved_qty",
			"reserved_qty_for_production",
			"reserved_qty_for_sub_contract",
			"ordered_qty",
			"planned_qty",
			"indented_qty",
			"projected_qty",
			"stock_value",
		],
		order_by="actual_qty desc",
		limit_page_length=0,
	)

	rows = []
	for row in bins:
		reserved = flt(row.reserved_qty) + flt(row.reserved_qty_for_production) + flt(row.reserved_qty_for_sub_contract)
		incoming = flt(row.ordered_qty) + flt(row.planned_qty) + flt(row.indented_qty)
		if not any((flt(row.actual_qty), reserved, incoming, flt(row.projected_qty))):
			continue
		rows.append(
			{
				"warehouse": row.warehouse,
				"warehouse_url": record_url("Warehouse", row.warehouse),
				"on_hand": flt(row.actual_qty),
				"reserved": reserved,
				"incoming": incoming,
				"projected": flt(row.projected_qty),
				"value": flt(row.stock_value),
			}
		)

	totals = {
		key: sum(row[key] for row in rows) for key in ("on_hand", "reserved", "incoming", "projected", "value")
	}
	return {
		"key": "stock_by_warehouse",
		"title": _("Stock by warehouse"),
		"uom": uom,
		"currency": frappe.defaults.get_global_default("currency"),
		"rows": rows,
		"totals": totals,
	}
