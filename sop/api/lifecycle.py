# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import hashlib

import frappe
from frappe import _

from sop.notifications import tell
from frappe.utils import cint, getdate, now_datetime, nowdate

from sop import training

DRAFT_STATES = ("Draft", "Under Revision")


@frappe.whitelist()
def send_for_approval(sop, approvers):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("write")

	if doc.status not in DRAFT_STATES:
		frappe.throw(
			_("{0} is {1}. Only a draft can be sent for approval.").format(doc.sop_no, doc.status)
		)

	rows = frappe.parse_json(approvers) or []
	if not rows:
		frappe.throw(_("Pick who has to approve this."))

	if doc.approvals:
		doc.add_comment("Comment", previous_cycle(doc))

	doc.approvals = []
	for row in rows:
		approver = row.get("approver") if isinstance(row, dict) else row
		if not approver:
			continue

		doc.append(
			"approvals",
			{
				"approver": approver,
				"approval_role": (row.get("approval_role") if isinstance(row, dict) else None)
				or "Approver",
				"decision": "Pending",
			},
		)

	if not doc.approvals:
		frappe.throw(_("Pick who has to approve this."))

	doc.status = "In Review"
	doc.save()
	tell_approvers(doc)

	return {"status": doc.status}


@frappe.whitelist()
def decide(sop, decision, comment=None):
	if decision not in ("Approved", "Rejected"):
		frappe.throw(_("A decision is either Approved or Rejected."))

	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")

	if doc.status != "In Review":
		frappe.throw(_("{0} is not waiting for approval.").format(doc.sop_no))

	mine = [
		row
		for row in doc.approvals
		if row.approver == frappe.session.user and row.decision == "Pending"
	]
	if not mine:
		frappe.throw(_("You are not waiting to approve this one."))

	if decision == "Rejected" and not comment:
		frappe.throw(_("Say what has to change before this can be approved."))

	for row in mine:
		row.decision = decision
		row.comment = comment
		row.signed_at = now_datetime()
		row.signature_hash = signature(doc, row)

	if decision == "Rejected":
		doc.status = "Under Revision" if cint(doc.version) else "Draft"
	elif all(row.decision == "Approved" for row in doc.approvals):
		doc.status = "Approved"

	doc.save(ignore_permissions=True)
	tell_owner(doc, decision, comment)

	return {"status": doc.status}


@frappe.whitelist()
def publish(sop, effective_from=None, change_summary=None, is_material=1):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("write")

	if doc.status != "Approved":
		frappe.throw(_("{0} has to be approved before it comes into force.").format(doc.sop_no))

	previous = latest_revision(doc.name)

	doc.version = cint(doc.version) + 1
	doc.effective_from = getdate(effective_from or nowdate())
	doc.status = "Effective"
	doc.save()

	cut_revision(doc, previous, change_summary, is_material)
	training.assign_for_procedure(doc.name, cause=_("Revision {0}").format(doc.version))

	return {"status": doc.status, "version": doc.version}


@frappe.whitelist()
def start_revision(sop):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("write")

	if doc.status != "Effective":
		frappe.throw(_("Only the version in force can be revised."))

	doc.status = "Under Revision"
	doc.save()

	return {"status": doc.status}


@frappe.whitelist()
def retire(sop, reason=None):
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("write")

	if doc.status == "Retired":
		return {"status": doc.status}

	if doc.status not in ("Approved", "Effective"):
		frappe.throw(_("Only an approved or in-force procedure can be retired."))

	doc.status = "Retired"
	doc.save()

	if reason:
		doc.add_comment("Comment", _("Retired — {0}").format(reason))

	return {"status": doc.status}


def previous_cycle(doc):
	lines = [
		_("{0} — {1} ({2})").format(row.approver, row.decision, row.approval_role)
		for row in doc.approvals
	]
	return _("Previous approval round: {0}").format("; ".join(lines))


def actions_for(doc):
	can_write = doc.has_permission("write")
	waiting = any(
		row.approver == frappe.session.user and row.decision == "Pending" for row in doc.approvals
	)

	return {
		"send_for_approval": can_write and doc.status in DRAFT_STATES,
		"decide": doc.status == "In Review" and waiting,
		"publish": can_write and doc.status == "Approved",
		"start_revision": can_write and doc.status == "Effective",
		"retire": can_write and doc.status in ("Approved", "Effective"),
	}


def approvals_of(doc):
	from sop.api.procedures import user_names

	names = user_names({row.approver for row in doc.approvals})

	return [
		{
			"approver": row.approver,
			"approver_name": names.get(row.approver, {}).get("full_name") or row.approver,
			"approver_image": names.get(row.approver, {}).get("user_image"),
			"approval_role": row.approval_role,
			"decision": row.decision,
			"comment": row.comment,
			"signed_at": row.signed_at,
		}
		for row in doc.approvals
	]


def cut_revision(doc, previous, change_summary=None, is_material=1):
	revision = frappe.get_doc(
		{
			"doctype": "SOP Revision",
			"name": f"{doc.name}-R{doc.version}",
			"sop": doc.name,
			"version": doc.version,
			"effective_from": doc.effective_from,
			"supersedes": previous,
			"cause": _("Approved revision"),
			"content": doc.content,
			"change_summary": change_summary,
			"is_material": cint(is_material),
			"approved_by": approver_of(doc),
			"approved_on": now_datetime(),
		}
	)
	revision.insert(ignore_permissions=True)

	return revision.name


def latest_revision(sop):
	rows = frappe.get_all(
		"SOP Revision", filters={"sop": sop}, pluck="name", order_by="version desc", limit=1
	)
	return rows[0] if rows else None


def approver_of(doc):
	for row in doc.approvals:
		if row.decision == "Approved":
			return row.approver

	return frappe.session.user


def signature(doc, row):
	raw = "|".join(
		[
			doc.name,
			str(cint(doc.version) + 1),
			row.approver,
			str(row.signed_at),
			hashlib.sha256((doc.content or "").encode("utf-8")).hexdigest(),
		]
	)
	return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def tell_approvers(doc):
	for row in doc.approvals:
		if row.decision != "Pending":
			continue

		tell(
			row.approver,
			_("{0} is waiting for your approval").format(doc.sop_no),
			doc,
			kind="approval",
		)


def tell_owner(doc, decision, comment=None):
	subject = _("{0} was {1}").format(doc.sop_no, decision.lower())
	if comment:
		subject = f"{subject} — {comment}"

	tell(doc.process_owner, subject, doc, kind="approval")
