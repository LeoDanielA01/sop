app_name = "sop"
app_title = "SOP"
app_publisher = "Leo Daniel"
app_description = "Standard operating procedures with live record context"
app_email = "daniel@onebook.app"
app_license = "mit"

required_apps = ["frappe"]

# The SPA is served at /sop; vue-router owns everything below it.
website_route_rules = [{"from_route": "/sop/<path:app_path>", "to_route": "sop"}]

# Built by `cd frontend && yarn build` into sop/public/frontend,
# with the index written to sop/www/sop.html.
website_redirects = [{"source": "/procedures", "target": "/sop"}]

after_install = "sop.install.after_install"
after_migrate = "sop.install.after_migrate"

scheduler_events = {
	"daily": [
		"sop.training.mark_overdue",
		"sop.training.schedule_refreshers",
	]
}

# Mention chips. A resolver answers "what is true about this record right now?"
# and returns {"label": str, "url": str, "badges": [{"label": str, "tone": str}]}.
# Anything without a resolver falls back to SOP Mention Config, then to the doctype meta.
sop_mention_resolvers = {}
