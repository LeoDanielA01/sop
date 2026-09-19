app_name = "sop"
app_title = "SOP"
app_publisher = "Leo Daniel"
app_description = "Standard operating procedures with live record context"
app_email = "daniel@onebook.app"
app_license = "mit"

required_apps = ["frappe"]

add_to_apps_screen = [
	{
		"name": "sop",
		"logo": "/assets/sop/images/sop-mark.svg",
		"title": "Procedures",
		"route": "/sop",
		"has_permission": "sop.api.session.can_use_app",
	}
]

website_route_rules = [
	{"from_route": "/sop/<path:app_path>", "to_route": "sop"},
]

website_redirects = [{"source": "/procedures", "target": "/sop"}]

after_install = "sop.install.after_install"
after_migrate = "sop.install.after_migrate"

sqlite_search = ["sop.sop.doctype.sop.sop_sqlite_search.SOPSQLiteSearch"]

sop_mention_facts = {
	"Item": ["sop.mention_facts.item"],
	"Warehouse": ["sop.mention_facts.warehouse"],
}

scheduler_events = {
	"daily": [
		"sop.training.mark_overdue",
		"sop.training.schedule_refreshers",
		"sop.training.sync_requirements",
		"sop.training.remind",
	]
}