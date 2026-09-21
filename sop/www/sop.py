import frappe
from frappe import _

from sop.api.session import can_use_app, realtime

no_cache = 1

SPA_PATH = "/sop"


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = f"/login?redirect-to={SPA_PATH}"
		raise frappe.Redirect

	if not can_use_app():
		frappe.throw(_("You do not have access to the SOP app."), frappe.PermissionError)

	context.boot = boot()
	frappe.db.commit()

	return context


def boot():
	return {"csrf_token": frappe.sessions.get_csrf_token(), "sop_path": SPA_PATH, **realtime()}
