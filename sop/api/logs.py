import frappe

FIELDS = (
	"log_type",
	"location",
	"location_text",
	"cleaning_type",
	"reason",
	"service_type",
	"product_before",
	"room_status",
	"checked_by",
	"notes",
)


@frappe.whitelist()
def locations(sop: str) -> list[dict]:
	frappe.get_doc("SOP", sop).check_permission("read")
	names = frappe.get_all(
		"SOP Reference",
		filters={"parenttype": "SOP", "parent": sop, "reference_doctype": "SOP Resource"},
		pluck="reference_name",
		distinct=True,
	)
	if not names:
		return []
	return frappe.get_all(
		"SOP Resource",
		filters={"name": ("in", names), "disabled": 0},
		fields=["name", "resource_name", "resource_type", "room_status", "room_status_on"],
		order_by="resource_name asc",
	)


@frappe.whitelist()
def create(sop: str, entry: dict | str) -> dict:
	frappe.get_doc("SOP", sop).check_permission("read")
	values = frappe.parse_json(entry) or {}
	doc = frappe.get_doc(
		{
			"doctype": "SOP Log Entry",
			"sop": sop,
			"done_by": frappe.session.user,
			**{key: values.get(key) for key in FIELDS if values.get(key)},
		}
	).insert()
	return {"name": doc.name}


@frappe.whitelist()
def recent(sop: str, limit: int = 10) -> list[dict]:
	frappe.get_doc("SOP", sop).check_permission("read")
	rows = frappe.get_all(
		"SOP Log Entry",
		filters={"sop": sop},
		fields=[
			"name",
			"log_type",
			"logged_at",
			"location",
			"location_text",
			"cleaning_type",
			"service_type",
			"room_status",
			"done_by",
			"checked_by",
			"notes",
		],
		order_by="logged_at desc",
		limit_page_length=int(limit) or 10,
	)
	names = {row.done_by for row in rows} | {row.checked_by for row in rows if row.checked_by}
	full = (
		dict(
			frappe.get_all(
				"User", filters={"name": ("in", list(names))}, fields=["name", "full_name"], as_list=True
			)
		)
		if names
		else {}
	)
	for row in rows:
		row.done_by_name = full.get(row.done_by) or row.done_by
		row.checked_by_name = full.get(row.checked_by) or row.checked_by
		row.where = row.location or row.location_text
	return rows
