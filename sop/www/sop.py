import frappe

no_cache = 1

SPA_PATH = "/sop"


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = f"/login?redirect-to={SPA_PATH}"
		raise frappe.Redirect

	context.boot = boot()
	frappe.db.commit()

	return context


def boot():
	user = frappe.get_cached_doc("User", frappe.session.user)
	roles = frappe.get_roles()

	return {
		"csrf_token": frappe.sessions.get_csrf_token(),
		"site_name": frappe.local.site,
		"sop_path": SPA_PATH,
		"sop_user": {
			"name": user.name,
			"full_name": user.full_name,
			"image": user.user_image,
			"is_manager": "SOP Manager" in roles,
			"is_author": bool({"SOP Author", "SOP Manager"} & set(roles)),
		},
	}
