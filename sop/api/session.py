# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _

API_PREFIXES = ("/api/method/sop.", "/api/v2/method/sop.")
APP_ROLES = (
	"SOP Manager",
	"SOP Author",
	"SOP Approver",
	"SOP Reviewer",
	"SOP Trainer",
	"SOP Reader",
)


@frappe.whitelist()
def me():
	from sop.api.settings import resolved

	user = frappe.get_cached_doc("User", frappe.session.user)
	roles = frappe.get_roles()

	return {
		"name": user.name,
		"full_name": user.full_name,
		"image": user.user_image,
		"is_manager": "SOP Manager" in roles,
		"is_admin": "System Manager" in roles or frappe.session.user == "Administrator",
		"is_author": bool({"SOP Author", "SOP Manager"} & set(roles)),
		"is_approver": bool({"SOP Approver", "SOP Reviewer", "SOP Manager"} & set(roles)),
		"csrf_token": frappe.sessions.get_csrf_token(),
		**resolved(),
	}

@frappe.whitelist()
def realtime():
	return {
		"site_name": frappe.local.site,
		"socketio_port": frappe.conf.socketio_port or 9000,
		"sop_ice_servers": frappe.conf.get("sop_ice_servers"),
		"sop_user": me(),
	}


def guard_api():
	path = getattr(frappe.request, "path", "") or ""
	command = frappe.form_dict.get("cmd") or ""

	if not path.startswith(API_PREFIXES) and not command.startswith("sop."):
		return

	if not can_use_app():
		frappe.throw(_("You do not have access to the SOP app."), frappe.PermissionError)


def can_use_app(user=None):
	roles = set(frappe.get_roles(user or frappe.session.user))

	return bool(
		roles
		& {
			"SOP Manager",
			"SOP Author",
			"SOP Approver",
			"SOP Reviewer",
			"SOP Trainer",
			"SOP Reader",
			"System Manager",
		}
	)


@frappe.whitelist()
def profile():
	user = frappe.session.user
	doc = frappe.get_cached_doc("User", user)

	teams = frappe.get_all(
		"SOP Team Member",
		filters={"user": user, "parenttype": "SOP Team"},
		fields=["parent", "team_role"],
		limit_page_length=0,
	)

	roles = frappe.get_roles()
	if "SOP Manager" in roles:
		role = "Manager"
	elif bool({"SOP Author", "SOP Manager"} & set(roles)):
		role = "Author"
	else:
		role = "Reader"

	held = [name.removeprefix("SOP ") for name in APP_ROLES if name in roles]

	return {
		"full_name": doc.full_name,
		"email": doc.email,
		"phone": doc.phone or "",
		"mobile_no": doc.mobile_no or "",
		"bio": doc.bio or "",
		"location": doc.location or "",
		"username": doc.username or "",
		"member_since": doc.creation,
		"last_active": doc.last_active,
		"role": role,
		"roles": held,
		"time_zone": doc.time_zone or "",
		"language": doc.language or "",
		"teams": [{"name": row.parent, "role": row.team_role} for row in teams],
	}
