# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint

from sop.api.chat import person, post, reachable

KINDS = {"ring", "accept", "decline", "busy", "cancel", "offer", "answer", "candidate", "end"}
OUTCOMES = {"Completed", "Missed", "Declined", "Busy"}


@frappe.whitelist()
def signal(to, kind, call, data=None):
	if kind not in KINDS:
		frappe.throw(_("Unknown call signal."))

	reachable(to)

	if isinstance(data, str):
		data = frappe.parse_json(data)

	frappe.publish_realtime(
		"sop_call",
		{"kind": kind, "call": call, "data": data, "from": person(frappe.session.user)},
		user=to,
	)

	if kind in ("accept", "decline"):
		frappe.publish_realtime("sop_call", {"kind": "taken", "call": call}, user=frappe.session.user)

	return {"ok": True}


@frappe.whitelist()
def log(to, outcome, duration=0, sop=None):
	if outcome not in OUTCOMES:
		frappe.throw(_("Unknown call outcome."))

	reachable(to)

	return post(frappe.session.user, to, outcome, kind="Call", sop=sop, duration=cint(duration))
