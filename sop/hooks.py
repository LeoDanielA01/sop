app_name = "sop"
app_title = "SOP"
app_publisher = "Leo Daniel"
app_description = "Standard operating procedures with live record context"
app_email = "daniel@onebook.app"
app_license = "mit"

required_apps = ["frappe"]

website_route_rules = [{"from_route": "/sop/<path:app_path>", "to_route": "sop"}]

website_redirects = [{"source": "/procedures", "target": "/sop"}]

after_install = "sop.install.after_install"
after_migrate = "sop.install.after_migrate"

scheduler_events = {
	"daily": [
		"sop.training.mark_overdue",
		"sop.training.schedule_refreshers",
	]
}

sop_mention_resolvers = {}
