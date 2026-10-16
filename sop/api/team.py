import frappe
from frappe import _


@frappe.whitelist()
def team_directory(search=None):
    filters = {"enabled": 1, "user_type": "System User"}
    if search:
        filters["full_name"] = ("like", f"%{search}%")

    users = frappe.get_all(
        "User",
        filters=filters,
        fields=["name", "full_name", "email", "user_image"],
        order_by="full_name asc",
        limit_page_length=0,
    )

    roles_map = frappe.get_all(
        "Has Role", fields=["parent", "role"], limit_page_length=0
    )
    user_roles = {}
    for r in roles_map:
        user_roles.setdefault(r.parent, []).append(r.role)

    sop_counts = frappe.db.sql(
        """
        SELECT process_owner, COUNT(name) AS count
        FROM `tabSOP`
        WHERE process_owner IS NOT NULL AND process_owner != ''
        GROUP BY process_owner
        """,
        as_dict=True,
    )
    sop_map = {r.process_owner: r.count for r in sop_counts}

    approval_counts = frappe.db.sql(
        """
        SELECT approver, COUNT(name) AS count
        FROM `tabSOP Approval`
        WHERE decision = 'Pending' AND approver IS NOT NULL AND approver != ''
        GROUP BY approver
        """,
        as_dict=True,
    )
    app_map = {r.approver: r.count for r in approval_counts}

    result = []
    for u in users:
        roles = user_roles.get(u.name, [])
        is_author = "SOP Author" in roles or "System Manager" in roles
        is_approver = "SOP Approver" in roles or "System Manager" in roles

        result.append(
            {
                "name": u.name,
                "full_name": u.full_name,
                "email": u.email,
                "user_image": u.user_image,
                "roles": [
                    r for r in roles if r.startswith("SOP") or r == "System Manager"
                ],
                "is_author": is_author,
                "is_approver": is_approver,
                "sop_count": sop_map.get(u.name, 0),
                "pending_approvals": app_map.get(u.name, 0),
            }
        )

    return result
