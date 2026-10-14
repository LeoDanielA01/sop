import frappe

DEFAULTS = [
	{
		"reference_doctype": "SOP Chemical",
		"label": "Chemical",
		"icon": "lucide-flask-conical",
		"fields_to_show": "hazard_class\nsignal_word\nprecautions\nexposure_risks\nfirst_aid\nsds\nsds_review_date",
		"in_safety": 1,
	},
	{
		"reference_doctype": "SOP PPE",
		"label": "PPE",
		"icon": "lucide-hard-hat",
		"fields_to_show": "standard\ndescription",
		"in_safety": 1,
	},
]


def execute():
	doc = frappe.get_doc("SOP Settings")
	present = {row.reference_doctype for row in doc.record_types}
	for row in DEFAULTS:
		if row["reference_doctype"] not in present:
			doc.append("record_types", row)

	doc.save(ignore_permissions=True)
