import frappe


def execute():
	for name in frappe.get_all("SOP", pluck="name", limit_page_length=0):
		doc = frappe.get_doc("SOP", name)
		doc.build_search_text()
		frappe.db.set_value("SOP", name, "search_text", doc.search_text, update_modified=False)

	frappe.enqueue(
		"sop.api.search.rebuild_nightly",
		queue="long",
		job_id="sop_search_rebuild_after_patch",
		deduplicate=True,
		enqueue_after_commit=True,
	)
