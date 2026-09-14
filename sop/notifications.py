# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe

from sop.api.preferences import record

WANTS = {
	"approval": "email_on_approval",
	"publish": "email_on_publish",
	"training": "email_on_training",
}


def tell(user, subject, doc, kind=None, body=None):
	if not user or user == frappe.session.user:
		return

	frappe.get_doc(
		{
			"doctype": "Notification Log",
			"for_user": user,
			"type": "Alert",
			"document_type": doc.doctype,
			"document_name": doc.name,
			"subject": subject,
		}
	).insert(ignore_permissions=True)

	if kind and wants_email(user, kind):
		send(user, subject, doc, body)


def wants_email(user, kind):
	field = WANTS.get(kind)
	if not field:
		return False

	try:
		return bool(record(user).get(field))
	except Exception:
		return True


def send(user, subject, doc, body=None):
	link = frappe.utils.get_url(f"/sop/{doc.name}")

	frappe.sendmail(
		recipients=[user],
		subject=subject,
		message=body or f"<p>{frappe.utils.escape_html(subject)}</p><p><a href='{link}'>Open it</a></p>",
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		now=False,
	)
