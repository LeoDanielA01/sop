# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe

from sop.api.settings import settings

TIERS = ("Beginner", "Intermediate", "Expert")


def tier_for(completions):
	current = settings()
	if completions >= current.expert_from:
		return "Expert"
	if completions >= current.intermediate_from:
		return "Intermediate"
	return "Beginner"


def rank(tier):
	return TIERS.index(tier) if tier in TIERS else -1


def completions(users=None, sops=None):
	filters = {"status": "Completed", "outcome": ("!=", "Not Competent")}
	if users is not None:
		filters["trainee"] = ("in", list(users) or [""])
	if sops is not None:
		filters["sop"] = ("in", list(sops) or [""])

	counts = {}
	for row in frappe.get_all(
		"SOP Training Assignment", filters=filters, fields=["trainee", "sop"], limit_page_length=0
	):
		key = (row.trainee, row.sop)
		counts[key] = counts.get(key, 0) + 1

	return counts


def level(user, sop):
	count = completions([user], [sop]).get((user, sop), 0)
	return {"completions": count, "tier": tier_for(count)}


@frappe.whitelist()
def of(sop, user=None):
	frappe.get_doc("SOP", sop).check_permission("read")
	user = user or frappe.session.user
	if user != frappe.session.user and not frappe.has_permission("SOP Training Assignment", "read"):
		frappe.throw(frappe._("You cannot see other people's training."), frappe.PermissionError)

	return level(user, sop)
