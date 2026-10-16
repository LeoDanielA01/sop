# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

"""Move SOP Chemical and SOP PPE into the generic SOP Resource, keeping every link.

Reads the old tables directly: their DocType files are gone, and migrate drops
the orphaned doctypes only after the patches have run."""

import re
from html import escape, unescape

import frappe

OLD_CHEMICAL = "SOP Chemical"
OLD_PPE = "SOP PPE"
NEW = "SOP Resource"

PPE_TYPE = {
	"type_name": "PPE",
	"icon": "lucide-hard-hat",
	"is_tree": 1,
	"show_in_procedure": 1,
	"can_be_issued": 1,
	"description": "Personal protective equipment, grouped from kind down to the exact model.",
	"attributes": [{"label": "Standard", "fieldtype": "Data", "show_in_procedure": 1}],
}

HAZARD_CLASSES = "\n".join(
	[
		"Flammable",
		"Corrosive",
		"Acute toxicity",
		"Health hazard",
		"Irritant",
		"Oxidiser",
		"Explosive",
		"Compressed gas",
		"Environmental",
		"Not classified",
	]
)

CHEMICAL_TYPE = {
	"type_name": "Chemical",
	"icon": "lucide-flask-conical",
	"is_tree": 0,
	"show_in_procedure": 1,
	"can_be_issued": 0,
	"document_label": "Safety Data Sheet",
	"review_label": "SDS Review",
	"description": "Chemicals with their hazards, precautions and safety data sheet.",
	"attributes": [
		{"label": "CAS Number", "fieldtype": "Data", "show_in_procedure": 0},
		{"label": "Signal Word", "fieldtype": "Select", "options": "Danger\nWarning", "show_in_procedure": 1},
		{"label": "Hazard Class", "fieldtype": "Select", "options": HAZARD_CLASSES, "show_in_procedure": 1},
		{"label": "Precautions", "fieldtype": "Text", "show_in_procedure": 1},
		{"label": "Exposure Risks", "fieldtype": "Text", "show_in_procedure": 1},
		{"label": "First Aid", "fieldtype": "Text", "show_in_procedure": 1},
		{"label": "Storage And Disposal", "fieldtype": "Text", "show_in_procedure": 0},
	],
}

CHEMICAL_VALUES = {
	"cas_number": "CAS Number",
	"signal_word": "Signal Word",
	"hazard_class": "Hazard Class",
	"precautions": "Precautions",
	"exposure_risks": "Exposure Risks",
	"first_aid": "First Aid",
	"storage": "Storage And Disposal",
}

RECORD_TYPE = {
	"reference_doctype": NEW,
	"label": "Resource",
	"icon": "lucide-boxes",
	"fields_to_show": "",
	"in_safety": 1,
}

LINK = re.compile(r'href="#mention:(SOP Chemical|SOP PPE):([^"]+)"')
LEGACY = re.compile(r'data-doctype="(SOP Chemical|SOP PPE)" data-name="([^"]+)"')

RICH_TEXT = [("SOP", "content"), ("SOP Revision", "content"), ("SOP Training Session", "notes")]


def execute():
	renamed = {}

	if frappe.db.table_exists(OLD_PPE) and frappe.db.sql(f"select count(*) from `tab{OLD_PPE}`")[0][0]:
		ensure_type(PPE_TYPE)
		renamed[OLD_PPE] = copy_ppe()

	if frappe.db.table_exists(OLD_CHEMICAL) and frappe.db.sql(f"select count(*) from `tab{OLD_CHEMICAL}`")[0][0]:
		ensure_type(CHEMICAL_TYPE)
		renamed[OLD_CHEMICAL] = copy_chemicals(renamed.get(OLD_PPE, {}))

	if renamed:
		relink(renamed)

	switch_record_types()
	frappe.db.delete("Custom Field", {"dt": OLD_PPE})
	frappe.db.delete("Custom Field", {"dt": OLD_CHEMICAL})
	frappe.clear_cache()


def ensure_type(definition):
	if frappe.db.exists("SOP Resource Type", definition["type_name"]):
		return

	frappe.get_doc({"doctype": "SOP Resource Type", **definition}).insert(ignore_permissions=True)


def free_name(name, resource_type):
	"""Keep the old name unless a resource of another type already has it."""
	existing = frappe.db.get_value(NEW, name, "resource_type")
	if not existing or existing == resource_type:
		return name

	return f"{name} ({resource_type})"


def copy_ppe():
	has_item = frappe.db.has_column(OLD_PPE, "item")
	columns = "name, parent_sop_ppe, is_group, standard, is_consumable, image, description"
	if has_item:
		columns += ", item"

	rows = frappe.db.sql(f"select {columns} from `tab{OLD_PPE}` order by lft asc", as_dict=True)
	names = {row.name: free_name(row.name, "PPE") for row in rows}

	for row in rows:
		new_name = names[row.name]
		if frappe.db.exists(NEW, new_name):
			continue

		doc = frappe.get_doc(
			{
				"doctype": NEW,
				"resource_name": new_name,
				"resource_type": "PPE",
				"parent_sop_resource": names.get(row.parent_sop_ppe) if row.parent_sop_ppe else None,
				"is_group": row.is_group,
				"is_consumable": row.is_consumable,
				"image": row.image,
				"description": row.description,
				"values": [{"attribute": "Standard", "value": row.standard}],
			}
		)
		if has_item and frappe.get_meta(NEW).has_field("item"):
			doc.item = row.item
		doc.insert(ignore_permissions=True)

	return names


def copy_chemicals(ppe_names):
	rows = frappe.db.sql(f"select * from `tab{OLD_CHEMICAL}` order by creation asc", as_dict=True)
	names = {row.name: free_name(row.name, "Chemical") for row in rows}

	required = {}
	if frappe.db.table_exists("SOP Chemical PPE"):
		for link in frappe.db.sql(
			"select parent, ppe from `tabSOP Chemical PPE` where parenttype = %s order by idx asc",
			OLD_CHEMICAL,
			as_dict=True,
		):
			required.setdefault(link.parent, []).append(ppe_names.get(link.ppe, link.ppe))

	for row in rows:
		new_name = names[row.name]
		if frappe.db.exists(NEW, new_name):
			continue

		frappe.get_doc(
			{
				"doctype": NEW,
				"resource_name": new_name,
				"resource_type": "Chemical",
				"disabled": row.get("disabled") or 0,
				"document": row.get("sds"),
				"check_date": row.get("sds_review_date"),
				"values": [
					{"attribute": label, "value": row.get(fieldname)} for fieldname, label in CHEMICAL_VALUES.items()
				],
				"requires": [
					{"resource": name} for name in required.get(row.name, []) if frappe.db.exists(NEW, name)
				],
			}
		).insert(ignore_permissions=True)

	return names


def relink(renamed):
	def target(doctype, name):
		return renamed.get(doctype, {}).get(unescape(name), unescape(name))

	def swap_link(match):
		return f'href="#mention:{NEW}:{escape(target(match.group(1), match.group(2)), quote=True)}"'

	def swap_legacy(match):
		return f'data-doctype="{NEW}" data-name="{escape(target(match.group(1), match.group(2)), quote=True)}"'

	for doctype, field in RICH_TEXT:
		if not frappe.db.table_exists(doctype) or not frappe.db.has_column(doctype, field):
			continue

		for row in frappe.db.sql(
			f"""select name, `{field}` as content from `tab{doctype}`
			where `{field}` like '%%SOP Chemical%%' or `{field}` like '%%SOP PPE%%'""",
			as_dict=True,
		):
			updated = LEGACY.sub(swap_legacy, LINK.sub(swap_link, row.content or ""))
			if updated != row.content:
				frappe.db.set_value(doctype, row.name, field, updated, update_modified=False)

	for old_doctype, names in renamed.items():
		for old_name, new_name in names.items():
			frappe.db.sql(
				"""update `tabSOP Reference` set reference_doctype = %s, reference_name = %s
				where reference_doctype = %s and reference_name = %s""",
				(NEW, new_name, old_doctype, old_name),
			)


def switch_record_types():
	doc = frappe.get_doc("SOP Settings")
	kept = []
	placed = False

	for row in doc.record_types:
		if row.reference_doctype in (OLD_CHEMICAL, OLD_PPE, NEW):
			if not placed:
				kept.append(frappe._dict(RECORD_TYPE))
				placed = True
			continue
		kept.append(row)

	if not placed:
		kept.append(frappe._dict(RECORD_TYPE))

	doc.set("record_types", [])
	for row in kept:
		doc.append(
			"record_types",
			{
				"reference_doctype": row.reference_doctype,
				"label": row.label,
				"icon": row.icon,
				"fields_to_show": row.fields_to_show,
				"in_safety": row.in_safety,
			},
		)

	doc.save(ignore_permissions=True)
