import frappe
from frappe import _
from frappe.utils import getdate, nowdate

from sop.notifications import tell
from sop.sop.doctype.sop_risk_assessment.sop_risk_assessment import next_due

ORDER = {"Very High": 4, "High": 3, "Medium": 2, "Low": 1, "": 0}


@frappe.whitelist()
def for_sop(sop: str) -> list[dict]:
	frappe.get_doc("SOP", sop).check_permission("read")
	names = frappe.get_all(
		"SOP Risk Procedure",
		filters={"parenttype": "SOP Risk Assessment", "sop": sop},
		pluck="parent",
		distinct=True,
	)
	today = getdate(nowdate())
	out = []
	for name in names:
		assessment = frappe.get_doc("SOP Risk Assessment", name)
		if assessment.status == "Retired" or not assessment.has_permission("read"):
			continue
		hazards = sorted(assessment.hazards, key=lambda row: row.risk_score or 0, reverse=True)
		out.append(
			{
				"name": assessment.name,
				"title": assessment.title,
				"status": assessment.status,
				"version": assessment.version_label,
				"highest_level": assessment.highest_level,
				"open_actions": assessment.open_actions,
				"hazards": [
					{
						"row": row.name,
						"id": row.hazard_id,
						"task": row.task,
						"hazard": row.hazard,
						"consequence": row.consequence,
						"controls": row.existing_controls,
						"score": row.risk_score,
						"level": row.risk_level,
						"residual_score": row.residual_score,
						"residual_level": row.residual_level,
						"action": row.additional_actions if row.action_status == "Open" else "",
						"check": row.recurring_check,
						"check_every": row.check_every,
						"check_due": bool(row.next_check and getdate(row.next_check) <= today),
						"next_check": row.next_check,
					}
					for row in hazards
				],
			}
		)
	out.sort(key=lambda row: ORDER.get(row["highest_level"] or "", 0), reverse=True)
	return out


@frappe.whitelist()
def complete_check(assessment: str, row: str, notes: str | None = None, sop: str | None = None) -> dict:
	doc = frappe.get_doc("SOP Risk Assessment", assessment)
	doc.check_permission("read")
	hazard = next((item for item in doc.hazards if item.name == row), None)
	if not hazard or not hazard.check_every:
		frappe.throw(_("This hazard has no recurring check."))

	log = frappe.get_doc(
		{
			"doctype": "SOP Log Entry",
			"log_type": "Service",
			"service_type": "Function test",
			"sop": sop,
			"risk_assessment": doc.name,
			"done_by": frappe.session.user,
			"notes": f"{hazard.hazard_id or ''} {hazard.recurring_check or hazard.hazard}. {notes or ''}".strip(),
		}
	).insert()

	frappe.db.set_value(
		"SOP Risk Hazard",
		hazard.name,
		{"last_checked": nowdate(), "next_check": next_due(hazard.check_every)},
	)
	doc.reload()
	doc.save(ignore_permissions=True)
	return {"log": log.name, "next_check": next_due(hazard.check_every)}


def remind():
	today = getdate(nowdate())
	for name in frappe.get_all("SOP Risk Assessment", filters={"status": ("!=", "Retired")}, pluck="name"):
		doc = frappe.get_doc("SOP Risk Assessment", name)
		doc.save(ignore_permissions=True)
		for row in doc.hazards:
			if row.action_status == "Open" and row.action_due and getdate(row.action_due) <= today:
				tell(
					row.action_owner or doc.assessed_by or doc.owner,
					_("Risk action overdue in {0}: {1}").format(
						doc.name, row.additional_actions or row.hazard
					),
					doc,
				)
			if row.next_check and getdate(row.next_check) <= today:
				tell(
					doc.assessed_by or doc.owner,
					_("Check due in {0}: {1}").format(doc.name, row.recurring_check or row.hazard),
					doc,
				)
