import frappe
from frappe import _

ROLES = ("Reader", "Author", "Reviewer", "Approver")


@frappe.whitelist()
def teams() -> list[dict]:
	rows = frappe.get_list(
		"SOP Team",
		fields=["name", "team_name", "description"],
		order_by="team_name asc",
		limit_page_length=0,
	)
	if not rows:
		return []

	names = [row.name for row in rows]
	members = frappe.get_all(
		"SOP Team Member",
		filters={"parenttype": "SOP Team", "parent": ("in", names)},
		fields=["parent", "user", "team_role"],
		order_by="idx asc",
		limit_page_length=0,
	)
	users = {
		row.name: row
		for row in frappe.get_all(
			"User",
			filters={"name": ("in", list({row.user for row in members}) or [""])},
			fields=["name", "full_name", "user_image", "enabled"],
			limit_page_length=0,
		)
	}
	spaces = frappe.get_all(
		"SOP Space",
		filters={"team": ("in", names)},
		fields=["name", "title", "team"],
		order_by="title asc",
		limit_page_length=0,
	)

	for row in rows:
		row.members = [
			{
				"user": member.user,
				"team_role": member.team_role or "Reader",
				"full_name": users.get(member.user, {}).get("full_name") or member.user,
				"user_image": users.get(member.user, {}).get("user_image"),
				"enabled": users.get(member.user, {}).get("enabled", 0),
			}
			for member in members
			if member.parent == row.name
		]
		row.spaces = [{"name": space.name, "title": space.title} for space in spaces if space.team == row.name]

	return rows


@frappe.whitelist()
def save_team(team_name: str, members: list | str | None = None, description: str | None = None, name: str | None = None) -> dict:
	team_name = (team_name or "").strip()
	if not team_name:
		frappe.throw(_("Give the team a name."))

	rows = []
	seen = set()
	for row in frappe.parse_json(members) or []:
		user = row.get("user")
		if not user or user in seen:
			continue
		role = row.get("team_role") if row.get("team_role") in ROLES else "Reader"
		seen.add(user)
		rows.append({"user": user, "team_role": role})

	if name:
		doc = frappe.get_doc("SOP Team", name)
		doc.check_permission("write")
		if team_name != doc.name:
			if frappe.db.exists("SOP Team", team_name):
				frappe.throw(_("A team called {0} already exists.").format(frappe.bold(team_name)))
			frappe.rename_doc("SOP Team", doc.name, team_name, force=True)
			doc = frappe.get_doc("SOP Team", team_name)
	else:
		doc = frappe.new_doc("SOP Team")

	doc.team_name = team_name
	doc.description = description
	doc.set("members", rows)
	doc.save() if name else doc.insert()

	return {"name": doc.name}


@frappe.whitelist()
def delete_team(name: str) -> None:
	frappe.get_doc("SOP Team", name).check_permission("delete")
	used = frappe.get_all("SOP Space", filters={"team": name}, pluck="title")
	if used:
		frappe.throw(
			_("{0} is the team of {1}. Pick another team for those spaces first.").format(
				frappe.bold(name), ", ".join(used)
			)
		)
	frappe.delete_doc("SOP Team", name)


@frappe.whitelist()
def set_space_team(space: str, team: str | None = None) -> None:
	doc = frappe.get_doc("SOP Space", space)
	doc.check_permission("write")
	doc.team = team or None
	doc.save()
